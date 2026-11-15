import React, { useState, useEffect, useRef } from "react";
import { ChevronDown, ChevronRight, Cpu, Sparkles, ShieldCheck, UserCheck, Terminal, Maximize2, Database, Clock } from "lucide-react";
import Link from "next/link";
import { AuditEntry } from "@/lib/api";
import { InspectionDrawer } from "./InspectionDrawer";

interface LiveTraceProps {
  auditTrail: AuditEntry[];
  activeCaseId?: string;
  sourceMode?: string;
  showConsoleLink?: boolean;
  isDrafting?: boolean;
}

export const LiveTrace: React.FC<LiveTraceProps> = ({
  auditTrail,
  activeCaseId,
  sourceMode = "template",
  showConsoleLink = true,
  isDrafting = false,
}) => {
  const [selectedEntry, setSelectedEntry] = useState<{ entry: AuditEntry; index: number } | null>(null);
  const [expandedInline, setExpandedInline] = useState<Record<string, boolean>>({});
  const traceEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the newest step
  useEffect(() => {
    traceEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [auditTrail]);

  const toggleInline = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedInline((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const openDrawer = (entry: AuditEntry, index: number) => {
    setSelectedEntry({ entry, index });
  };

  const getLayerBadge = (stage: string, layer: string, isAi: boolean, details: Record<string, any>) => {
    if (stage === "VOICE") {
      if (isAi || details.source === "sarvam") {
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-purple-900/70 text-purple-200 border border-purple-400 shadow-sm flex-shrink-0">
            <Sparkles size={11} className="text-purple-300" />
            <span>AI MODEL (Sarvam)</span>
          </span>
        );
      }
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-sky-950/80 text-sky-300 border border-sky-600/40 flex-shrink-0">
          <Cpu size={11} />
          <span>DETERMINISTIC CODE</span>
        </span>
      );
    }

    if (stage === "LLM_DRAFT" || isAi) {
      if (isAi || details.source === "gemini" || (details.summary && details.summary.includes("Gemini"))) {
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-purple-900/70 text-purple-200 border border-purple-400 shadow-sm flex-shrink-0">
            <Sparkles size={11} className="text-purple-300" />
            <span>AI MODEL (Gemini)</span>
          </span>
        );
      }
    }

    if (stage === "TEMPLATE_FALLBACK" || details.source === "template") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-sky-950/80 text-sky-300 border border-sky-600/40 flex-shrink-0">
          <Cpu size={11} />
          <span>DETERMINISTIC CODE</span>
        </span>
      );
    }

    if (layer === "SAFETY_GATE") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/50 flex-shrink-0">
          <ShieldCheck size={11} />
          <span>SAFETY GATE</span>
        </span>
      );
    }
    if (layer === "CUSTOMER_ACTION") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 flex-shrink-0">
          <UserCheck size={11} />
          <span>CUSTOMER ACTION</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-sky-950/80 text-sky-300 border border-sky-600/40 flex-shrink-0">
        <Cpu size={11} />
        <span>DETERMINISTIC CODE</span>
      </span>
    );
  };

  const getHumanReadableSummary = (entry: AuditEntry): string => {
    if (entry.details && entry.details.summary) {
      return entry.details.summary;
    }
    switch (entry.stage) {
      case "EVENT":
        return `Mandate failed · code ${entry.details.code || "AP15"} · attempt 1`;
      case "PLAYBOOK":
        return entry.details.playbook_name || "Mandate retry playbook";
      case "FACTS":
        return `HDFC ••9012 failed · SBI ••4521 available · language ${entry.details.language || "Marathi"}`;
      case "CODE_LOOKUP":
        return `${entry.details.code || "AP15"} → ${entry.details.cause || "required balance not maintained"}`;
      case "RULES":
        return `Allowed actions: ${Array.isArray(entry.details.allowed_actions) ? entry.details.allowed_actions.join(", ") : "retry_mandate, book_callback"}`;
      case "LLM_DRAFT":
        return entry.details.explanation ? `Generated explanation (${entry.details.source || "template"})` : "Generated message";
      case "TEMPLATE_FALLBACK":
        return "Approved template used";
      case "VALIDATOR":
        return "Numbers ✓ · Action allowed ✓ · Language ✓";
      case "CONSENT_PROPOSED":
        return `Proposed ${entry.details.action || "retry_mandate"} with SBI ••4521`;
      case "CONSENT_RECEIVED":
        return entry.details.consent_given ? "Customer confirmed retry_mandate via tap" : "Customer declined action";
      case "ACTION":
        return `retry_mandate executed · Ref ${entry.details.reference_id || "MND-SBI-4521"}`;
      case "AUDIT":
        return "Case closed · Receipt logged";
      default:
        return JSON.stringify(entry.details).slice(0, 45);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-900 border border-slate-800 rounded-2xl p-3 md:p-4 overflow-hidden shadow-2xl h-full">
      {/* Console Header */}
      <div className="flex items-center justify-between pb-2.5 mb-2 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#00BAF2]/20 border border-[#00BAF2]/40 flex items-center justify-center text-[#00BAF2]">
            <Terminal size={13} />
          </div>
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>Operator Execution Trace</span>
            </h2>
            <p className="text-[11px] text-slate-400 font-mono">
              Case: {activeCaseId || "Standby / Idle"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300 border border-slate-700">
            {auditTrail.length} / 10 Steps
          </span>

          {showConsoleLink && (
            <Link
              href="/console"
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition flex items-center gap-1 text-[11px] font-mono border border-slate-700"
              title="Open Fullscreen Operator Console"
            >
              <Maximize2 size={11} />
              <span className="hidden sm:inline">/console</span>
            </Link>
          )}
        </div>
      </div>

      {/* Compact Single-Line Trace List with Step Numbers & Latencies */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 font-sans">
        {auditTrail.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs text-center p-6 space-y-1.5">
            <Cpu size={28} className="opacity-40" />
            <p>Waiting for a loan failure event...</p>
          </div>
        ) : (
          auditTrail.map((entry, idx) => {
            const stepNum = String(idx + 1).padStart(2, "0");
            const isInlineExpanded = expandedInline[entry.entry_id];
            const summaryText = getHumanReadableSummary(entry);
            const latencyStr = entry.details.latency_sec
              ? `${entry.details.latency_sec}s`
              : entry.is_ai
              ? "AI"
              : "<5ms";

            return (
              <div
                key={entry.entry_id}
                className="bg-slate-950/70 hover:bg-slate-950 rounded-lg border border-slate-800/80 px-3 py-1.5 transition text-xs flex flex-col gap-1 cursor-pointer group"
                onClick={() => openDrawer(entry, idx + 1)}
              >
                {/* Single Compact Header Line */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0 flex-1 overflow-hidden">
                    {/* Step Number */}
                    <span className="text-[10px] font-mono text-slate-500 font-bold w-5 flex-shrink-0">
                      {stepNum}
                    </span>

                    {/* Stage Name */}
                    <span className="font-mono text-xs md:text-sm font-bold text-white tracking-wide uppercase w-28 md:w-36 flex-shrink-0 truncate group-hover:text-[#00BAF2] transition">
                      {entry.stage === "TEMPLATE_FALLBACK" ? "TEMPLATE" : entry.stage}
                    </span>

                    {/* Badge */}
                    {getLayerBadge(entry.stage, entry.layer, entry.is_ai, entry.details)}

                    {/* Human readable line */}
                    <span className="text-slate-200 text-xs md:text-[13px] font-medium truncate ml-1 flex-1">
                      {summaryText}
                    </span>
                  </div>

                  {/* Latency & Inspect Actions */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 flex items-center gap-1">
                      <Clock size={10} className="text-slate-500" />
                      <span>{latencyStr}</span>
                    </span>

                    <button
                      onClick={(e) => toggleInline(entry.entry_id, e)}
                      title="Quick JSON toggle"
                      className="text-slate-400 hover:text-white text-[11px] font-mono flex items-center gap-0.5 px-1 py-0.5 rounded hover:bg-slate-800 transition"
                    >
                      <span>{isInlineExpanded ? "less" : "inspect"}</span>
                      {isInlineExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                    </button>
                  </div>
                </div>

                {/* Inline Quick JSON view */}
                {isInlineExpanded && (
                  <div
                    className="mt-1 pt-1.5 border-t border-slate-800/80"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <pre className="text-[10px] font-mono text-sky-300 bg-slate-900/90 p-2 rounded overflow-x-auto border border-slate-800 max-h-40">
                      {JSON.stringify(entry.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Pending Progressive Row for LLM Gateway (Requirement 3) */}
        {isDrafting && (
          <div className="bg-purple-950/40 rounded-lg border border-purple-500/50 px-3 py-1.5 text-xs flex items-center justify-between gap-2 animate-pulse shadow-sm">
            <div className="flex items-center gap-2 min-w-0 flex-1 overflow-hidden">
              <span className="text-[10px] font-mono text-purple-400 font-bold w-5 flex-shrink-0">
                {String(auditTrail.length + 1).padStart(2, "0")}
              </span>
              <span className="font-mono text-xs md:text-sm font-bold text-purple-300 tracking-wide uppercase w-28 md:w-36 flex-shrink-0 truncate">
                LLM_DRAFT
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-purple-900/80 text-purple-200 border border-purple-400 shadow-sm flex-shrink-0">
                <Sparkles size={11} className="text-purple-300 animate-spin" />
                <span>AI MODEL (Gemini)</span>
              </span>
              <span className="text-purple-200 text-xs md:text-[13px] font-medium truncate ml-1 flex-1">
                Sudhaar is drafting explanation with Gemini...
              </span>
            </div>
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-[10px] font-mono text-purple-300 bg-purple-900/60 px-2 py-0.5 rounded border border-purple-600/50">
                writing…
              </span>
            </div>
          </div>
        )}
        <div ref={traceEndRef} />
      </div>

      {/* Slide-over Inspection Drawer for deep inspection */}
      <InspectionDrawer
        entry={selectedEntry?.entry || null}
        stepIndex={selectedEntry?.index || 1}
        totalSteps={auditTrail.length}
        onClose={() => setSelectedEntry(null)}
      />
    </div>
  );
};
