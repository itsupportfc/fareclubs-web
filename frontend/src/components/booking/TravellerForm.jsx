import React from "react";
import { motion } from "framer-motion";

const inputBase =
    "w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-800 bg-white transition-all duration-200 outline-none focus:ring-2 focus:ring-[#0047FF]/30 focus:border-[#0047FF] focus:shadow-sm placeholder:text-gray-400";

const InputLabel = ({ label, required, children }) => (
    <label className="block">
        <span className="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1">
            {label}
            {required && <span className="text-[#FF2E57] ml-0.5">*</span>}
        </span>
        {children}
    </label>
);

const TYPE_BADGE = {
    Adult: "bg-blue-50 text-blue-700 border-blue-200",
    Child: "bg-green-50 text-green-700 border-green-200",
    Infant: "bg-orange-50 text-orange-700 border-orange-200",
};

export default function TravellerForm({ travellers, setTravellers, fareQuoteFlags }) {
    const update = (i, k, v) => {
        const copy = [...travellers];
        copy[i] = { ...copy[i], [k]: v };
        setTravellers(copy);
    };

    return (
        <div className="space-y-5">
            {travellers.map((t, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.08 }}
                    className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5"
                >
                    <div className="flex items-center gap-2 mb-4">
                        <span
                            className={`text-xs font-semibold px-3 py-1 rounded-full border ${
                                TYPE_BADGE[t.type] || TYPE_BADGE.Adult
                            }`}
                        >
                            {t.type} {i + 1}
                        </span>
                        {i === 0 && (
                            <span className="text-[11px] text-gray-400 font-medium">
                                (Lead Passenger)
                            </span>
                        )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <InputLabel label="Title" required>
                            <select
                                className={inputBase}
                                value={t.title}
                                onChange={(e) => update(i, "title", e.target.value)}
                            >
                                <option value="">Select</option>
                                <option>Mr</option>
                                <option>Mrs</option>
                                <option>Ms</option>
                                <option>Master</option>
                            </select>
                        </InputLabel>
                        <InputLabel label="First Name" required>
                            <input
                                className={inputBase}
                                placeholder="As on ID"
                                value={t.firstName}
                                onChange={(e) => update(i, "firstName", e.target.value)}
                            />
                        </InputLabel>
                        <InputLabel label="Last Name" required>
                            <input
                                className={inputBase}
                                placeholder="As on ID"
                                value={t.lastName}
                                onChange={(e) => update(i, "lastName", e.target.value)}
                            />
                        </InputLabel>
                        <InputLabel label="Date of Birth" required>
                            <input
                                className={inputBase}
                                type="date"
                                value={t.dateOfBirth}
                                onChange={(e) => update(i, "dateOfBirth", e.target.value)}
                            />
                        </InputLabel>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <InputLabel label="Gender" required>
                            <select
                                className={inputBase}
                                value={t.gender}
                                onChange={(e) => update(i, "gender", e.target.value)}
                            >
                                <option value="">Select</option>
                                <option>Male</option>
                                <option>Female</option>
                            </select>
                        </InputLabel>
                    </div>

                    {/* PAN (conditional) */}
                    {fareQuoteFlags?.isPanRequired && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                            <InputLabel label="PAN Number" required>
                                <input
                                    className={inputBase}
                                    placeholder="ABCDE1234F"
                                    value={t.pan || ""}
                                    onChange={(e) =>
                                        update(i, "pan", e.target.value.toUpperCase())
                                    }
                                    maxLength={10}
                                />
                            </InputLabel>
                        </div>
                    )}

                    {/* Passport (conditional) */}
                    {fareQuoteFlags?.isPassportRequired && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                            <InputLabel label="Passport Number" required>
                                <input
                                    className={inputBase}
                                    placeholder="Passport No."
                                    value={t.passportNo || ""}
                                    onChange={(e) =>
                                        update(i, "passportNo", e.target.value.toUpperCase())
                                    }
                                />
                            </InputLabel>
                            <InputLabel label="Passport Expiry" required>
                                <input
                                    className={inputBase}
                                    type="date"
                                    value={t.passportExpiry || ""}
                                    onChange={(e) =>
                                        update(i, "passportExpiry", e.target.value)
                                    }
                                />
                            </InputLabel>
                            {fareQuoteFlags?.isPassportFullDetailRequired && (
                                <>
                                    <InputLabel label="Issue Date">
                                        <input
                                            className={inputBase}
                                            type="date"
                                            value={t.passportIssueDate || ""}
                                            onChange={(e) =>
                                                update(i, "passportIssueDate", e.target.value)
                                            }
                                        />
                                    </InputLabel>
                                    <InputLabel label="Issue Country">
                                        <input
                                            className={inputBase}
                                            placeholder="e.g. IN"
                                            value={t.passportIssueCountryCode || ""}
                                            onChange={(e) =>
                                                update(
                                                    i,
                                                    "passportIssueCountryCode",
                                                    e.target.value.toUpperCase(),
                                                )
                                            }
                                            maxLength={2}
                                        />
                                    </InputLabel>
                                </>
                            )}
                        </div>
                    )}

                    {/* GST (conditional, lead pax only) */}
                    {fareQuoteFlags?.isGstAllowed && i === 0 && (
                        <div className="mt-4 bg-gray-50 rounded-lg p-4">
                            <p className="text-xs font-semibold uppercase tracking-wide text-gray-600 mb-3">
                                GST Details (Optional)
                            </p>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                <InputLabel label="GST Number">
                                    <input
                                        className={inputBase}
                                        placeholder="22AAAAA0000A1Z5"
                                        value={t.gstNumber || ""}
                                        onChange={(e) =>
                                            update(i, "gstNumber", e.target.value.toUpperCase())
                                        }
                                        maxLength={15}
                                    />
                                </InputLabel>
                                <InputLabel label="Company Name">
                                    <input
                                        className={inputBase}
                                        placeholder="Company Name"
                                        value={t.gstCompanyName || ""}
                                        onChange={(e) =>
                                            update(i, "gstCompanyName", e.target.value)
                                        }
                                    />
                                </InputLabel>
                                <InputLabel label="Company Email">
                                    <input
                                        className={inputBase}
                                        type="email"
                                        placeholder="gst@company.com"
                                        value={t.gstCompanyEmail || ""}
                                        onChange={(e) =>
                                            update(i, "gstCompanyEmail", e.target.value)
                                        }
                                    />
                                </InputLabel>
                                <InputLabel label="Company Phone">
                                    <input
                                        className={inputBase}
                                        type="tel"
                                        placeholder="Phone"
                                        value={t.gstCompanyPhone || ""}
                                        onChange={(e) =>
                                            update(i, "gstCompanyPhone", e.target.value)
                                        }
                                    />
                                </InputLabel>
                                <InputLabel label="Company Address">
                                    <input
                                        className={inputBase}
                                        placeholder="Address"
                                        value={t.gstCompanyAddress || ""}
                                        onChange={(e) =>
                                            update(i, "gstCompanyAddress", e.target.value)
                                        }
                                    />
                                </InputLabel>
                            </div>
                        </div>
                    )}
                </motion.div>
            ))}
        </div>
    );
}
