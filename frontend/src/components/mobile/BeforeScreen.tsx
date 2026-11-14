import React from "react";
import { XCircle, RefreshCw, AlertTriangle } from "lucide-react";

interface BeforeScreenProps {
  onSwitchToSudhaar: () => void;
}

export const BeforeScreen: React.FC<BeforeScreenProps> = ({ onSwitchToSudhaar }) => {
  return (
    <div className="flex-1 flex flex-col justify-between p-6 bg-slate-50 text-slate-800">
      {/* Broken UX Notice */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2.5 shadow-sm">
        <AlertTriangle className="text-red-600 flex-shrink-0 mt-0.5" size={16} />
        <div>
          <p className="text-xs font-bold text-red-900">Today's Generic Failure Screen</p>
          <p className="text-[11px] text-red-700 leading-snug mt-0.5">
            Borrower gets a dead-end message with no reason code or account details. Most users abandon the loan right here.
          </p>
        </div>
      </div>

      {/* Main Error Body */}
      <div className="flex-1 flex flex-col items-center justify-center text-center my-8">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-red-600 mb-4 shadow-inner">
          <XCircle size={38} strokeWidth={2.2} />
        </div>

        <h2 className="text-lg font-bold text-slate-900">
          Mandate Registration Failed
        </h2>

        <p className="text-xs text-slate-500 max-w-[260px] mt-2 leading-relaxed">
          Mandate registration failed. Please try again. If the problem continues, please contact your bank branch.
        </p>

        <div className="mt-4 px-3 py-1.5 bg-slate-200/80 rounded text-[11px] text-slate-600 font-mono">
          Error Reference: ERR-MND-9901
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <button
          onClick={() => alert("Retrying with the same failed HDFC account will fail again with AP15.")}
          className="w-full py-3 px-4 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-xl text-xs flex items-center justify-center gap-2 transition"
        >
          <RefreshCw size={14} />
          <span>Try Again (Blind Retry)</span>
        </button>

        <button
          onClick={onSwitchToSudhaar}
          className="w-full py-3 px-4 bg-[#00BAF2] hover:bg-[#009fd2] text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 shadow-md transition transform active:scale-95"
        >
          <span>See with Sudhaar AI Agent ✨</span>
        </button>
      </div>
    </div>
  );
};

