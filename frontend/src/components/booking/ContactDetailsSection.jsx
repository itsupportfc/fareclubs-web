import React, { useState } from "react";

const inputBase =
  "w-full border rounded-lg px-3 py-2.5 text-sm text-gray-800 bg-white transition-all duration-200 outline-none placeholder:text-gray-400";

const getInputClass = (hasError, isTouched) =>
  `${inputBase} ${
    hasError && isTouched
      ? "border-red-500 focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
      : "border-gray-200 focus:ring-2 focus:ring-[#0047FF]/30 focus:border-[#0047FF] focus:shadow-sm"
  }`;

const InputLabel = ({ label, required, error, showError, children }) => (
  <label className="block">
    <span className="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1">
      {label}
      {required && <span className="text-[#FF2E57] ml-0.5">*</span>}
    </span>
    {children}
    {showError && error && <p className="mt-1 text-xs text-red-500">{error}</p>}
  </label>
);

const emailRegex = /^[^\s@,]+@[^\s@,]+\.[^\s@,]+$/;
const phoneRegex = /^\d{10}$/;

export default function ContactDetailsSection({
  travellers,
  setTravellers,
}) {
  const [touched, setTouched] = useState({});

  const lead = travellers[0];
  if (!lead) return null;

  const update = (k, v) => {
    const copy = [...travellers];
    copy[0] = { ...copy[0], [k]: v };
    setTravellers(copy);
  };

  const markTouched = (field) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  // 🔥 Validation logic
  const errors = {};

  if (lead.email && !emailRegex.test(lead.email.trim())) {
    errors.email = "Enter a valid email address";
  }

  if (lead.contactNo && !phoneRegex.test(lead.contactNo.trim())) {
    errors.contactNo = "Phone number must be exactly 10 digits";
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* EMAIL */}
        <InputLabel
          label="Email Address"
          required
          error={errors.email}
          showError={touched.email}
        >
          <input
            className={getInputClass(!!errors.email, touched.email)}
            type="email"
            placeholder="email@example.com"
            value={lead.email || ""}
            onChange={(e) => update("email", e.target.value)}
            onBlur={() => markTouched("email")}
          />
        </InputLabel>

        {/* PHONE */}
        <InputLabel
          label="Phone Number"
          required
          error={errors.contactNo}
          showError={touched.contactNo}
        >
          <input
            className={getInputClass(!!errors.contactNo, touched.contactNo)}
            type="tel"
            placeholder="9876543210"
            value={lead.contactNo || ""}
            onChange={(e) =>
              update(
                "contactNo",
                e.target.value.replace(/\D/g, "").slice(0, 10)
              )
            }
            onBlur={() => markTouched("contactNo")}
          />
        </InputLabel>

        {/* ADDRESS */}
        <InputLabel label="Address">
          <input
            className={getInputClass(false, false)}
            placeholder="Street address"
            value={lead.addressLine1 || ""}
            onChange={(e) => update("addressLine1", e.target.value)}
          />
        </InputLabel>

        {/* CITY */}
        <InputLabel label="City">
          <input
            className={getInputClass(false, false)}
            placeholder="City"
            value={lead.city || ""}
            onChange={(e) => update("city", e.target.value)}
          />
        </InputLabel>

      </div>
    </div>
  );
}