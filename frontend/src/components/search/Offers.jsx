import React from "react";
import { motion } from "framer-motion";

const Offers = () => {
  const offers = [
    {
      id: 1,
      title: "Festive Flight Sale",
      desc: "Get up to 25% off on all domestic flights this festive season! Limited time only.",
      img: "https://www.shutterstock.com/image-vector/3d-hand-holding-couple-flight-600nw-2641682345.jpg",
    },
    {
      id: 2,
      title: "International Escape Deal",
      desc: "Flat ₹5000 off on top international destinations — explore the world for less!",
      img: "https://images.unsplash.com/photo-1526772662000-3f88f10405ff?auto=format&fit=crop&w=1000&q=80",
    },
  ];

  return (
    <div className="w-full flex flex-col items-center gap-8">
      {offers.map((offer, idx) => (
        <motion.div
          key={offer.id}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: idx * 0.1 }}
          className="w-full bg-white rounded-2xl overflow-hidden border border-gray-100 hover:shadow-xl hover:scale-[1.01] transition-all duration-300"
        >
          <img
            src={offer.img}
            alt={offer.title}
            className="w-full h-64 object-cover"
          />
          <div className="p-6 flex flex-col justify-center h-44">
            <h2 className="font-display text-xl text-gray-900 mb-2">
              {offer.title}
            </h2>
            <p className="text-gray-600 text-sm leading-relaxed">{offer.desc}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default Offers;
