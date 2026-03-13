import React from "react";

const inputBase =
    "w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-800 bg-white transition-all outline-none focus:ring-2 focus:ring-[#0047FF]/30 focus:border-[#0047FF] placeholder:text-gray-400";

const InputLabel = ({ label, required, children }) => (
    <label className="block">
        <span className="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1">
            {label}
            {required && <span className="text-[#FF2E57] ml-0.5">*</span>}
        </span>
        {children}
    </label>
);

export default function ContactDetailsSection({ travellers, setTravellers }) {
    const lead = travellers[0];
    if (!lead) return null;

    const update = (k, v) => {
        const copy = [...travellers];
        copy[0] = { ...copy[0], [k]: v };
        setTravellers(copy);
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <InputLabel label="Email Address" required>
                    <input
                        className={inputBase}
                        type="email"
                        placeholder="email@example.com"
                        value={lead.email}
                        onChange={(e) => update("email", e.target.value)}
                    />
                </InputLabel>
                <InputLabel label="Phone Number" required>
                    <input
                        className={inputBase}
                        type="tel"
                        placeholder="+91 XXXXX XXXXX"
                        value={lead.contactNo}
                        onChange={(e) => update("contactNo", e.target.value)}
                    />
                </InputLabel>
                <InputLabel label="Address">
                    <input
                        className={inputBase}
                        placeholder="Street address"
                        value={lead.addressLine1}
                        onChange={(e) => update("addressLine1", e.target.value)}
                    />
                </InputLabel>
                <InputLabel label="City">
                    <input
                        className={inputBase}
                        placeholder="City"
                        value={lead.city}
                        onChange={(e) => update("city", e.target.value)}
                    />
                </InputLabel>
            </div>
        </div>
    );
}
