// =============================
// FareRules.jsx
// Extracted Fare Rules + Fare Quote logic
// =============================

import React, { useEffect, useMemo, useRef } from "react";
import useFlightStore from "../../store/useFlightStore";

/* ------------------------------
   Helper: Find HTML fare rule source
-------------------------------- */
const findHtmlSource = (fareObj) => {
    if (!fareObj) return null;

    const candidates = [
        fareObj.FareRuleDetail,
        fareObj.FareRuleDetailHtml,
        fareObj.FareRulesHtml,
        fareObj.fareRuleDetail,
        fareObj.fareRulesHtml,
        fareObj.noteHtml,
        fareObj.html,
    ];

    for (const c of candidates) {
        if (typeof c === "string" && c.trim().length > 0) return c;
    }

    if (Array.isArray(fareObj.fareRules) && fareObj.fareRules.length > 0) {
        const fr = fareObj.fareRules[0];
        if (typeof fr === "string" && fr.trim()) return fr;
        if (fr?.FareRuleDetail) return fr.FareRuleDetail;
    }

    return null;
};

/* ------------------------------
   HTML parser (extract tables)
-------------------------------- */
const parseHtmlRules = (htmlString) => {
  if (!htmlString) return null;

  let doc;
  try {
    // DOMParser is safe — parsed documents never execute scripts.
    // Available in all browsers since IE10. No innerHTML fallback needed.
    const parser = new DOMParser();
    doc = parser.parseFromString(htmlString, "text/html");
  } catch {
    // If DOMParser fails (shouldn't happen in any modern browser),
    // return null rather than falling back to innerHTML which has XSS risk.
    return null;
  }

/* ------------------------------
   Date Change Table UI
-------------------------------- */
const ChangeTable = ({ rows }) => (
    <div className="bg-white border rounded-lg p-4">
        <h3 className="font-semibold text-lg mb-3">Date Change Fees</h3>
        <div className="overflow-x-auto">
            <table className="min-w-full border border-gray-200 rounded-lg">
                <thead className="bg-gray-100">
                    <tr className="text-left text-sm font-medium">
                        <th className="px-4 py-2 border">No. of Days Left</th>
                        <th className="px-4 py-2 border">Details</th>
                    </tr>
                </thead>
                <tbody className="text-sm text-gray-700">
                    {rows.map((r, i) => (
                        <tr key={i}>
                            <td className="px-4 py-2 border">{r.days}</td>
                            <td className="px-4 py-2 border">{r.detail}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
);

/* ------------------------------
   Cancellation Table UI
-------------------------------- */
const CancelTable = ({ rows }) => (
    <div className="bg-white border rounded-lg p-4">
        <h3 className="font-semibold text-lg mb-3">Cancellation Fees</h3>
        <div className="overflow-x-auto">
            <table className="min-w-full border border-gray-200 rounded-lg">
                <thead className="bg-gray-100">
                    <tr className="text-left text-sm font-medium">
                        <th className="px-4 py-2 border">No. of Days Left</th>
                        <th className="px-4 py-2 border">Details</th>
                    </tr>
                </thead>
                <tbody className="text-sm text-gray-700">
                    {rows.map((r, i) => (
                        <tr key={i}>
                            <td className="px-4 py-2 border">{r.days}</td>
                            <td className="px-4 py-2 border">{r.detail}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
);

/* ------------------------------
   MAIN COMPONENT: <FareRules />
-------------------------------- */
export default function FareRules({ flightToken }) {
    const getFareRulesAPI = useFlightStore((s) => s.getFareRulesAPI);
    const getFareQuoteAPI = useFlightStore((s) => s.getFareQuoteAPI);
    const fareData = useFlightStore((s) => s.fareData);
    const fareError = useFlightStore((s) => s.fareError);
    const fetchedRef = useRef(false);

    const currentFare = flightToken ? fareData[flightToken.ResultIndex] : null;

    useEffect(() => {
        if (!flightToken || fetchedRef.current) return;
        fetchedRef.current = true;

        (async () => {
            await getFareQuoteAPI(flightToken);
            await getFareRulesAPI(flightToken);
        })();
    }, [flightToken]);

    const parsed = useMemo(() => {
        const html = findHtmlSource(currentFare);
        return html ? parseHtmlRules(html) : null;
    }, [currentFare]);

    if (!parsed)
        return <p className="text-gray-500 text-sm">Fare rules unavailable.</p>;

    return (
        <div className="space-y-6">
            {/* Fare Basis */}
            <div className="bg-white border rounded-lg p-4">
                {parsed.fareBasis && (
                    <p className="text-sm mb-1">
                        <b>Fare Basis Code:</b> {parsed.fareBasis}
                    </p>
                )}
                {parsed.isFlexi && (
                    <p className="text-sm mb-2">
                        <b>This is a Flexi Fare.</b>
                    </p>
                )}
                {parsed.bullets.length > 0 && (
                    <ul className="list-disc list-inside text-sm space-y-1">
                        {parsed.bullets.map((b, i) => (
                            <li key={i}>{b}</li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Change + Cancel tables */}
            <ChangeTable rows={parsed.changeRows} />
            <CancelTable rows={parsed.cancelRows} />

            {parsed.notes.length > 0 && (
                <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold mb-2">Notes</h4>
                    <ul className="list-disc list-inside text-sm space-y-1">
                        {parsed.notes.map((n, i) => (
                            <li key={i}>{n}</li>
                        ))}
                    </ul>
                </div>
            )}

            {fareError && <p className="text-red-600">{fareError}</p>}
        </div>
    );
}
