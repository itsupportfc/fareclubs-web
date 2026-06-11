import Navbar from "../components/Home/Navbar";
import Footer from "../components/Home/Footer";
import privacyPolicyText from "../content/legal/privacy-policy.txt?raw";
import bookingRefundsText from "../content/legal/booking-cancellation-refunds.txt?raw";
import termsText from "../content/legal/terms-and-conditions.txt?raw";

const pageMeta = {
    privacy: {
        title: "Privacy Policy",
        subtitle:
            "This policy explains how RNR Traveltech Private Limited collects, uses, protects, and shares information when you use fareclubs.com.",
        updated: "Last updated: June 11, 2026",
    },
    booking: {
        title: "Booking, Cancellation and Refunds",
        subtitle:
            "Important terms for flight bookings, cancellations, reissuance, no-show cases, and refund processing.",
        updated: "Last updated: June 11, 2026",
    },
    terms: {
        title: "Terms and Conditions",
        subtitle:
            "These terms govern your access to and use of Fareclubs services, bookings, payments, and related travel products.",
        updated: "Last updated: June 11, 2026",
    },
};

const privacyHeadings = [
    "Consent Notice",
    "1. Information We Collect",
    "Travel-Specific Data",
    "2. How We Collect This Information",
    "3. How We Use Your Information",
    "4. Disclosure of Your Information",
    "Operational Disclosures",
    "Legal and Compliance Disclosures",
    "5. Automated Data Collection Technologies",
    "Technologies Used",
    "6. Third-Party Use of Tracking Technologies",
    "7. Changes to Our Privacy Policy",
    "8. Contact Information",
];

const bookingHeadings = [
    "Intermediary Status",
    "Flight Alterations",
    "Airfares & Baggage",
    "Code-Share Arrangements",
    "Service Fees",
    "Final Pricing",
    "Infant & Child Fares",
    "Travel Documentation",
    "Airport Check-in",
    "Booking Modifications",
    "Amendment, Cancellation, and Refund Policy",
    "Governing Terms",
    "No-Show & Partial Modifications",
    "Infant Travel Restrictions",
    "Handling Fees",
    "Policy Restrictions",
    "Reissue & Rebooking Charges",
    "Direct Airline Changes",
    "Refund Disbursement Process",
    "Jurisdiction and Governing Law",
];

const termsHeadings = [
    "ELIGIBILITY TO USE",
    "INTELLECTUAL PROPERTY RIGHTS",
    "USAGE OF WEBSITE AND MOBILE APPLICATION",
    "BOOKING BY TRAVEL AGENTS",
    "LIMITATION OF LIABILITY",
    "USER'S RESPONSIBILITY",
    "SECURITY AND ACCOUNT-RELATED INFORMATION",
    "FEES AND PAYMENT",
    "SPECIAL FARE RESTRICTIONS",
    "INSURANCE",
    "COMPLIANCE OF LIBERALIZED REMITTANCE SCHEME (LRS)",
    "VISA OBLIGATIONS",
    "COMPLIANCE WITH TAX COLLECTED AT SOURCE",
    "FORCE MAJEURE",
    "ADVERTISEMENTS ON THE COMPANY'S WEBSITE AND RELATED SITES",
    "RIGHT TO CANCEL",
    "SPAMMING AND PHISHING",
    "RIGHT TO REFUSE",
    "INDEMNIFICATION",
    "CONDITIONS RELATED TO FLIGHT TICKETS",
    "CONDITIONS RELATED TO CHARTER",
    "CONDITIONS RELATED TO HOTELS",
    "CONDITIONS RELATED TO BUS",
    "CONDITIONS RELATED TO TRAIN",
    "CONDITIONS RELATED TO CABS",
    "CONDITIONS RELATED TO UPI",
    "CONDITIONS RELATED TO ACTIVITIES AND OTHER SERVICES",
    "VISA SERVICES",
    "OUTBOUND AND DOMESTIC TOURS",
    "CONDITIONS RELATED TO SELF-DRIVEN CARS",
    "CONDITIONS RELATED TO COVID-19",
    "SEVERABILITY",
    "JURISDICTION",
    "CONFIDENTIAL",
    "AMENDMENTS AND MODIFICATIONS",
    "REDRESSAL OF GRIEVANCES",
];

