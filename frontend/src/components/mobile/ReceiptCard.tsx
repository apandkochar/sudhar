import React from "react";
import { CheckCircle2, ShieldCheck, ArrowRight, FileText } from "lucide-react";

interface ReceiptCardProps {
  receipt: Record<string, any>;
  onContinue: () => void;
}

export const ReceiptCard: React.FC<ReceiptCardProps> = ({ receipt, onContinue }) => {
  return (
    <div className="bg-white rounded-t-3xl border-t-2 border-emerald-500 shadow-2xl p-5 flex flex-col gap-4 animate-in slide-in-from-bottom duration-300">
      {/* Success Badge */}
      <div className="flex flex-col items-center text-center pt-2">
        <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-2 shadow-inner">
          <CheckCircle2 size={32} strokeWidth={2.5} />
        </div>
        <h3 className="text-base font-bold text-slate-900">
          Action Completed Successfully
        </h3>
        <p className="text-[11px] text-slate-500 mt-0.5">
          {receipt.message || "Your request has been processed."}
        </p>
      </div>

      {/* Receipt Details Box */}
      <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 space-y-2 text-xs">
        <div className="flex justify-between items-center pb-2 border-b border-slate-200/80">
          <span className="text-slate-500 font-medium">Reference ID</span>
          <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
            {receipt.reference_id}
          </span>
        </div>

        {receipt.bank_account && (
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500">Registered Account</span>
            <span className="font-semibold text-slate-800">{receipt.bank_account}</span>
          </div>
        )}

        {receipt.refund_amount && (
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500">Refund Amount</span>
            <span className="font-bold text-emerald-600">₹{receipt.refund_amount}</span>
          </div>
        )}

        {receipt.refund_sla && (
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500">Refund Timeline</span>
            <span className="font-medium text-slate-700">{receipt.refund_sla}</span>
          </div>
        )}

        {receipt.link_validity && (
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500">Link Validity</span>
            <span className="font-medium text-slate-700">{receipt.link_validity}</span>
          </div>
        )}

        <div className="flex items-center gap-1.5 pt-1 text-[10px] text-emerald-700 font-medium">
          <ShieldCheck size={12} />
          <span>Audit trail entry committed to ledger.</span>
        </div>
      </div>

      {/* Button */}
      <button
        onClick={onContinue}
        className="w-full py-3.5 px-4 bg-[#002970] hover:bg-[#051A44] active:scale-98 text-white font-bold rounded-2xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-blue-950/20 transition"
      >
        <span>Continue Loan Journey</span>
        <ArrowRight size={14} />
      </button>
    </div>
  );
};

