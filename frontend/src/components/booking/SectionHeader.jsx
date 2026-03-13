import React from "react";

export default function SectionHeader({ number, icon: Icon, title, subtitle }) {
    return (
        <div className="flex items-center gap-3 mb-5">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-[#FF2E57] to-[#FF6B35] text-white text-sm font-bold shrink-0">
                {number}
            </span>
            {Icon && <Icon className="w-5 h-5 text-[#0047FF] shrink-0" />}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 leading-tight">
                    {title}
                </h3>
                {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
            </div>
        </div>
    );
}
