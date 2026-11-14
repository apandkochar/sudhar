import React from "react";

interface LanguageChipsProps {
  currentLanguage: string;
  onSelectLanguage: (lang: string) => void;
}

export const LanguageChips: React.FC<LanguageChipsProps> = ({
  currentLanguage,
  onSelectLanguage,
}) => {
  const languages = [
    { code: "mr", label: "मराठी" },
    { code: "hi", label: "हिंदी" },
    { code: "en", label: "EN" },
  ];

  return (
    <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-full border border-slate-200">
      {languages.map((lang) => {
        const isSelected = currentLanguage === lang.code;
        return (
          <button
            key={lang.code}
            onClick={() => onSelectLanguage(lang.code)}
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold transition-all ${
              isSelected
                ? "bg-[#002970] text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            {lang.label}
          </button>
        );
      })}
    </div>
  );
};

