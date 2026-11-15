import React from "react";
import {
  XCircle,
  RefreshCw,
  AlertTriangle,
  VideoOff,
  HelpCircle,
  PhoneCall,
  RotateCcw,
  Sparkles,
  MessageSquare
} from "lucide-react";

interface BeforeScreenProps {
  onSwitchToSudhaar: () => void;
  personaId?: string;
}

interface ScenarioData {
  badgeTitle: string;
  badgeDesc: string;
  badgeBorder: string;
  badgeBg: string;
  badgeText: string;
  iconBg: string;
  iconColor: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  refLabel: string;
  refValue: string;
  snippet?: {
    header: string;
    body: string;
  };
  retryLabel: string;
  retryIcon: React.ReactNode;
  onRetry: () => void;
}

export const BeforeScreen: React.FC<BeforeScreenProps> = ({
  onSwitchToSudhaar,
  personaId = "rohit",
}) => {
  const scenarios: Record<string, ScenarioData> = {
    rohit: {
      badgeTitle: "Today's Generic Failure Screen",
      badgeDesc:
        "Borrower gets a dead-end message with no reason code or account details. Most users abandon the loan right here.",
      badgeBorder: "border-red-200",
      badgeBg: "bg-red-50",
      badgeText: "text-red-900",
      iconBg: "bg-red-100",
      iconColor: "text-red-600",
      icon: <XCircle size={36} strokeWidth={2.2} />,
      title: "Mandate Registration Failed",
      subtitle:
        "Mandate registration failed. Please try again. If the problem continues, please contact your bank branch.",
      refLabel: "Error Reference",
      refValue: "ERR-MND-9901 (AP15)",
      retryLabel: "Try Again (Blind Retry)",
      retryIcon: <RefreshCw size={14} />,
      onRetry: () =>
        alert(
          "Retrying with the same failed HDFC account will fail again due to AP15 (insufficient balance)."
        ),
    },
    asha: {
      badgeTitle: "Today's Silent EMI Deduction",
      badgeDesc:
        "Borrower is blindsided by a ₹4,500 debit after loan closure. Forced to wait on bank phone support.",
      badgeBorder: "border-amber-200",
      badgeBg: "bg-amber-50",
      badgeText: "text-amber-900",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600",
      icon: <AlertTriangle size={36} strokeWidth={2.2} />,
      title: "Unexpected ₹4,500 EMI Debit",
      subtitle:
        "An EMI of ₹4,500 was deducted today, despite loan LN-ASHA-150K being closed and NOC issued on 28-Oct-2026.",
      refLabel: "Bank Transaction UTR",
      refValue: "UTR-NACH-99482103",
      snippet: {
        header: "Axis Bank SMS · Today 09:30 AM",
        body: "Rs 4,500.00 debited from A/c XX7810 on 12-Nov-26 towards NACH/NIMBUS/LNASHA150K. Avl Bal: Rs 14,200.",
      },
      retryLabel: "Call Bank Support (Wait ~18 mins)",
      retryIcon: <PhoneCall size={14} />,
      onRetry: () =>
        alert(
          "Calling Bank Helpline... All agents are currently busy assisting other customers. Estimated hold time: 18 minutes."
        ),
    },
    sunita: {
      badgeTitle: "Today's Dropped Video Call",
      badgeDesc:
        "Call disconnected due to weak network. Session expires with no recovery link, abandoning the application.",
      badgeBorder: "border-orange-200",
      badgeBg: "bg-orange-50",
      badgeText: "text-orange-900",
      iconBg: "bg-orange-100",
      iconColor: "text-orange-600",
      icon: <VideoOff size={36} strokeWidth={2.2} />,
      title: "Video KYC Disconnected",
      subtitle:
        "Your live video verification call dropped due to connection loss. This verification session has now expired.",
      refLabel: "Session Status",
      refValue: "VKYC-SESSION-EXPIRED-3301",
      snippet: {
        header: "Video KYC Portal",
        body: "Verification incomplete. You cannot resume this call. Please visit a branch or restart your loan application.",
      },
      retryLabel: "Restart Application from Step 1",
      retryIcon: <RotateCcw size={14} />,
      onRetry: () =>
        alert(
          "Application reset: You will need to re-enter PAN, Aadhaar, address verification, and bank statements from step 1."
        ),
    },
    meena: {
      badgeTitle: "Today's Unexplained Deductions",
      badgeDesc:
        "Borrower expected ₹1,00,000 but received ₹96,045. No fee breakup is given, triggering customer dispute.",
      badgeBorder: "border-blue-200",
      badgeBg: "bg-blue-50",
      badgeText: "text-blue-900",
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
      icon: <HelpCircle size={36} strokeWidth={2.2} />,
      title: "Net Disbursed: ₹96,045",
      subtitle:
        "Your approved loan was ₹1,00,000, but ₹3,955 was deducted upfront with no itemized explanation on your screen.",
      refLabel: "Disbursal Reference",
      refValue: "DISB-NIMBUS-99042",
      snippet: {
        header: "HDFC Bank Alert · Today 08:45 AM",
        body: "Rs 96,045.00 credited to A/c XX5541 on 15-Nov-26 from NIMBUS FINANCE. Sanctioned: Rs 1,00,000. Net: Rs 96,045.",
      },
      retryLabel: "Raise Grievance Ticket",
      retryIcon: <MessageSquare size={14} />,
      onRetry: () =>
        alert(
          "Support Ticket #TKT-88421 raised: 'Disbursal amount discrepancy'. Expected turnaround time: 3 to 5 business days."
        ),
    },
  };

  const current = scenarios[personaId] || scenarios.rohit;

  return (
    <div className="flex-1 flex flex-col justify-between p-4 sm:p-5 bg-slate-50 text-slate-800 overflow-y-auto">
      {/* Broken UX Notice */}
      <div
        className={`${current.badgeBg} border ${current.badgeBorder} rounded-xl p-3 flex items-start gap-2.5 shadow-xs`}
      >
        <AlertTriangle
          className="text-amber-600 flex-shrink-0 mt-0.5"
          size={16}
        />
        <div>
          <p className={`text-xs font-bold ${current.badgeText}`}>
            {current.badgeTitle}
          </p>
          <p className="text-[11px] text-slate-600 leading-snug mt-0.5">
            {current.badgeDesc}
          </p>
        </div>
      </div>

      {/* Main Error Body */}
      <div className="flex-1 flex flex-col items-center justify-center text-center my-4 space-y-3">
        <div
          className={`w-14 h-14 ${current.iconBg} rounded-full flex items-center justify-center ${current.iconColor} shadow-inner`}
        >
          {current.icon}
        </div>

        <div>
          <h2 className="text-base font-bold text-slate-900">
            {current.title}
          </h2>
          <p className="text-xs text-slate-500 max-w-[270px] mx-auto mt-1 leading-relaxed">
            {current.subtitle}
          </p>
        </div>

        {/* Optional realistic snippet (e.g. Bank SMS) */}
        {current.snippet && (
          <div className="w-full max-w-[280px] bg-white border border-slate-200 rounded-xl p-2.5 text-left shadow-xs">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              {current.snippet.header}
            </p>
            <p className="text-[11px] font-mono text-slate-700 mt-1 leading-snug">
              {current.snippet.body}
            </p>
          </div>
        )}

        <div className="px-3 py-1 bg-slate-200/80 rounded-md text-[10px] text-slate-600 font-mono">
          <span className="text-slate-400">{current.refLabel}:</span> {current.refValue}
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-2.5 pt-2">
        <button
          onClick={current.onRetry}
          className="w-full py-2.5 px-4 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-xl text-xs flex items-center justify-center gap-2 transition"
        >
          {current.retryIcon}
          <span>{current.retryLabel}</span>
        </button>

        <button
          onClick={onSwitchToSudhaar}
          className="w-full py-2.5 px-4 bg-[#00BAF2] hover:bg-[#009fd2] text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 shadow-md transition transform active:scale-95"
        >
          <Sparkles size={14} />
          <span>See with Sudhaar AI Agent ✨</span>
        </button>
      </div>
    </div>
  );
};
