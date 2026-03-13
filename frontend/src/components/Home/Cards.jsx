import React from "react";

export default function Cards() {
  const footerCards = [
    {
      image: "https://png.pngtree.com/background/20230525/original/pngtree-human-resources-hiring-manager-with-human-search-in-background-with-people-picture-image_2728908.jpg",
      title: "More Than 25 Million Monthly Visitors",
      description:
        "Thanks to its easy-to-use and secure payment infrastructure where you can compare hundreds of flights, obilet.com serves millions of users every month.",
    },
    {
      image: "https://img.freepik.com/premium-psd/red-circle-with-clock-it-that-says-verizon_680596-2979.jpg",
      title: "Book Your Ticket in 2 Minutes",
      description:
        "Creating the opportunity to compare numerous companies with its easy-to-use and secure payment infrastructure, obilet enables everyone to find a flight ticket suitable for their budget in 2 minutes.",
    },
    {
      image: "https://cdn-icons-png.flaticon.com/512/7210/7210904.png",
      title: "Secure Payment",
      description:
        "You can make all your flight ticket purchases easily, quickly, and reliably from your home, office, or with your mobile phone.",
    },
    {
      image: "https://static.vecteezy.com/system/resources/previews/003/344/968/non_2x/hotline-icon-with-headphones-and-24-7-sign-client-support-service-vector.jpg",
      title: "24/7 Live Support",
      description:
        "Our customer service team is ready to support you 24/7 for all transactions you make through obilet Mobile Applications. You can start Live Support with one click and get help.",
    },
  ];

  return (
    <>
      <div className="text-center">
        <h1 className="text-black-400 text-2xl">
          Cheap Flight Tickets{" "}
          <span className="text-gray-600 text-2xl">
            Prices are at FareClubs!
          </span>
        </h1>
      </div>

      {/* Wrapper to center the gray background div */}
      <div className="flex justify-center mt-5">
        <div className="bg-gray-200 inline-block rounded-lg w-full sm:w-4/5 lg:w-3/4 p-2 mx-auto">
          <h2 className="mt-3 text-2xl text-left non-italic ml-2">
            Promotional Offers
          </h2>

          {/* First Set of Cards (1-3) */}
          <div className="grid grid-cols-1 cursor-pointer gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 mt-2 mx-2">
            {[
              "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTGv5BV3XCf-uIqPL_BpNVBCvsZT2PPFCogtA&s",
              "https://gos3.ibcdn.com/top-1569824183.jpg",
              "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRG-EQb9e2AKAJKgDDvMJnpmTqplTzyMRJx8w&s",
            ].map((src, index) => (
              <div
                key={index}
                className="card bg-base-100 image-full w-full max-w-none shadow-xl hover:scale-105 transform transition duration-300 ease-in-out"
              >
                <figure>
                  <img
                    src={src}
                    className="w-full h-60 object-cover rounded-lg"
                    alt="Flight Destination"
                  />
                </figure>
              </div>
            ))}
          </div>

          <h2 className="mt-4 text-2xl text-left non-italic ml-2">
            Holiday Packages
          </h2>

          {/* Second Set of Cards (4-6) */}
          <div className="grid grid-cols-1 cursor-pointer gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 mt-4 mx-2">
            {[
              "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzlVR9yR4vBii20Kd9juIEA5DPEwHyB8_Mwg&s",
              "https://images.pexels.com/photos/2662116/pexels-photo-2662116.jpeg?cs=srgb&dl=pexels-jaime-reimer-1376930-2662116-2662116.jpg&fm=jpg",
              "https://plus.unsplash.com/premium_photo-1673971706769-13a9499e3794?fm=jpg&q=60&w=3000&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NXx8ZGVzdGluYXRpb258ZW58MHx8MHx8fDA%3D",
            ].map((src, index) => (
              <div
                key={index}
                className="card bg-base-100 image-full w-full max-w-none shadow-xl hover:scale-105 transform transition duration-300 ease-in-out"
              >
                <figure>
                  <img
                    src={src}
                    className="w-full h-60 object-cover rounded-lg"
                    alt="Flight Destination"
                  />
                </figure>
              </div>
            ))}
          </div>
        </div>
      </div>

      <h1 className="text-black-400 text-2xl mt-5 text-center">
        Cheap Flight Tickets{" "}
        <span className="text-gray-600 text-2xl">
          Prices are at FareClubs!
        </span>
      </h1>

      {/* ⬇️ Added Footer Info Section (nothing deleted) */}
      <footer className="bg-gray-100 text-white py-12 px-6 mt-5 mr-15 ml-16">
        <div className="max-w-6xl cursor-pointer mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {footerCards.map((card, index) => (
            <div
              key={index}
              className="bg-white rounded-lg overflow-hidden shadow-lg flex flex-col transition-all hover:scale-105 hover:shadow-2xl hover:bg-gray-100"
            >
              {/* Image Section */}
              <div className="h-36">
                <img
                  src={card.image}
                  alt={card.title}
                  className="w-full h-full object-contain"
                />
              </div>

              {/* Text Section */}
              <div className="p-4 flex-1">
                <h3 className="text-black text-xl font-semibold">
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