const cp1252ByteMap = {
    0x20ac: 0x80,
    0x201a: 0x82,
    0x0192: 0x83,
    0x201e: 0x84,
    0x2026: 0x85,
    0x2020: 0x86,
    0x2021: 0x87,
    0x02c6: 0x88,
    0x2030: 0x89,
    0x0160: 0x8a,
    0x2039: 0x8b,
    0x0152: 0x8c,
    0x017d: 0x8e,
    0x2018: 0x91,
    0x2019: 0x92,
    0x201c: 0x93,
    0x201d: 0x94,
    0x2022: 0x95,
    0x2013: 0x96,
    0x2014: 0x97,
    0x02dc: 0x98,
    0x2122: 0x99,
    0x0161: 0x9a,
    0x203a: 0x9b,
    0x0153: 0x9c,
    0x017e: 0x9e,
    0x0178: 0x9f,
};

function fixMojibake(text) {
    if (!text.includes("\u00e2")) {
        return text;
    }

    const bytes = [];
    const encoder = new TextEncoder();

    Array.from(text).forEach((char) => {
        const code = char.codePointAt(0);

        if (cp1252ByteMap[code]) {
            bytes.push(cp1252ByteMap[code]);
            return;
        }

        if (code <= 255) {
            bytes.push(code);
            return;
        }

        bytes.push(...encoder.encode(char));
    });

    return new TextDecoder("utf-8").decode(new Uint8Array(bytes));
}

function normalizeText(text) {
    return fixMojibake(text)
        .replace(/\r/g, "")
        .replace(/[\u2018\u2019]/g, "'")
        .replace(/[\u201c\u201d]/g, '"')
        .replace(/[\u2013\u2014]/g, "-")
        .replace(/[\u2022\u25cf]/g, "-")
        .replace(/\u00a0/g, " ")
        .replace(/\t/g, " ");
}

function getLines(text, titleLine) {
    const lines = normalizeText(text)
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);

    if (!titleLine) {
        return lines;
    }

    const titleIndex = lines.findIndex(
        (line) => line.toLowerCase() === titleLine.toLowerCase(),
    );

    return titleIndex >= 0 ? lines.slice(titleIndex + 1) : lines;
}

function getHeading(line, headings) {
    return headings.find(
        (heading) => line === heading || line.startsWith(`${heading}:`),
    );
}

function getInlineHeading(line, headings) {
    const heading = headings.find(
        (item) => line === item || line.startsWith(`${item} `),
    );

    if (!heading) {
        return null;
    }

    return {
        title: heading,
        body: line.slice(heading.length).trim(),
    };
}

function getCancellationTable() {
    return {
        type: "table",
        headers: [
            "S.NO",
            "TIME SPAN DURING WHICH THE CANCELLATION IS MADE",
            "CHARGES",
        ],
        rows: [
            ["1", "Within a period of 7 days of the scheduled departure", "100%"],
            ["2", "14 to 8 days before departure", "75%"],
            ["3", "30 to 15 days before departure", "50%"],
            ["4", "44 to 31 days before departure", "25%"],
            ["5", "As per airline cancellation policy and DGCA directives", ""],
        ],
    };
}

function parseLegalDocument(text, options) {
    const lines = getLines(text, options.titleLine);
    const sections = [];
    let currentSection = {
        title: options.defaultTitle,
        body: [],
    };

    const pushSection = () => {
        if (
            currentSection.body.length > 0 ||
            (options.keepEmptySections &&
                currentSection.title !== options.defaultTitle)
        ) {
            sections.push(currentSection);
        }
    };

    lines.forEach((line) => {
        if (line.startsWith("S.NO | TIME SPAN")) {
            currentSection.body.push(getCancellationTable());
            return;
        }

        if (line.startsWith("-")) {
            currentSection.body.push({
                type: "bullet",
                text: line.replace(/^-\s*/, ""),
            });
            return;
        }

        const heading = getHeading(line, options.headings);
        const inlineHeading = heading
            ? {
                  title: heading,
                  body:
                      line === heading
                          ? ""
                          : line
                                .slice(heading.length)
                                .replace(/^:\s*/, "")
                                .trim(),
              }
            : getInlineHeading(line, options.inlineHeadings || []);

        if (inlineHeading) {
            pushSection();
            currentSection = {
                title: inlineHeading.title,
                body: inlineHeading.body
                    ? [{ type: "paragraph", text: inlineHeading.body }]
                    : [],
            };
            return;
        }

        currentSection.body.push({ type: "paragraph", text: line });
    });

    pushSection();

    return sections;
}

