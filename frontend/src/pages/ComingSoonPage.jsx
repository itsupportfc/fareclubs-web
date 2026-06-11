import { Link } from "react-router-dom";
import { Bed, Bus, Plane } from "lucide-react";
import Navbar from "../components/Home/Navbar";

const pageContent = {
    hotels: {
        icon: Bed,
        title: "Hotel Bookings Coming Soon",
        description:
            "We are preparing a reliable stay-booking experience for your trips.",
    },
    buses: {
        icon: Bus,
        title: "Bus Bookings Coming Soon",
        description:
            "We are working on a smoother way to plan your road journeys.",
    },
};

export default function ComingSoonPage({ type }) {
    const content = pageContent[type] || pageContent.hotels;
    const Icon = content.icon;

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="min-h-screen flex items-center justify-center px-4 pt-24">
                <div className="max-w-xl w-full text-center bg-white border border-gray-100 shadow-sm rounded-2xl px-6 py-12">
                    <div className="mx-auto mb-5 h-14 w-14 rounded-full bg-red-50 flex items-center justify-center">
                        <Icon className="h-7 w-7 text-[#FF2E57]" />
                    </div>

                    <h1 className="font-display text-3xl font-bold text-gray-900">
                        {content.title}
                    </h1>

                    <p className="mt-3 text-gray-500">{content.description}</p>

                    <Link
                        to="/"
                        className="mt-8 inline-flex items-center justify-center gap-2 rounded-full bg-[#FF2E57] px-6 py-3 text-sm font-semibold text-white hover:bg-[#e61a42] transition-colors"
                    >
                        <Plane className="h-4 w-4" />
                        Back to Flights
                    </Link>
                </div>
            </main>
        </div>
    );
}
