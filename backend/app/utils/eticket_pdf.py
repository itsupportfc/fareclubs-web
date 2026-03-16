"""E-Ticket PDF generation using fpdf2."""

import io
import logging
from datetime import datetime

from fpdf import FPDF

logger = logging.getLogger(__name__)

PAX_TYPE_LABELS = {1: "Adult", 2: "Child", 3: "Infant"}


def _fmt_dt(dt_str: str | datetime | None) -> tuple[str, str]:
    """Return (date_str, time_str) from a datetime string or object."""
    if not dt_str:
        return ("--", "--")
    if isinstance(dt_str, str):
        try:
            dt = datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return (dt_str, "")
    else:
        dt = dt_str
    return (dt.strftime("%d %b %Y"), dt.strftime("%H:%M"))


def generate_eticket_pdf(provider_raw: dict) -> bytes:
    """Generate a PDF e-ticket from the stored provider_raw JSON.

    Handles both TBOTicketResponse and TBOGetBookingDetailsResponse formats.
    """
    # Log entry summary for debugging
    top_keys = list(provider_raw.keys()) if isinstance(provider_raw, dict) else type(provider_raw).__name__
    logger.info(
        "generate_eticket_pdf called: top-level keys=%s",
        top_keys,
    )

    # Navigate to FlightItinerary — handle both response structures
    itinerary = _extract_itinerary(provider_raw)
    if not itinerary:
        logger.error("generate_eticket_pdf: no itinerary found in provider_raw")
        raise ValueError("Cannot generate e-ticket: no itinerary data found")

    passengers = itinerary.get("Passenger", [])
    segments = itinerary.get("Segments", [])
    logger.info(
        "generate_eticket_pdf: itinerary found — passengers=%d, segments=%d",
        len(passengers) if isinstance(passengers, list) else 0,
        len(segments),
    )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Header ──
    pdf.set_fill_color(31, 41, 55)  # dark gray
    pdf.rect(0, 0, 210, 35, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "FareClubs", new_x="LMARGIN")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(10, 20)
    pdf.cell(0, 6, "E-Ticket / Itinerary", new_x="LMARGIN")

    # PNR on right side of header
    pnr = itinerary.get("PNR", "N/A")
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(140, 10)
    pdf.cell(60, 10, f"PNR: {pnr}", align="R")

    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)

    # ── Booking Info ──
    booking_id = itinerary.get("BookingId", "")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 6, f"Booking ID: {booking_id}")
    pdf.cell(95, 6, f"Airline: {itinerary.get('AirlineCode', '')} - {itinerary.get('ValidatingAirlineCode', '')}", align="R")
    pdf.ln(8)

    # ── Flight Details ──
    _section_header(pdf, "Flight Details")
    segments = itinerary.get("Segments", [])
    for leg in segments:
        if isinstance(leg, list):
            for seg in leg:
                _render_segment(pdf, seg)
        elif isinstance(leg, dict):
            _render_segment(pdf, leg)

    pdf.ln(4)

    # ── Passenger Details ──
    _section_header(pdf, "Passenger Details")
    passengers = itinerary.get("Passenger", [])

    # Table header
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(243, 244, 246)
    col_w = [10, 55, 25, 50, 50]
    headers = ["#", "Name", "Type", "Ticket Number", "Baggage"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for idx, pax in enumerate(passengers):
        name = f"{pax.get('Title', '')} {pax.get('FirstName', '')} {pax.get('LastName', '')}".strip()
        pax_type = PAX_TYPE_LABELS.get(pax.get("PaxType", 1), "Adult")
        ticket_num = ""
        ticket = pax.get("Ticket")
        if ticket and isinstance(ticket, dict):
            ticket_num = ticket.get("TicketNumber", "")

        baggage_str = ""
        seg_add_info = pax.get("SegmentAdditionalInfo", [])
        if seg_add_info and isinstance(seg_add_info, list) and len(seg_add_info) > 0:
            baggage_str = seg_add_info[0].get("Baggage", "")

        pdf.cell(col_w[0], 6, str(idx + 1), border=1)
        pdf.cell(col_w[1], 6, name[:30], border=1)
        pdf.cell(col_w[2], 6, pax_type, border=1)
        pdf.cell(col_w[3], 6, ticket_num[:28], border=1)
        pdf.cell(col_w[4], 6, baggage_str[:28], border=1)
        pdf.ln()

    pdf.ln(4)

    # ── Fare Summary ──
    _section_header(pdf, "Fare Summary")
    fare = itinerary.get("Fare", {})
    pdf.set_font("Helvetica", "", 9)
    _fare_row(pdf, "Base Fare", fare.get("BaseFare", 0), fare.get("Currency", "INR"))
    _fare_row(pdf, "Taxes & Fees", fare.get("Tax", 0), fare.get("Currency", "INR"))
    pdf.set_font("Helvetica", "B", 10)
    _fare_row(pdf, "Total", fare.get("PublishedFare", 0), fare.get("Currency", "INR"))
    pdf.ln(4)

    # ── Cancellation / Change Policy ──
    mini_rules = itinerary.get("MiniFareRules")
    if mini_rules:
        _section_header(pdf, "Cancellation / Change Policy")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(243, 244, 246)
        rule_cols = [50, 35, 105]
        for i, h in enumerate(["Route", "Type", "Charges / Details"]):
            pdf.cell(rule_cols[i], 7, h, border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for rule_group in mini_rules:
            rules = rule_group if isinstance(rule_group, list) else [rule_group]
            for rule in rules:
                if not isinstance(rule, dict):
                    continue
                pdf.cell(rule_cols[0], 6, str(rule.get("JourneyPoints", ""))[:28], border=1)
                pdf.cell(rule_cols[1], 6, str(rule.get("Type", ""))[:20], border=1)
                pdf.cell(rule_cols[2], 6, str(rule.get("Details", "N/A"))[:60], border=1)
                pdf.ln()
        pdf.ln(4)

    # ── Footer / Disclaimer ──
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(
        0, 4,
        "This is a computer-generated e-ticket. Please carry a valid photo ID to the airport. "
        "For support, contact support@fareclubs.com. "
        "FareClubs is not liable for schedule changes made by the airline.",
    )

    return pdf.output()


def _extract_itinerary(raw: dict) -> dict | None:
    """Extract FlightItinerary from either TBOTicketResponse or TBOGetBookingDetailsResponse."""
    # TBOTicketResponse: Response.Response.FlightItinerary
    resp = raw.get("Response", {})
    inner = resp.get("Response")
    if isinstance(inner, dict) and "FlightItinerary" in inner:
        return inner["FlightItinerary"]
    # TBOGetBookingDetailsResponse: Response.FlightItinerary
    if "FlightItinerary" in resp:
        return resp["FlightItinerary"]
    return None


def _section_header(pdf: FPDF, title: str):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 8, title)
    pdf.ln(4)
    pdf.set_draw_color(59, 130, 246)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)


