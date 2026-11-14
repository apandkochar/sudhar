import React from "react";
import { Check, AlertCircle } from "lucide-react";

interface StepperProps {
  currentStep: number; // 1 to 5
  isFailed?: boolean;
}

const STEPS = ["Offer", "KYC", "Mandate", "Sign", "Disbursal"];

export const Stepper: React.FC<StepperProps> = ({ currentStep = 3, isFailed = false }) => {
  return (
    <div className="bg-white py-3 px-4 border-b border-slate-200">
      <div className="flex items-center justify-between relative">
        {/* Connecting line */}
        <div className="absolute left-4 right-4 top-3.5 h-[2px] bg-slate-200 -z-0" />
        <div
          className="absolute left-4 top-3.5 h-[2px] bg-[#00BAF2] -z-0 transition-all duration-300"
          style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
        />

        {STEPS.map((step, idx) => {
          const stepNum = idx + 1;
          const isCompleted = stepNum < currentStep;
          const isCurrent = stepNum === currentStep;
          const isCurrentFailed = isCurrent && isFailed;

          return (
            <div key={step} className="flex flex-col items-center relative z-10">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                  isCompleted
                    ? "bg-[#00BAF2] text-white"
                    : isCurrentFailed
                    ? "bg-red-500 text-white ring-4 ring-red-100"
                    : isCurrent
                    ? "bg-[#002970] text-white ring-4 ring-blue-100"
                    : "bg-white text-slate-400 border-2 border-slate-300"
                }`}
              >
                {isCompleted ? (
                  <Check size={14} strokeWidth={3} />
                ) : isCurrentFailed ? (
                  <AlertCircle size={14} />
                ) : (
                  stepNum
                )}
              </div>
              <span
                className={`text-[10px] mt-1 font-medium ${
                  isCurrentFailed
                    ? "text-red-600 font-semibold"
                    : isCurrent
                    ? "text-[#002970] font-bold"
                    : "text-slate-500"
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
