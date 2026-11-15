import React, { useState, useEffect, useRef } from "react";
import { Sparkles, CheckCircle2, XCircle, ArrowRight, ShieldCheck, Volume2, VolumeX, AlertTriangle, Calendar, Clock } from "lucide-react";
import { LanguageChips } from "./LanguageChips";
import { fetchTTSAudio } from "@/lib/api";

interface SudhaarCardProps {
  language: string;
  onLanguageChange: (lang: string) => void;
  explanation: string;
  actionLabel?: string;
  visualData?: Record<string, any>;
  onProposeAction: () => void;
  sourceMode?: string;
  isDrafting?: boolean;
  onVoiceLogged?: (traceSummary: string, isAi: boolean) => void;
}

export const SudhaarCard: React.FC<SudhaarCardProps> = ({
  language,
  onLanguageChange,
  explanation,
  actionLabel = "Fix this issue",
  visualData,
  onProposeAction,
  sourceMode = "template",
  isDrafting = false,
  onVoiceLogged,
}) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Cancel any speech synthesis on language or explanation change
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsSpeaking(false);
  }, [language, explanation]);

  const fallbackToBrowserSpeech = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setIsSpeaking(false);
      return;
    }
    onVoiceLogged?.("Voice: browser fallback", false);
    const utterance = new SpeechSynthesisUtterance(explanation);
    utterance.lang = language === "hi" ? "hi-IN" : language === "mr" ? "mr-IN" : "en-IN";
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const handleToggleSpeak = async () => {
    if (isSpeaking) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
      return;
    }

    try {
      setIsSpeaking(true);
      const res = await fetchTTSAudio(explanation, language);
      if (res && res.blob) {
        const trace = res.source === "cached" ? "Voice: Sarvam (cached)" : "Voice: Sarvam";
        onVoiceLogged?.(trace, true);

        const url = URL.createObjectURL(res.blob);
        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(url);
          audioRef.current = null;
        };
        audio.onerror = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(url);
          audioRef.current = null;
          fallbackToBrowserSpeech();
        };

        await audio.play();
      } else {
        fallbackToBrowserSpeech();
      }
    } catch {
      fallbackToBrowserSpeech();
    }
  };

  const isAccountComparison = visualData && visualData.failed_account && visualData.suggested_account;
  const isTimelineMismatch = visualData && visualData.closure_event && visualData.erroneous_debit;
  const isChecklist = visualData && visualData.checklist;
  const isDeductionBreakup = visualData && visualData.deductions;

  return (
    <div className="bg-white rounded-t-3xl border-t-2 border-[#00BAF2] shadow-2xl p-4 md:p-5 flex flex-col gap-3.5 animate-in slide-in-from-bottom duration-300">
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

        {/* Listen Button (Requirement 7) & Language Chips */}
        <div className="flex items-center gap-2">
          {!isDrafting && (
            <button
              onClick={handleToggleSpeak}
              title="Listen to explanation"
              className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold flex items-center gap-1 transition ${
                isSpeaking
                  ? "bg-purple-100 text-purple-700 border border-purple-300 animate-pulse font-bold"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200"
              }`}
            >
              {isSpeaking ? (
                <>
                  <VolumeX size={12} />
                  <span>Stop</span>
                </>
              ) : (
                <>
                  <Volume2 size={12} className="text-[#002970]" />
                  <span>{language === "hi" ? "सुनें" : language === "mr" ? "ऐका" : "Listen"}</span>
                </>
              )}
            </button>
          )}

          <LanguageChips
            currentLanguage={language}
            onSelectLanguage={onLanguageChange}
          />
        </div>
      </div>

      {/* Explanation text or Shimmering Skeleton (Requirement 3) */}
      {isDrafting ? (
        <div className="bg-blue-50/60 rounded-xl p-3.5 border border-blue-100/80 space-y-2.5 animate-pulse">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#002970]">
            <Sparkles size={13} className="text-[#00BAF2] animate-spin" />
            <span>
              {language === "hi"
                ? "सुधार लिख रहा है..."
                : language === "mr"
                ? "सुधार लिहित आहे..."
                : "Sudhaar is writing…"}
            </span>
          </div>
          <div className="space-y-1.5">
            <div className="h-3 bg-blue-200/60 rounded w-full" />
            <div className="h-3 bg-blue-200/60 rounded w-5/6" />
            <div className="h-3 bg-blue-200/60 rounded w-3/4" />
          </div>
        </div>
      ) : (
        <div className="bg-blue-50/60 rounded-xl p-3 border border-blue-100/80">
          <p className="text-xs text-slate-800 leading-relaxed font-medium">
            {explanation}
          </p>
        </div>
      )}

      {/* Visual Component: Rohit Account Comparison */}
      {isAccountComparison && !isDrafting && (
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

      {/* Visual Component: Asha Timeline Mismatch Side-by-Side (Requirement 5) */}
      {isTimelineMismatch && !isDrafting && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          {/* Card 1: Verified Loan Closure */}
          <div className="p-2.5 rounded-xl border border-emerald-200 bg-emerald-50/50 flex flex-col justify-between">
            <div className="flex items-center justify-between text-emerald-800 mb-1">
              <span className="font-bold text-[11px] flex items-center gap-1">
                <CheckCircle2 size={13} className="text-emerald-600" />
                <span>Loan Closed</span>
              </span>
              <span className="text-[9px] bg-emerald-100 text-emerald-700 px-1 py-0.2 rounded font-mono font-bold">
                VERIFIED
              </span>
            </div>
            <p className="text-xs font-bold text-slate-900 mt-1">
              {visualData.closure_event.date}
            </p>
            <span className="text-[10px] text-slate-500 mt-0.5">
              Settled in Full
            </span>
          </div>

          {/* Card 2: Erroneous Clearing Debit */}
          <div className="p-2.5 rounded-xl border border-rose-300 bg-rose-50/60 flex flex-col justify-between relative shadow-xs">
            <div className="flex items-center justify-between text-rose-700 mb-1">
              <span className="font-bold text-[11px] flex items-center gap-1">
                <AlertTriangle size={13} className="text-rose-600" />
                <span>EMI Debited</span>
              </span>
              <span className="text-[9px] bg-rose-100 text-rose-700 px-1 py-0.2 rounded font-mono font-bold">
                Debited after closure
              </span>
            </div>
            <p className="text-xs font-bold text-rose-700 mt-1">
              {visualData.erroneous_debit.amount} on {visualData.erroneous_debit.date}
            </p>
            <span className="text-[10px] text-slate-500 mt-0.5">
              ICICI ••7810
            </span>
          </div>
        </div>
      )}

      {/* Visual Component: Sunita Checklist */}
      {isChecklist && !isDrafting && (
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

      {/* Visual Component: Meena Deduction Breakup */}
      {isDeductionBreakup && !isDrafting && (
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-xs space-y-1.5">
          <div className="flex justify-between items-center text-[11px] pb-1 border-b border-slate-200 font-semibold text-slate-800">
            <span>Approved Loan</span>
            <span className="font-bold text-[#002970]">{visualData.approved_amount}</span>
          </div>
          <div className="space-y-1 text-[10px]">
            {visualData.deductions.map((d: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center text-slate-600">
                <span>{d.label}</span>
                <span className="font-mono font-medium text-slate-700">{d.amount}</span>
              </div>
            ))}
          </div>
          <div className="flex justify-between items-center text-[11px] pt-1 border-t border-slate-200 font-bold text-emerald-700">
            <span>Net Disbursed</span>
            <span>{visualData.disbursed_amount}</span>
          </div>
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
        disabled={isDrafting}
        className="w-full py-3.5 px-4 bg-[#002970] hover:bg-[#051A44] active:scale-[0.99] text-white font-bold rounded-2xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-blue-950/20 transition disabled:opacity-50"
      >
        <span>{actionLabel}</span>
        <ArrowRight size={15} />
      </button>
    </div>
  );
};