def _render_segment(pdf: FPDF, seg: dict):
    origin = seg.get("Origin", {})
    dest = seg.get("Destination", {})
    airline = seg.get("Airline", {})

    dep_airport = origin.get("Airport", {})
    arr_airport = dest.get("Airport", {})

    dep_date, dep_time = _fmt_dt(origin.get("DepTime"))
    arr_date, arr_time = _fmt_dt(dest.get("ArrTime"))

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(
        95, 6,
        f"{airline.get('AirlineCode', '')} {airline.get('FlightNumber', '')}  |  {airline.get('AirlineName', '')}",
    )
    duration = seg.get("Duration")
    if duration:
        h, m = divmod(int(duration), 60)
        pdf.cell(95, 6, f"Duration: {h}h {m}m", align="R")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    # Departure
    pdf.cell(
        95, 5,
        f"{dep_time}  {dep_airport.get('CityName', '')} ({dep_airport.get('AirportCode', '')})"
        f"  T{dep_airport.get('Terminal', '-')}  |  {dep_date}",
    )
    # Arrival
    pdf.cell(
        95, 5,
        f"{arr_time}  {arr_airport.get('CityName', '')} ({arr_airport.get('AirportCode', '')})"
        f"  T{arr_airport.get('Terminal', '-')}  |  {arr_date}",
        align="R",
    )
    pdf.ln()

    # Baggage line
    baggage = seg.get("Baggage", "")
    cabin_bag = seg.get("CabinBaggage", "")
    if baggage or cabin_bag:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Check-in: {baggage or 'N/A'}  |  Cabin: {cabin_bag or 'N/A'}")
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    pdf.ln(2)


def _fare_row(pdf: FPDF, label: str, amount: float, currency: str):
    pdf.cell(120, 6, label)
    pdf.cell(70, 6, f"Rs. {amount:,.2f}" if currency == "INR" else f"{currency} {amount:,.2f}", align="R")
    pdf.ln()
