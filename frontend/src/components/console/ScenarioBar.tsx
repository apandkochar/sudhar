import React from "react";
import { Play, RotateCcw, Eye, ShieldAlert, Sparkles } from "lucide-react";

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
    <div className="w-full bg-slate-900 border-b border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Track badge */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#002970] to-[#00BAF2] flex items-center justify-center text-white font-extrabold text-sm shadow-md">
          सु
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold text-white tracking-tight">
              Sudhaar <span className="text-[#00BAF2]">सुधार</span>
            </h1>
            <span className="text-[10px] bg-[#00BAF2]/10 text-[#00BAF2] border border-[#00BAF2]/30 px-2 py-0.2 rounded-full font-mono font-medium">
              Track 2 • Build for India
            </span>
          </div>
          <p className="text-[10px] text-slate-400">
            Paytm-style loan journey rescue agent • Nimbus Finance
          </p>
        </div>
      </div>

      {/* Persona scenario buttons */}
      <div className="flex items-center gap-2">
        <span className="text-[11px] text-slate-400 font-mono mr-1">Trigger:</span>

        {/* Rohit */}
        <button
          onClick={() => onSelectPersona("rohit")}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
            activePersonaId === "rohit"
              ? "bg-[#00BAF2] text-white shadow-md ring-2 ring-[#00BAF2]/30"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>Rohit (Hero • AP15 मराठी)</span>
        </button>

        {/* Asha */}
        <button
          onClick={() => onSelectPersona("asha")}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
            activePersonaId === "asha"
              ? "bg-[#00BAF2] text-white shadow-md ring-2 ring-[#00BAF2]/30"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-amber-400" />
          <span>Asha (Post-Closure हिंदी)</span>
        </button>

        {/* Sunita */}
        <button
          onClick={() => onSelectPersona("sunita")}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
            activePersonaId === "sunita"
              ? "bg-[#00BAF2] text-white shadow-md ring-2 ring-[#00BAF2]/30"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-purple-400" />
          <span>Sunita (vKYC Drop मराठी)</span>
        </button>
      </div>

      {/* Before/After Toggle & Stats */}
      <div className="flex items-center gap-3">
        {/* Toggle pill */}
        <div className="flex bg-slate-800 p-0.5 rounded-xl border border-slate-700 text-xs">
          <button
            onClick={() => onToggleBeforeMode(true)}
            className={`px-3 py-1 rounded-lg font-medium transition ${
              isBeforeMode
                ? "bg-red-500/20 text-red-300 border border-red-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Today's UX (Before)
          </button>
          <button
            onClick={() => onToggleBeforeMode(false)}
            className={`px-3 py-1 rounded-lg font-bold flex items-center gap-1 transition ${
              !isBeforeMode
                ? "bg-[#002970] text-white border border-[#00BAF2]/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Sparkles size={11} className="text-[#00BAF2]" />
            <span>With Sudhaar (After)</span>
          </button>
        </div>

        {/* Rescues Counter Badge */}
        <div className="px-2.5 py-1 bg-slate-800 rounded-xl border border-slate-700 text-[11px] font-mono text-slate-300 flex items-center gap-1.5">
          <span className="text-slate-400">Rescues:</span>
          <span className="font-bold text-emerald-400">{rescuesCount}</span>
        </div>

        {/* Reset button */}
        <button
          onClick={onReset}
          title="Reset database to initial state"
          className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-xl transition border border-slate-700"
        >
          <RotateCcw size={15} />
        </button>
      </div>
    </div>
  );
};

