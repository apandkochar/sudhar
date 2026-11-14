import React, { useState } from "react";
import { ChevronDown, ChevronRight, Cpu, Sparkles, ShieldCheck, UserCheck, Terminal } from "lucide-react";
import { AuditEntry } from "@/lib/api";

interface LiveTraceProps {
  auditTrail: AuditEntry[];
  activeCaseId?: string;
  sourceMode?: string;
}

export const LiveTrace: React.FC<LiveTraceProps> = ({
  auditTrail,
  activeCaseId,
  sourceMode = "template",
}) => {
  const [expandedEntries, setExpandedEntries] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpandedEntries((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getLayerBadge = (layer: string, isAi: boolean) => {
    if (isAi || layer === "AI_GATEWAY") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
          <Sparkles size={10} />
          <span>AI MODEL</span>
        </span>
      );
    }
    if (layer === "SAFETY_GATE") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
          <ShieldCheck size={10} />
          <span>SAFETY GATE</span>
        </span>
      );
    }
    if (layer === "CUSTOMER_ACTION") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
          <UserCheck size={10} />
          <span>CUSTOMER ACTION</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40">
        <Cpu size={10} />
        <span>DETERMINISTIC CODE</span>
      </span>
    );
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-900 border border-slate-800 rounded-2xl p-4 overflow-hidden shadow-2xl">
      {/* Console Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#00BAF2]/20 border border-[#00BAF2]/40 flex items-center justify-center text-[#00BAF2]">
            <Terminal size={14} />
          </div>
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              Operator Execution Trace
            </h2>
            <p className="text-[11px] text-slate-400 font-mono">
              Case: {activeCaseId || "Idle (No active event)"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800 text-[10px] font-mono text-slate-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span>Live Audit Store</span>
          </div>
        </div>
      </div>

      {/* Trace Timeline List */}
      <div className="flex-1 overflow-y-auto pt-4 space-y-3 pr-1">
        {auditTrail.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs text-center p-6 space-y-2">
            <Cpu size={32} className="opacity-40" />
            <p>Waiting for a loan failure event...</p>
            <p className="text-[11px] text-slate-600">
              Click any scenario button on top to inject a real broken moment.
            </p>
          </div>
        ) : (
          auditTrail.map((entry, index) => {
            const isExpanded = expandedEntries[entry.entry_id];
            const isLast = index === auditTrail.length - 1;

            return (
              <div
                key={entry.entry_id}
                className="relative pl-6 pb-2 border-l-2 border-slate-800 last:border-l-0"
              >
                {/* Node icon circle */}
                <div
                  className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                    entry.is_ai
                      ? "bg-purple-950 border-purple-400"
                      : entry.layer === "SAFETY_GATE"
                      ? "bg-amber-950 border-amber-400"
                      : entry.layer === "CUSTOMER_ACTION"
                      ? "bg-emerald-950 border-emerald-400"
                      : "bg-sky-950 border-sky-400"
                  }`}
                >
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${
                      entry.is_ai
                        ? "bg-purple-400"
                        : entry.layer === "SAFETY_GATE"
                        ? "bg-amber-400"
                        : entry.layer === "CUSTOMER_ACTION"
                        ? "bg-emerald-400"
                        : "bg-sky-400"
                    }`}
                  />
                </div>

                {/* Entry Card */}
                <div className="bg-slate-950/60 rounded-xl border border-slate-800/80 p-3 hover:border-slate-700 transition">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-white tracking-wide">
                        {entry.stage}
                      </span>
                      {getLayerBadge(entry.layer, entry.is_ai)}
                    </div>

                    <span className="text-[10px] font-mono text-slate-500">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  {/* Summary row */}
                  <div className="mt-1.5 flex items-center justify-between">
                    <p className="text-[11px] text-slate-300 truncate max-w-[280px]">
                      {entry.details.cause ||
                        entry.details.explanation ||
                        entry.details.message ||
                        (entry.details.rule && `Rule: ${entry.details.rule}`) ||
                        (entry.details.action && `Action: ${entry.details.action}`) ||
                        JSON.stringify(entry.details).slice(0, 45) + "..."}
                    </p>

                    <button
                      onClick={() => toggleExpand(entry.entry_id)}
                      className="text-slate-400 hover:text-white text-[11px] flex items-center gap-0.5 font-mono"
                    >
                      <span>{isExpanded ? "hide" : "inspect"}</span>
                      {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </button>
                  </div>

                  {/* Expandable JSON Inspector for Judges */}
                  {isExpanded && (
                    <div className="mt-2 pt-2 border-t border-slate-800">
                      <pre className="text-[10px] font-mono text-sky-300 bg-slate-900/90 p-2 rounded-lg overflow-x-auto border border-slate-800/80">
                        {JSON.stringify(entry.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
