import React from "react";

interface PhoneFrameProps {
  children: React.ReactNode;
}

export const PhoneFrame: React.FC<PhoneFrameProps> = ({ children }) => {
  return (
    <div className="flex flex-col items-center justify-between h-full max-h-full py-0.5 w-full">
      {/* Outer Mobile Frame */}
      <div className="phone-mockup relative shadow-2xl bg-white border-[10px] border-slate-800 rounded-[44px] overflow-hidden flex flex-col justify-between flex-1 min-h-0 w-[380px]">
        {/* Dynamic Island / Speaker notch */}
        <div className="absolute top-2 left-1/2 -translate-x-1/2 w-28 h-4 bg-slate-900 rounded-full z-50 flex items-center justify-end px-3">
          <div className="w-2.5 h-2.5 bg-slate-800 rounded-full border border-slate-700/50" />
        </div>

        {/* Screen Content Container */}
        <div className="flex-1 flex flex-col overflow-y-auto relative bg-slate-50 pt-2 pb-4 min-h-0">
          {children}
        </div>

        {/* Home Indicator bar */}
        <div className="w-full py-1 flex justify-center bg-white border-t border-slate-100 z-30 flex-shrink-0">
          <div className="w-28 h-1 bg-slate-300 rounded-full" />
        </div>
      </div>

      {/* Non-negotiable Disclaimer Footer */}
      <p className="text-[10px] text-slate-400 text-center max-w-[370px] mt-2 leading-tight font-medium flex-shrink-0">
        Concept prototype for the Paytm Build for India AI Hackathon. Not the Paytm app.
      </p>
    </div>
  );
};

