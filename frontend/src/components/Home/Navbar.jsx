import React, { useState, useRef, useEffect } from "react";
import { Plane, Bed, Car, Bus, Menu, Sun } from "lucide-react";
import Farelogo from "../../assets/Farelogo.png";
import WalletProfile from "../Home/WalletProfile";

const Navbar = () => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const menuRef = useRef(null);

  const toggleDropdown = () => setIsDropdownOpen(!isDropdownOpen);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        menuRef.current &&
        !menuRef.current.contains(event.target)
      ) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  const navItems = [
    { icon: Plane, text: "Flights", color: "text-red-500" },
    { icon: Bed, text: "Hotels", color: "text-yellow-500" },
    { icon: Sun, text: "Holidays", color: "text-orange-500" },
    { icon: Bus, text: "Buses", color: "text-green-500" },
  ];

  return (
    <div className="fixed top-0 left-0 w-full z-50 bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-4 sm:px-6 py-3">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          {/* Hamburger Icon (Visible on Mobile) */}
          <div
            className="sm:hidden cursor-pointer"
            ref={menuRef}
            onClick={toggleDropdown}
          >
            <Menu className="w-7 h-7 text-gray-800" />
          </div>

          {/* Logo */}
          <div className="flex items-center">
            <img
              src={Farelogo}
              alt="Fareclubs Logo"
              className="h-10 w-auto object-contain"
            />
          </div>

          {/* Navigation Links (Hidden on Mobile) */}
          <ul className="hidden sm:flex space-x-3 ml-4">
            {navItems.map((item, index) => (
              <li key={index}>
                <a
                  href="#"
                  className="group flex items-center space-x-2 text-black border border-none rounded-full px-4 py-2 hover:bg-red-500 hover:text-white transition text-sm sm:text-base"
                >
                  <item.icon
                    className={`w-5 h-5 ${item.color} group-hover:text-white`}
                  />
                  <span>{item.text}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-4">
          <WalletProfile />
        </div>
      </div>

      {/* Dropdown Menu for Small Screens */}
      {isDropdownOpen && (
        <div
          ref={dropdownRef}
          className="sm:hidden absolute top-full left-0 w-full bg-white shadow-md z-50 border-t border-gray-100"
        >
          <ul className="flex flex-col divide-y divide-gray-200">
            {navItems.map((item, index) => (
              <li key={index}>
                <a
                  href="#"
                  className="flex items-center space-x-3 px-6 py-3 hover:bg-red-500 hover:text-white transition"
                >
                  <item.icon
                    className={`w-5 h-5 ${item.color} group-hover:text-white`}
                  />
                  <span className="text-sm font-medium">{item.text}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Navbar;
