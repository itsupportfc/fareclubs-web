import React from "react";
import {
  FaFacebookF,
  FaInstagram,
  FaLinkedinIn,
  FaYoutube,
  FaTwitter,
} from "react-icons/fa";

// Importing images correctly
import visa from "../../assets/payments/Visa1.png";
import mastercard from "../../assets/payments/MasterCard.png";
import amex from "../../assets/payments/Amex-logo.webp";
import bhim from "../../assets/payments/Bhim.jpg";
import rupay from "../../assets/payments/Rupay.png";
import pci from "../../assets/payments/pci 1.png";
import secure from "../../assets/payments/Secure.jpg";

const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200 py-10">
      <div
        className="
          max-w-[1400px] mx-auto px-6
          flex flex-col lg:flex-row justify-between items-start text-sm gap-10
        "
      >
        {/* Left Columns */}
        <div className="flex flex-col cursor-pointer sm:flex-row sm:flex-wrap lg:flex-nowrap gap-10 lg:gap-20 w-full lg:w-auto text-center sm:text-left justify-center lg:justify-start">
          {/* COMPANY + PARTNER */}
          <div>
            <h4 className="font-display text-base text-blue-600 mb-3">COMPANY</h4>
            <ul className="space-y-2 text-gray-500">
              <li className="hover:text-gray-700 transition-colors duration-200">About Us</li>
            </ul>

            <div className="mt-8">
              <h4 className="font-display text-base text-blue-600 mb-3">
                PARTNER WITH US
              </h4>
              <ul className="space-y-2 text-gray-500">
                <li className="hover:text-gray-700 transition-colors duration-200">Corporate Login</li>
              </ul>
            </div>
          </div>

          {/* OFFERING */}
          <div>
            <h4 className="font-display text-base text-blue-600 mb-3">OFFERING</h4>
            <ul className="space-y-2 text-gray-500">
              <li className="hover:text-gray-700 transition-colors duration-200">Flights</li>
              <li className="hover:text-gray-700 transition-colors duration-200">Hotels</li>
              <li className="hover:text-gray-700 transition-colors duration-200">Fare Calendar</li>
              <li className="hover:text-gray-700 transition-colors duration-200">Print E-ticket</li>
            </ul>
          </div>

          {/* CUSTOMER CARE */}
          <div>
            <h4 className="font-display text-base text-blue-600 mb-3">CUSTOMER CARE</h4>
            <ul className="space-y-2 text-gray-500">
              <li className="hover:text-gray-700 transition-colors duration-200">Contact Us</li>
              <li className="hover:text-gray-700 transition-colors duration-200">Register with Us</li>
              <li className="hover:text-gray-700 transition-colors duration-200">Terms and Conditions</li>
              <li className="hover:text-gray-700 transition-colors duration-200">Privacy Policy</li>
            </ul>
          </div>
        </div>

        {/* Center — Payment + Social */}
        <div className="flex flex-col cursor-pointer items-center lg:items-start w-full lg:w-auto">
          <h4 className="font-display text-base text-blue-600 mb-3">PAYMENT MODE</h4>
          <div className="flex flex-wrap justify-center lg:justify-start items-center gap-3 sm:gap-4 mb-6">
            {[visa, mastercard, amex, bhim, rupay].map((img, i) => (
              <div
                key={i}
                className="border border-gray-300 rounded-lg p-2 bg-white hover:shadow-sm transition-all duration-200"
              >
                <img
                  src={img}
                  alt="payment"
                  className="h-7 sm:h-8 md:h-9 lg:h-8 w-auto object-contain"
                />
              </div>
            ))}
          </div>

          <h4 className="font-display text-base text-blue-600 mb-3 text-center lg:text-left">
            FOLLOW US ON
          </h4>
          <div className="flex justify-center lg:justify-start items-center gap-5 text-2xl">
            <FaFacebookF className="text-blue-600 hover:scale-110 transition-transform duration-200" />
            <FaYoutube className="text-red-500 hover:scale-110 transition-transform duration-200" />
            <FaInstagram className="text-pink-500 hover:scale-110 transition-transform duration-200" />
            <FaLinkedinIn className="text-blue-700 hover:scale-110 transition-transform duration-200" />
            <FaTwitter className="text-gray-800 hover:scale-110 transition-transform duration-200" />
          </div>
        </div>

        {/* Right — Security Badges */}
        <div className="flex flex-col cursor-pointer items-center justify-center gap-4 w-full lg:w-auto mt-8 lg:mt-0">
          <img
            src={pci}
            alt="PCI DSS Compliant"
            className="h-14 sm:h-16 md:h-18 lg:h-20 object-contain"
          />
          <img
            src={secure}
            alt="100% Secure"
            className="h-12 sm:h-14 md:h-16 lg:h-18 object-contain"
          />
        </div>
      </div>

      {/* Bottom Line */}
      <div className="border-t border-gray-200 mt-10 pt-4 text-center text-xs text-gray-500">
        &copy; {new Date().getFullYear()} FareClubs. All Rights Reserved.
      </div>
    </footer>
  );
};

export default Footer;
