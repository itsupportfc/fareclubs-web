import React from "react";
import lensImage from "../../assets/lens.avif";
import tickImage from "../../assets/tick.avif";
import secureLogoImage from "../../assets/securelogo.png";
import supportImage from "../../assets/24-7.jpg";
import cardsImage from "../../assets/cards.avif";
import airplaneImage from "../../assets/airplane.avif";
import familyTravelImage from "../../assets/familytravel.webp";
import travelPicImage from "../../assets/travelpic.avif";
import scenaryImage from "../../assets/scenary.avif";
import vanImage from "../../assets/van.avif";

const promotionalImages = [cardsImage, airplaneImage, familyTravelImage];
const holidayImages = [travelPicImage, scenaryImage, vanImage];

export default function Cards() {
    const footerCards = [
        {
            image: lensImage,
            title: "More Than 25 Million Monthly Visitors",
            description:
                "Thanks to its easy-to-use and secure payment infrastructure where you can compare hundreds of flights, FareClubs serves millions of users every month.",
        },
        {
            image: tickImage,
            title: "Book Your Ticket in 2 Minutes",
            description:
                "Compare flight options quickly and book a ticket that suits your schedule and budget in just a few minutes.",
        },
        {
            image: secureLogoImage,
            title: "Secure Payment",
            description:
                "Make flight ticket payments easily and securely from your home, office, or mobile phone.",
        },
        {
            image: supportImage,
            title: "24/7 Live Support",
            description:
                "Our customer support team is available to help you with your bookings and travel-related queries.",
        },
    ];

    return (
        <>
            <div className="text-center">
                <h1 className="font-display text-2xl text-black">
                    Cheap Flight Tickets{" "}
                    <span className="text-gray-600">
                        Prices are at FareClubs!
                    </span>
                </h1>
            </div>

            {/* Wrapper to center the gray background div */}
            <div className="flex justify-center mt-5">
                <div className="bg-gray-200 inline-block rounded-lg w-full sm:w-4/5 lg:w-3/4 p-2 mx-auto">
                    <h2 className="font-display text-xl mt-3 text-left ml-2">
                        Promotional Offers
                    </h2>

                    {/* First Set of Cards (1-3) */}
                    <div className="grid grid-cols-1 cursor-pointer gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 mt-2 mx-2">
                        {promotionalImages.map((src, index) => (
                            <div
                                key={index}
                                className="card bg-base-100 image-full w-full max-w-none shadow-xl hover:scale-[1.02] transform transition-all duration-300 ease-in-out rounded-xl overflow-hidden"
                            >
                                <figure>
                                    <img
                                        src={src}
                                        className="w-full h-60 object-cover"
                                        alt="Flight Destination"
                                        loading="lazy"
                                        decoding="async"
                                        width={384}
                                        height={240}
                                    />
                                </figure>
                            </div>
                        ))}
                    </div>

                    <h2 className="font-display text-xl mt-4 text-left ml-2">
                        Holiday Packages
                    </h2>

                    {/* Second Set of Cards (4-6) */}
                    <div className="grid grid-cols-1 cursor-pointer gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 mt-4 mx-2">
                        {holidayImages.map((src, index) => (
                            <div
                                key={index}
                                className="card bg-base-100 image-full w-full max-w-none shadow-xl hover:scale-[1.02] transform transition-all duration-300 ease-in-out rounded-xl overflow-hidden"
                            >
                                <figure>
                                    <img
                                        src={src}
                                        className="w-full h-60 object-cover"
                                        alt="Flight Destination"
                                        loading="lazy"
                                        decoding="async"
                                        width={384}
                                        height={240}
                                    />
                                </figure>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <h1 className="font-display text-2xl mt-5 text-center text-black">
                Cheap Flight Tickets{" "}
                <span className="text-gray-600">Prices are at FareClubs!</span>
            </h1>

            {/* Footer Info Section */}
            <footer className="bg-gray-100 text-white py-12 px-6 mt-5 mr-15 ml-16">
                <div className="max-w-6xl cursor-pointer mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {footerCards.map((card, index) => (
                        <div
                            key={index}
                            className="bg-white rounded-xl overflow-hidden shadow-lg border border-gray-100 flex flex-col transition-all duration-300 hover:scale-[1.02] hover:shadow-xl"
                        >
                            {/* Image Section */}
                            <div className="h-36">
                                <img
                                    src={card.image}
                                    alt={card.title}
                                    className="w-full h-full object-contain"
                                    loading="lazy"
                                    decoding="async"
                                    width={240}
                                    height={144}
                                />
                            </div>

                            {/* Text Section */}
                            <div className="p-4 flex-1">
                                <h3 className="font-display text-lg text-black">
                                    {card.title}
                                </h3>
                                <p className="text-gray-700 text-sm mt-2">
                                    {card.description}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </footer>
        </>
    );
}
