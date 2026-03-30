import React, { useState } from "react";
import { motion } from "framer-motion";

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

const TYPE_BADGE = {
  Adult: "bg-blue-50 text-blue-700 border-blue-200",
  Child: "bg-green-50 text-green-700 border-green-200",
  Infant: "bg-orange-50 text-orange-700 border-orange-200",
};

const nameRegex = /^[A-Za-z\s]+$/;
const emailRegex = /^[^\s@,]+@[^\s@,]+\.[^\s@,]+$/;
const phoneRegex = /^\d{10}$/;

export default function TravellerForm({
  travellers,
  setTravellers,
  fareQuoteFlags,
  travellersValidation,
  isDomestic = false,
}) {
  const [touched, setTouched] = useState({});

  const update = (i, k, v) => {
    const copy = [...travellers];
    copy[i] = { ...copy[i], [k]: v };
    setTravellers(copy);
  };

  const markTouched = (i, field) => {
    setTouched((prev) => ({
      ...prev,
      [i]: {
        ...(prev[i] || {}),
        [field]: true,
      },
    }));
  };

  const isFieldTouched = (i, field) => !!touched?.[i]?.[field];

  const getMergedErrors = (traveller, i) => {
    const baseErrors = travellersValidation?.errors?.[i] || {};
    const localErrors = { ...baseErrors };

    if (traveller.firstName && !nameRegex.test(traveller.firstName.trim())) {
      localErrors.firstName = "First name should contain only letters";
    }

    if (traveller.lastName && !nameRegex.test(traveller.lastName.trim())) {
      localErrors.lastName = "Last name should contain only letters";
    }

    if (
      fareQuoteFlags?.isGstAllowed &&
      i === 0 &&
      traveller.gstCompanyName &&
      !nameRegex.test(traveller.gstCompanyName.trim())
    ) {
      localErrors.gstCompanyName = "Company name should contain only letters";
    }

    if (
      fareQuoteFlags?.isGstAllowed &&
      i === 0 &&
      traveller.gstCompanyEmail &&
      !emailRegex.test(traveller.gstCompanyEmail.trim())
    ) {
      localErrors.gstCompanyEmail = "Enter a valid email address";
    }

    if (
      fareQuoteFlags?.isGstAllowed &&
      i === 0 &&
      traveller.gstCompanyPhone &&
      !phoneRegex.test(traveller.gstCompanyPhone.trim())
    ) {
      localErrors.gstCompanyPhone = "Phone number must be exactly 10 digits";
    }

    return localErrors;
  };

  return (
    <div className="space-y-5">
      {travellers.map((t, i) => {
        const errors = getMergedErrors(t, i);

        return (
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
              <InputLabel
                label="Title"
                required
                error={errors.title}
                showError={isFieldTouched(i, "title")}
              >
                <select
                  className={getInputClass(
                    !!errors.title,
                    isFieldTouched(i, "title")
                  )}
                  value={t.title}
                  onChange={(e) => update(i, "title", e.target.value)}
                  onBlur={() => markTouched(i, "title")}
                >
                  <option value="">Select</option>
                  <option>Mr</option>
                  <option>Mrs</option>
                  <option>Ms</option>
                  <option>Master</option>
                </select>
              </InputLabel>

              <InputLabel
                label="First Name"
                required
                error={errors.firstName}
                showError={isFieldTouched(i, "firstName")}
              >
                <input
                  className={getInputClass(
                    !!errors.firstName,
                    isFieldTouched(i, "firstName")
                  )}
                  placeholder="As on ID"
                  value={t.firstName}
                  onChange={(e) => update(i, "firstName", e.target.value)}
                  onBlur={() => markTouched(i, "firstName")}
                />
              </InputLabel>

              <InputLabel
                label="Last Name"
                required
                error={errors.lastName}
                showError={isFieldTouched(i, "lastName")}
              >
                <input
                  className={getInputClass(
                    !!errors.lastName,
                    isFieldTouched(i, "lastName")
                  )}
                  placeholder="As on ID"
                  value={t.lastName}
                  onChange={(e) => update(i, "lastName", e.target.value)}
                  onBlur={() => markTouched(i, "lastName")}
                />
              </InputLabel>

              <InputLabel
                label="Date of Birth"
                required
                error={errors.dateOfBirth}
                showError={isFieldTouched(i, "dateOfBirth")}
              >
                <input
                  className={getInputClass(
                    !!errors.dateOfBirth,
                    isFieldTouched(i, "dateOfBirth")
                  )}
                  type="date"
                  max={new Date().toISOString().split("T")[0]}
                  value={t.dateOfBirth}
                  onChange={(e) => update(i, "dateOfBirth", e.target.value)}
                  onBlur={() => markTouched(i, "dateOfBirth")}
                />
              </InputLabel>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <InputLabel
                label="Gender"
                required
                error={errors.gender}
                showError={isFieldTouched(i, "gender")}
              >
                <select
                  className={getInputClass(
                    !!errors.gender,
                    isFieldTouched(i, "gender")
                  )}
                  value={t.gender}
                  onChange={(e) => update(i, "gender", e.target.value)}
                  onBlur={() => markTouched(i, "gender")}
                >
                  <option value="">Select</option>
                  <option>Male</option>
                  <option>Female</option>
                </select>
              </InputLabel>
            </div>

            {fareQuoteFlags?.isPanRequired && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <InputLabel
                  label="PAN Number"
                  required
                  error={errors.pan}
                  showError={isFieldTouched(i, "pan")}
                >
                  <input
                    className={getInputClass(
                      !!errors.pan,
                      isFieldTouched(i, "pan")
                    )}
                    placeholder="ABCDE1234F"
                    value={t.pan || ""}
                    onChange={(e) =>
                      update(i, "pan", e.target.value.toUpperCase())
                    }
                    onBlur={() => markTouched(i, "pan")}
                    maxLength={10}
                  />
                </InputLabel>
              </div>
            )}

            {fareQuoteFlags?.isPassportRequired && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <InputLabel
                  label="Passport Number"
                  required
                  error={errors.passportNo}
                  showError={isFieldTouched(i, "passportNo")}
                >
                  <input
                    className={getInputClass(
                      !!errors.passportNo,
                      isFieldTouched(i, "passportNo")
                    )}
                    placeholder="Passport No."
                    value={t.passportNo || ""}
                    onChange={(e) =>
                      update(i, "passportNo", e.target.value.toUpperCase())
                    }
                    onBlur={() => markTouched(i, "passportNo")}
                  />
                </InputLabel>

                <InputLabel
                  label="Passport Expiry"
                  required
                  error={errors.passportExpiry}
                  showError={isFieldTouched(i, "passportExpiry")}
                >
                  <input
                    className={getInputClass(
                      !!errors.passportExpiry,
                      isFieldTouched(i, "passportExpiry")
                    )}
                    type="date"
                    value={t.passportExpiry || ""}
                    onChange={(e) =>
                      update(i, "passportExpiry", e.target.value)
                    }
                    onBlur={() => markTouched(i, "passportExpiry")}
                  />
                </InputLabel>

                {fareQuoteFlags?.isPassportFullDetailRequired && (
                  <>
                    <InputLabel
                      label="Issue Date"
                      required
                      error={errors.passportIssueDate}
                      showError={isFieldTouched(i, "passportIssueDate")}
                    >
                      <input
                        className={getInputClass(
                          !!errors.passportIssueDate,
                          isFieldTouched(i, "passportIssueDate")
                        )}
                        type="date"
                        value={t.passportIssueDate || ""}
                        onChange={(e) =>
                          update(i, "passportIssueDate", e.target.value)
                        }
                        onBlur={() => markTouched(i, "passportIssueDate")}
                      />
                    </InputLabel>

                    <InputLabel
                      label="Issue Country"
                      required
                      error={errors.passportIssueCountryCode}
                      showError={isFieldTouched(i, "passportIssueCountryCode")}
                    >
                      <input
                        className={getInputClass(
                          !!errors.passportIssueCountryCode,
                          isFieldTouched(i, "passportIssueCountryCode")
                        )}
                        placeholder="e.g. IN"
                        value={t.passportIssueCountryCode || ""}
                        onChange={(e) =>
                          update(
                            i,
                            "passportIssueCountryCode",
                            e.target.value.toUpperCase()
                          )
                        }
                        onBlur={() =>
                          markTouched(i, "passportIssueCountryCode")
                        }
                        maxLength={2}
                      />
                    </InputLabel>
                  </>
                )}
              </div>
            )}

            {fareQuoteFlags?.isGstAllowed && i === 0 && (
              <div className="mt-4 bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-600 mb-3">
                  GST Details (Optional)
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <InputLabel label="GST Number">
                    <input
                      className={getInputClass(false, false)}
                      placeholder="22AAAAA0000A1Z5"
                      value={t.gstNumber || ""}
                      onChange={(e) =>
                        update(i, "gstNumber", e.target.value.toUpperCase())
                      }
                      maxLength={15}
                    />
                  </InputLabel>

                  <InputLabel
                    label="Company Name"
                    error={errors.gstCompanyName}
                    showError={isFieldTouched(i, "gstCompanyName")}
                  >
                    <input
                      className={getInputClass(
                        !!errors.gstCompanyName,
                        isFieldTouched(i, "gstCompanyName")
                      )}
                      placeholder="Company Name"
                      value={t.gstCompanyName || ""}
                      onChange={(e) =>
                        update(i, "gstCompanyName", e.target.value)
                      }
                      onBlur={() => markTouched(i, "gstCompanyName")}
                    />
                  </InputLabel>

                  <InputLabel
                    label="Company Email"
                    error={errors.gstCompanyEmail}
                    showError={isFieldTouched(i, "gstCompanyEmail")}
                  >
                    <input
                      className={getInputClass(
                        !!errors.gstCompanyEmail,
                        isFieldTouched(i, "gstCompanyEmail")
                      )}
                      type="email"
                      placeholder="gst@company.com"
                      value={t.gstCompanyEmail || ""}
                      onChange={(e) =>
                        update(i, "gstCompanyEmail", e.target.value)
                      }
                      onBlur={() => markTouched(i, "gstCompanyEmail")}
                    />
                  </InputLabel>

                  <InputLabel
                    label="Company Phone"
                    error={errors.gstCompanyPhone}
                    showError={isFieldTouched(i, "gstCompanyPhone")}
                  >
                    <input
                      className={getInputClass(
                        !!errors.gstCompanyPhone,
                        isFieldTouched(i, "gstCompanyPhone")
                      )}
                      type="tel"
                      placeholder="Phone"
                      value={t.gstCompanyPhone || ""}
                      onChange={(e) =>
                        update(
                          i,
                          "gstCompanyPhone",
                          e.target.value.replace(/\D/g, "").slice(0, 10)
                        )
                      }
                      onBlur={() => markTouched(i, "gstCompanyPhone")}
                    />
                  </InputLabel>

                  <InputLabel label="Company Address">
                    <input
                      className={getInputClass(false, false)}
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
        );
      })}
    </div>
  );
}