const legalContent = {
    privacy: {
        ...pageMeta.privacy,
        sections: parseLegalDocument(privacyPolicyText, {
            titleLine: "Privacy Policy",
            defaultTitle: "Overview",
            headings: privacyHeadings,
        }),
    },
    booking: {
        ...pageMeta.booking,
        sections: parseLegalDocument(bookingRefundsText, {
            titleLine: "Terms for Flight Booking, Cancellation, Reissuance, and Refunds",
            defaultTitle: "Overview",
            headings: bookingHeadings,
            keepEmptySections: true,
        }),
    },
    terms: {
        ...pageMeta.terms,
        sections: parseLegalDocument(termsText, {
            defaultTitle: "Overview",
            headings: [],
            inlineHeadings: termsHeadings,
        }),
    },
};

function renderContent(items) {
    const renderedItems = [];

    for (let index = 0; index < items.length; index += 1) {
        const item = items[index];

        if (item.type === "bullet") {
            const bullets = [];
            let bulletIndex = index;

            while (items[bulletIndex]?.type === "bullet") {
                bullets.push(items[bulletIndex].text);
                bulletIndex += 1;
            }

            renderedItems.push(
                <ul
                    key={`bullets-${index}`}
                    className="list-disc pl-5 space-y-2"
                >
                    {bullets.map((bullet, bulletIndex) => (
                        <li key={`${bullet}-${bulletIndex}`}>{bullet}</li>
                    ))}
                </ul>,
            );

            index = bulletIndex - 1;
            continue;
        }

        if (item.type === "table") {
            renderedItems.push(
                <div
                    key={`table-${index}`}
                    className="overflow-x-auto rounded-lg border border-gray-200"
                >
                    <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
                        <thead className="bg-gray-50 text-gray-700">
                            <tr>
                                {item.headers.map((header) => (
                                    <th
                                        key={header}
                                        scope="col"
                                        className="px-4 py-3 font-semibold"
                                    >
                                        {header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 bg-white">
                            {item.rows.map((row) => (
                                <tr key={row.join("-")}>
                                    {row.map((cell, cellIndex) => (
                                        <td
                                            key={`${row[0]}-${cellIndex}`}
                                            className="px-4 py-3 text-gray-600"
                                        >
                                            {cell}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>,
            );
            continue;
        }

        renderedItems.push(<p key={`${item.text}-${index}`}>{item.text}</p>);
    }

    return renderedItems;
}

export default function LegalPage({ type }) {
    const page = legalContent[type] || legalContent.privacy;

    return (
        <div className="min-h-screen bg-gray-50 text-gray-800">
            <Navbar />

            <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-16">
                <div className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
                    <div className="bg-gradient-to-r from-[#FF2E57] to-[#0047FF] px-6 py-8 text-white">
                        <h1 className="font-display text-3xl font-bold">
                            {page.title}
                        </h1>
                        <p className="mt-2 text-sm text-white/90 max-w-3xl">
                            {page.subtitle}
                        </p>
                        <p className="mt-4 text-xs text-white/75">
                            {page.updated}
                        </p>
                    </div>

                    <div className="px-6 py-8 space-y-8">
                        {page.sections.map((section) => (
                            <section key={section.title}>
                                <h2 className="font-display text-xl text-blue-600 mb-3">
                                    {section.title}
                                </h2>

                                {section.body.length > 0 && (
                                    <div className="space-y-3 text-sm leading-6 text-gray-600">
                                        {renderContent(section.body)}
                                    </div>
                                )}
                            </section>
                        ))}
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
}
