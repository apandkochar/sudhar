import React, { useState } from "react";
import { X, Copy, Check, Sparkles, Cpu, ShieldCheck, UserCheck, Clock, Hash, Database } from "lucide-react";
import { AuditEntry } from "@/lib/api";

interface InspectionDrawerProps {
  entry: AuditEntry | null;
  stepIndex: number;
  totalSteps: number;
  onClose: () => void;
}

export const InspectionDrawer: React.FC<InspectionDrawerProps> = ({
  entry,
  stepIndex,
  totalSteps,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);

  if (!entry) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(entry.details, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLayerBadge = () => {
    if (entry.stage === "LLM_DRAFT" || entry.is_ai) {
      if (entry.is_ai || entry.details.source === "gemini") {
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-purple-900/80 text-purple-200 border border-purple-400 shadow-sm">
            <Sparkles size={13} className="text-purple-300" />
            <span>AI MODEL (Gemini)</span>
          </span>
        );
      }
    }
    if (entry.layer === "SAFETY_GATE") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-amber-950/80 text-amber-300 border border-amber-500/50">
          <ShieldCheck size={13} />
          <span>SAFETY GATE</span>
        </span>
      );
    }
    if (entry.layer === "CUSTOMER_ACTION") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/50">
          <UserCheck size={13} />
          <span>CUSTOMER ACTION</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-sky-950/80 text-sky-300 border border-sky-600/40">
        <Cpu size={13} />
        <span>DETERMINISTIC CODE</span>
      </span>
    );
  };

  const latency = entry.details.latency_sec
    ? `${entry.details.latency_sec} s`
    : entry.is_ai
    ? "AI Latency"
    : "< 5 ms";

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      {/* Backdrop click dismiss */}
      <div className="flex-1" onClick={onClose} />

      {/* Drawer Panel */}
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-mono text-[#00BAF2] font-bold bg-[#00BAF2]/10 border border-[#00BAF2]/30 px-2 py-0.5 rounded">
                STEP {stepIndex} OF {totalSteps}
              </span>
              {getLayerBadge()}
            </div>
            <h2 className="text-base font-bold text-white font-mono tracking-wide">
              {entry.stage === "TEMPLATE_FALLBACK" ? "TEMPLATE" : entry.stage}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Metadata Strip */}
        <div className="px-5 py-3 bg-slate-950/50 border-b border-slate-800/80 grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-300">
            <Clock size={13} className="text-slate-500" />
            <span className="text-slate-400">Latency:</span>
            <span className="font-bold text-sky-400">{latency}</span>
          </div>

          <div className="flex items-center gap-2 text-slate-300">
            <Database size={13} className="text-slate-500" />
            <span className="text-slate-400">Entry ID:</span>
            <span className="text-slate-300 font-semibold">{entry.entry_id}</span>
          </div>

          <div className="flex items-center gap-2 text-slate-300 col-span-2">
            <Hash size={13} className="text-slate-500" />
            <span className="text-slate-400">Idempotency Key:</span>
            <span className="text-slate-400 truncate">
              {entry.idempotency_key || "None (Read-only stage)"}
            </span>
          </div>
        </div>

        {/* Human Readable Summary */}
        <div className="px-5 py-3 bg-slate-800/40 border-b border-slate-800">
          <span className="text-[10px] uppercase font-mono font-bold text-slate-400 block mb-1">
            Summary
          </span>
          <p className="text-xs text-white font-medium">
            {entry.details.summary || JSON.stringify(entry.details).slice(0, 80)}
          </p>
        </div>

        {/* JSON Payload Inspector */}
        <div className="flex-1 flex flex-col p-5 overflow-hidden">
          <div className="flex items-center justify-between pb-2 mb-2">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">
              Raw Payload Inspector
            </span>

            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-mono transition border border-slate-700"
            >
              {copied ? (
                <>
                  <Check size={12} className="text-emerald-400" />
                  <span className="text-emerald-400">Copied!</span>
                </>
              ) : (
                <>
                  <Copy size={12} />
                  <span>Copy JSON</span>
                </>
              )}
            </button>
          </div>

          <div className="flex-1 overflow-auto bg-slate-950 p-4 rounded-xl border border-slate-800">
            <pre className="text-xs font-mono text-sky-300 leading-relaxed overflow-x-auto whitespace-pre">
              {JSON.stringify(entry.details, null, 2)}
            </pre>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-[11px] font-mono text-slate-500">
          <span>Case: {entry.case_id}</span>
          <span>Timestamp: {entry.timestamp}</span>
        </div>
      </div>
    </div>
  );
};

