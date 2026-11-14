import React from "react";
import { ArrowLeft, Wifi, Battery, Signal } from "lucide-react";

interface PaytmHeaderProps {
  title?: string;
  onBack?: () => void;
}

export const PaytmHeader: React.FC<PaytmHeaderProps> = ({
  title = "Personal Loan",
  onBack,
}) => {
  return (
    <div className="bg-[#002970] text-white pt-2 pb-3 px-4 shadow-md">
      {/* iOS style status bar */}
      <div className="flex justify-between items-center text-xs text-white/80 pb-2 px-1 font-medium">
        <span>9:41</span>
        <div className="flex items-center space-x-1.5">
          <Signal size={12} />
          <Wifi size={12} />
          <Battery size={14} />
        </div>
      </div>

      {/* Main navigation header */}
      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center space-x-2">
          {onBack && (
            <button
              onClick={onBack}
              className="p-1 -ml-1 text-white/90 hover:text-white rounded-full hover:bg-white/10 transition"
            >
              <ArrowLeft size={18} />
            </button>
          )}
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
              <span>{title}</span>
            </h1>
            <p className="text-[10px] text-[#00BAF2] font-semibold tracking-wide uppercase">
              Nimbus Finance
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
