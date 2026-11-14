import React from "react";
import { Sparkles, CheckCircle2, XCircle, ArrowRight, ShieldCheck } from "lucide-react";
import { LanguageChips } from "./LanguageChips";

interface SudhaarCardProps {
  language: string;
  onLanguageChange: (lang: string) => void;
  explanation: string;
  actionLabel?: string;
  visualData?: Record<string, any>;
  onProposeAction: () => void;
  sourceMode?: string;
}

export const SudhaarCard: React.FC<SudhaarCardProps> = ({
  language,
  onLanguageChange,
  explanation,
  actionLabel = "Fix this issue",
  visualData,
  onProposeAction,
  sourceMode = "template",
}) => {
  const isAccountComparison = visualData && visualData.failed_account && visualData.suggested_account;
  const isTimelineMismatch = visualData && visualData.closure_event && visualData.erroneous_debit;
  const isChecklist = visualData && visualData.checklist;

  return (
    <div className="bg-white rounded-t-3xl border-t-2 border-[#00BAF2] shadow-2xl p-5 flex flex-col gap-4 animate-in slide-in-from-bottom duration-300">
      {/* Header bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-[#002970] to-[#00BAF2] flex items-center justify-center text-white shadow-xs">
            <Sparkles size={12} />
          </div>
          <div>
            <span className="text-xs font-bold text-[#002970] tracking-tight">
              Sudhaar AI Assistant
            </span>
            <span className="ml-1.5 text-[9px] px-1.5 py-0.2 rounded font-mono uppercase bg-blue-50 text-[#00BAF2] border border-[#00BAF2]/30">
              {sourceMode}
            </span>
          </div>
        </div>

        <LanguageChips
          currentLanguage={language}
          onSelectLanguage={onLanguageChange}
        />
      </div>

      {/* Explanation text */}
      <div className="bg-blue-50/60 rounded-xl p-3 border border-blue-100/80">
        <p className="text-xs text-slate-800 leading-relaxed font-medium">
          {explanation}
        </p>
      </div>

      {/* Visual Component */}
      {isAccountComparison && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          {/* Failed Account */}
          <div className="p-2.5 rounded-xl border border-red-200 bg-red-50/40 flex flex-col justify-between">
            <div className="flex items-center justify-between text-red-600 mb-1">
              <span className="font-semibold text-[11px] truncate">
                {visualData.failed_account.bank}
              </span>
              <XCircle size={14} />
            </div>
            <p className="text-[11px] text-slate-500 font-mono">
              Ending {visualData.failed_account.last4}
            </p>
            <span className="text-[10px] text-red-600 font-medium mt-1">
              {visualData.failed_account.status}
            </span>
          </div>

          {/* Suggested Eligible Account */}
          <div className="p-2.5 rounded-xl border-2 border-[#00BAF2] bg-blue-50/40 flex flex-col justify-between relative shadow-xs">
            <div className="absolute -top-2 right-2 bg-[#00BAF2] text-white text-[8px] font-bold px-1.5 py-0.2 rounded-full uppercase tracking-wider">
              Recommended
            </div>
            <div className="flex items-center justify-between text-[#002970] mb-1">
              <span className="font-semibold text-[11px] truncate">
                {visualData.suggested_account.bank}
              </span>
              <CheckCircle2 size={14} className="text-[#00BAF2]" />
            </div>
            <p className="text-[11px] text-slate-600 font-mono">
              Ending {visualData.suggested_account.last4}
            </p>
            <span className="text-[10px] text-[#002970] font-medium mt-1">
              {visualData.suggested_account.status}
            </span>
          </div>
        </div>
      )}

      {/* Timeline Mismatch Visual (Asha) */}
      {isTimelineMismatch && (
        <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl border border-slate-200 text-xs">
          <div className="text-left">
            <span className="text-[10px] text-slate-500 block">Loan Closed</span>
            <span className="font-bold text-emerald-700">{visualData.closure_event.date}</span>
          </div>
          <ArrowRight size={14} className="text-slate-400" />
          <div className="text-right">
            <span className="text-[10px] text-red-500 block">Excess Debit</span>
            <span className="font-bold text-red-600">{visualData.erroneous_debit.amount} ({visualData.erroneous_debit.date})</span>
          </div>
        </div>
      )}

      {/* Checklist Visual (Sunita) */}
      {isChecklist && (
        <div className="space-y-1.5 bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-xs">
          {visualData.checklist.map((item: any, i: number) => (
            <div key={i} className="flex items-center gap-2 text-[11px] text-slate-700">
              <CheckCircle2 size={13} className="text-[#00BAF2]" />
              <span>{item.label}</span>
            </div>
          ))}
          <p className="text-[10px] text-slate-500 pt-1 font-mono">Valid until: {visualData.valid_until}</p>
        </div>
      )}

      {/* Trust pill */}
      <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-500">
        <ShieldCheck size={12} className="text-[#002970]" />
        <span>Actions run ONLY after you tap Confirm. Never moves money.</span>
      </div>

      {/* Action CTA Button */}
      <button
        onClick={onProposeAction}
        className="w-full py-3.5 px-4 bg-[#002970] hover:bg-[#051A44] active:scale-[0.99] text-white font-bold rounded-2xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-blue-950/20 transition"
      >
        <span>{actionLabel}</span>
        <ArrowRight size={15} />
      </button>
    </div>
  );
};
