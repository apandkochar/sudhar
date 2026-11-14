import React, { useState, useRef, useEffect } from "react";
import { ShieldAlert, Check, X, AlertCircle, Lock, Loader2 } from "lucide-react";

interface ConsentCardProps {
  actionName: string;
  targetAccount?: string;
  whatItDoes: string;
  whatItDoesNotDo: string;
  howToUndo: string;
  onConfirm: () => void;
  onDecline: () => void;
  isProcessing?: boolean;
}

export const ConsentCard: React.FC<ConsentCardProps> = ({
  actionName,
  targetAccount = "State Bank of India ending 4521",
  whatItDoes,
  whatItDoesNotDo,
  howToUndo,
  onConfirm,
  onDecline,
  isProcessing = false,
}) => {
  const [hasTapped, setHasTapped] = useState(false);
  const tappedRef = useRef(false);

  useEffect(() => {
    tappedRef.current = false;
    setHasTapped(false);
  }, [actionName]);

  const handleConfirmClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (tappedRef.current || isProcessing || hasTapped) {
      return;
    }
    tappedRef.current = true;
    setHasTapped(true);
    onConfirm();
  };

  const isButtonDisabled = hasTapped || isProcessing;
  return (
    <div className="bg-white rounded-t-3xl border-t-2 border-[#002970] shadow-2xl p-5 flex flex-col gap-4 animate-in slide-in-from-bottom duration-300">
      {/* Title */}
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <div className="w-8 h-8 rounded-full bg-blue-50 text-[#002970] flex items-center justify-center">
          <Lock size={16} />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Explicit Consent Required
          </h3>
          <p className="text-[10px] text-slate-500">
            Sudhaar acts ONLY with your confirmation.
          </p>
        </div>
      </div>

      {/* 3 Explicit Disclosures */}
      <div className="space-y-2.5 text-xs">
        {/* 1. What will happen */}
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
          <span className="text-[10px] font-bold text-[#002970] uppercase tracking-wider block mb-0.5">
            1. What will happen
          </span>
          <p className="text-slate-700 text-[11px] leading-relaxed">
            {whatItDoes}
          </p>
        </div>

        {/* 2. What it will not do */}
        <div className="bg-amber-50/60 p-2.5 rounded-xl border border-amber-200">
          <span className="text-[10px] font-bold text-amber-900 uppercase tracking-wider block mb-0.5">
            2. What it will NOT do
          </span>
          <p className="text-amber-800 text-[11px] leading-relaxed">
            {whatItDoesNotDo}
          </p>
        </div>

        {/* 3. How to undo */}
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
          <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider block mb-0.5">
            3. How to undo anytime
          </span>
          <p className="text-slate-600 text-[11px] leading-relaxed">
            {howToUndo}
          </p>
        </div>
      </div>

      {/* Buttons */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={onDecline}
          disabled={isButtonDisabled}
          className="flex-1 py-3 px-3 rounded-xl border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-50 active:scale-98 transition flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:pointer-events-none"
        >
          <X size={14} />
          <span>Not Now</span>
        </button>

        <button
          onClick={handleConfirmClick}
          disabled={isButtonDisabled}
          className={`flex-[2] py-3 px-4 rounded-xl bg-[#002970] hover:bg-[#051A44] active:scale-98 text-white font-bold text-xs shadow-md flex items-center justify-center gap-1.5 transition ${
            isButtonDisabled ? "opacity-75 cursor-not-allowed pointer-events-none" : ""
          }`}
        >
          {isButtonDisabled ? (
            <>
              <Loader2 size={16} className="animate-spin text-[#00BAF2]" />
              <span>Authorizing...</span>
            </>
          ) : (
            <>
              <Check size={16} strokeWidth={2.5} />
              <span>Confirm & Authorize</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

