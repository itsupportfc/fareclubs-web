import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const GA_MEASUREMENT_ID = "G-QW1RTE1RY4";

export default function GoogleAnalytics() {
    const location = useLocation();

    useEffect(() => {
        if (typeof window.gtag !== "function") return;

        window.gtag("event", "page_view", {
            send_to: GA_MEASUREMENT_ID,
            page_title: document.title,
            page_location: window.location.href,
            page_path: `${location.pathname}${location.search}${location.hash}`,
        });
    }, [location.pathname, location.search, location.hash]);

    return null;
}
