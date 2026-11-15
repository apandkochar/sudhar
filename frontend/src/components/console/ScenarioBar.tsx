import React from "react";
import Link from "next/link";
import { Play, RotateCcw, Eye, ShieldAlert, Sparkles, Terminal } from "lucide-react";

interface ScenarioBarProps {
  onSelectPersona: (personaId: string) => void;
  activePersonaId: string;
  isBeforeMode: boolean;
  onToggleBeforeMode: (before: boolean) => void;
  onReset: () => void;
  rescuesCount: number;
}

export const ScenarioBar: React.FC<ScenarioBarProps> = ({
  onSelectPersona,
  activePersonaId,
  isBeforeMode,
  onToggleBeforeMode,
  onReset,
  rescuesCount,
}) => {
  return (
    <div className="w-full bg-slate-900 border-b border-slate-800 px-4 md:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-[#002970] to-[#00BAF2] flex items-center justify-center text-white font-extrabold text-xs shadow-md">
          सु
        </div>
        <div>
          <h1 className="text-xs font-bold text-white tracking-tight flex items-center gap-1.5">
            <span>Sudhaar <span className="text-[#00BAF2]">सुधार</span></span>
            <span className="text-[9px] bg-[#00BAF2]/10 text-[#00BAF2] border border-[#00BAF2]/30 px-1.5 py-0.2 rounded font-mono">
              Nimbus Finance
            </span>
          </h1>
        </div>
      </div>

      {/* Persona scenario buttons (Requirement 8) */}
      <div className="flex items-center gap-2">
        <span className="text-[11px] text-slate-400 font-mono hidden md:inline">Trigger:</span>

        {/* Rohit */}
        <button
          onClick={() => onSelectPersona("rohit")}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
            activePersonaId === "rohit"
              ? "bg-[#00BAF2] text-white shadow-md ring-2 ring-[#00BAF2]/30 font-bold"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>Rohit · Mandate failed</span>
        </button>

        {/* Asha */}
        <button
          onClick={() => onSelectPersona("asha")}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
            activePersonaId === "asha"
              ? "bg-[#00BAF2] text-white shadow-md ring-2 ring-[#00BAF2]/30 font-bold"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-amber-400" />
          <span>Asha · EMI after closure</span>
        </button>

        {/* Sunita */}
        <button
          onClick={() => onSelectPersona("sunita")}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
            activePersonaId === "sunita"
              ? "bg-[#00BAF2] text-white shadow-md ring-2 ring-[#00BAF2]/30 font-bold"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-purple-400" />
          <span>Sunita · Video KYC dropped</span>
        </button>

        {/* Meena */}
        <button
          onClick={() => onSelectPersona("meena")}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
            activePersonaId === "meena"
              ? "bg-[#00BAF2] text-white shadow-md ring-2 ring-[#00BAF2]/30 font-bold"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          <span>Meena · Disbursal breakup</span>
        </button>
      </div>

      {/* Before/After Toggle & Stats */}
      <div className="flex items-center gap-2.5">
        <div className="flex bg-slate-800 p-0.5 rounded-xl border border-slate-700 text-xs">
          <button
            onClick={() => onToggleBeforeMode(true)}
            className={`px-2.5 py-1 rounded-lg font-medium transition ${
              isBeforeMode
                ? "bg-red-500/20 text-red-300 border border-red-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Today's UX (Before)
          </button>
          <button
            onClick={() => onToggleBeforeMode(false)}
            className={`px-2.5 py-1 rounded-lg font-bold flex items-center gap-1 transition ${
              !isBeforeMode
                ? "bg-[#002970] text-white border border-[#00BAF2]/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Sparkles size={11} className="text-[#00BAF2]" />
            <span>With Sudhaar (After)</span>
          </button>
        </div>

        {/* Session Counter: Tickets avoided: N */}
        <div className="px-2 py-1 bg-slate-800 rounded-xl border border-slate-700 text-[11px] font-mono text-slate-300 flex items-center gap-1">
          <span className="text-slate-400">Tickets avoided:</span>
          <span className="font-bold text-emerald-400">{rescuesCount}</span>
        </div>

        {/* Operator Console Link */}
        <Link
          href="/console"
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl transition border border-slate-700 text-[11px] font-mono flex items-center gap-1"
          title="Open Dedicated Fullscreen Operator Console"
        >
          <Terminal size={12} className="text-[#00BAF2]" />
          <span className="hidden sm:inline">Console</span>
        </Link>

        {/* Reset button */}
        <button
          onClick={onReset}
          title="Reset database to initial state"
          className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-xl transition border border-slate-700"
        >
          <RotateCcw size={14} />
        </button>
      </div>
    </div>
  );
};
