import React, { useState, useRef, useEffect } from "react";
import { Home, Printer, Phone, Lock, LogOut, ChevronDown } from "lucide-react";
import { toast } from "sonner";

const WalletProfile = () => {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);
  const userName = "Himanshu";
  const firstLetter = userName.charAt(0).toUpperCase();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    toast.success("Logged out successfully!");
    setOpen(false);
    // Add your logout logic here
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Profile Button */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center space-x-2 bg-white border border-none cursor-pointer rounded-full px-2 sm:px-3 py-1 hover:shadow-sm transition"
      >
        {/* Profile Circle */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#eb0066] to-[#007aff] text-white flex items-center justify-center font-semibold text-sm">
          {firstLetter}
        </div>

        {/* Name hidden on small screens */}
        <span className="hidden sm:inline text-sm font-medium text-gray-700">
          {userName}
        </span>

        <ChevronDown
          className={`w-4 h-4 text-gray-500 transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className={`absolute sm:right-0 mt-2 w-48 sm:w-52 bg-white border border-gray-200 rounded-lg shadow-lg z-50 
          animate-slide-down transition-all duration-200 ease-out
          left-1/2 sm:left-auto sm:transform-none -translate-x-1/2 sm:translate-x-0`}
        >
          <ul className="py-2 text-gray-700 text-sm">
            <li className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100 cursor-pointer">
              <Home className="w-4 h-4 text-gray-600" />
              Home
            </li>
            <li className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100 cursor-pointer">
              <Printer className="w-4 h-4 text-gray-600" />
              Print E-Ticket
            </li>
            <li className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100 cursor-pointer">
              <Phone className="w-4 h-4 text-gray-600" />
              Contact Us
            </li>

            <hr className="my-1 border-gray-200" />

            <li className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100 cursor-pointer">
              <Lock className="w-4 h-4 text-gray-600" />
              Sign-In
            </li>
            <li className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100 cursor-pointer">
              <Lock className="w-4 h-4 text-gray-600" />
              Partner Login
            </li>

            <hr className="my-1 border-gray-200" />

            {/* Logout Button */}
            <li
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-2 hover:bg-red-100 text-red-600 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </li>
          </ul>
        </div>
      )}

      {/* Animation Keyframes */}
      <style>{`
        @keyframes slideDown {
          0% {
            opacity: 0;
            transform: translateY(-5px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-slide-down {
          animation: slideDown 0.15s ease-out;
        }
      `}</style>
    </div>
  );
};

export default WalletProfile;
