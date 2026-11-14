"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { LiveTrace } from "../../components/console/LiveTrace";
import { getCaseDetails, CaseData } from "../../lib/api";
import { ArrowLeft, RefreshCw, Shield, Sparkles, CheckCircle2 } from "lucide-react";

export default function StandaloneConsolePage() {
  const [caseId, setCaseId] = useState<string>("CASE-EVT-ROHIT-DEMO-01");
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchTrace = async (id: string) => {
    setIsLoading(true);
    try {
      const data = await getCaseDetails(id);
      setCaseData(data);
    } catch (e) {
      console.error("Failed to load trace for case:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTrace(caseId);
    const interval = setInterval(() => fetchTrace(caseId), 2000);
    return () => clearInterval(interval);
  }, [caseId]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <div className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              <span>Sudhaar Operator Console</span>
              <span className="text-xs bg-[#00BAF2]/20 text-[#00BAF2] border border-[#00BAF2]/40 px-2 py-0.5 rounded-full font-mono">
                Nimbus Finance
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Live audit pipeline • Deterministic code vs AI model verification
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Quick Case Selectors */}
          <div className="flex items-center gap-1.5 text-xs font-mono">
            <span className="text-slate-400">Case:</span>
            {["CASE-EVT-ROHIT-DEMO-01", "CASE-EVT-ASHA-DEMO-01", "CASE-EVT-SUNITA-DEMO-01"].map((id) => (
              <button
                key={id}
                onClick={() => setCaseId(id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition ${
                  caseId === id
                    ? "bg-[#00BAF2] text-white font-bold"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {id.split("-")[2]}
              </button>
            ))}
          </div>

          <button
            onClick={() => fetchTrace(caseId)}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh Trace"
          >
            <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-6 max-w-6xl mx-auto w-full flex flex-col gap-6">
        {/* KPI Strip */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] text-slate-400 uppercase font-mono">Active Case</span>
            <p className="text-sm font-bold text-white font-mono mt-1">{caseId}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] text-slate-400 uppercase font-mono">Status</span>
            <p className="text-sm font-bold text-emerald-400 font-mono mt-1">
              {caseData?.status || "STANDBY"}
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] text-slate-400 uppercase font-mono">Mode</span>
            <p className="text-sm font-bold text-sky-400 font-mono mt-1">
              {caseData?.source_mode.toUpperCase() || "TEMPLATE"}
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] text-slate-400 uppercase font-mono">Audit Entries</span>
            <p className="text-sm font-bold text-purple-400 font-mono mt-1">
              {caseData?.audit_trail?.length || 0} Stages Committed
            </p>
          </div>
        </div>

        {/* Live Trace */}
        <div className="flex-1 min-h-[500px]">
          <LiveTrace
            auditTrail={caseData?.audit_trail || []}
            activeCaseId={caseId}
            sourceMode={caseData?.source_mode}
          />
        </div>
      </div>
    </div>
  );
}
