import React from "react";
import { CreditCard, Smartphone, Send, QrCode, ArrowUpRight, Shield, Sparkles } from "lucide-react";

interface HomeViewProps {
  onStartLoanJourney: () => void;
  personaName: string;
  loanAmount: number;
}

export const HomeView: React.FC<HomeViewProps> = ({
  onStartLoanJourney,
  personaName,
  loanAmount,
}) => {
  return (
    <div className="flex-1 flex flex-col p-4 space-y-4">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-[#002970] to-[#00BAF2] rounded-2xl p-4 text-white shadow-md">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-white/80">
              Welcome back
            </span>
            <h2 className="text-base font-bold mt-0.5">{personaName}</h2>
          </div>
          <span className="bg-white/20 text-[10px] px-2 py-0.5 rounded-full font-medium">
            Pune Verified
          </span>
        </div>
      </div>

      {/* Hero Personal Loan Rescue Card */}
      <div className="bg-white rounded-2xl p-4 border-2 border-[#00BAF2] shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 bg-[#00BAF2] text-white text-[9px] font-bold px-2 py-0.5 rounded-bl-lg">
          ACTIVE JOURNEY
        </div>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#002970] flex items-center justify-center font-bold">
            <CreditCard size={20} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">Personal Loan</h3>
            <p className="text-[11px] text-slate-500 font-medium">
              Approved Limit: ₹{loanAmount.toLocaleString("en-IN")}
            </p>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span>Action Required: Mandate</span>
          </div>

          <button
            onClick={onStartLoanJourney}
            className="px-3 py-1.5 bg-[#002970] hover:bg-[#051A44] text-white rounded-xl text-xs font-bold flex items-center gap-1 transition shadow-xs"
          >
            <span>Resume</span>
            <ArrowUpRight size={13} />
          </button>
        </div>
      </div>

      {/* Services Grid (Paytm-inspired 4x2) */}
      <div className="bg-white rounded-2xl p-3 border border-slate-200">
        <p className="text-[11px] font-bold text-slate-700 mb-2 px-1">Quick Services</p>
        <div className="grid grid-cols-4 gap-3 text-center">
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-[#002970] flex items-center justify-center mb-1">
              <QrCode size={18} />
            </div>
            <span className="text-[10px] text-slate-600 font-medium">Scan & Pay</span>
          </div>

          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-[#002970] flex items-center justify-center mb-1">
              <Send size={18} />
            </div>
            <span className="text-[10px] text-slate-600 font-medium">To Mobile</span>
          </div>

          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-[#002970] flex items-center justify-center mb-1">
              <Smartphone size={18} />
            </div>
            <span className="text-[10px] text-slate-600 font-medium">Recharge</span>
          </div>

          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-[#002970] flex items-center justify-center mb-1">
              <Shield size={18} />
            </div>
            <span className="text-[10px] text-slate-600 font-medium">Insurance</span>
          </div>
        </div>
      </div>
    </div>
  );
};
