"use client";

import React, { useState, useEffect, useRef } from "react";
import { PaytmHeader } from "../components/mobile/PaytmHeader";
import { Stepper } from "../components/mobile/Stepper";
import { BeforeScreen } from "../components/mobile/BeforeScreen";
import { SudhaarCard } from "../components/mobile/SudhaarCard";
import { ConsentCard } from "../components/mobile/ConsentCard";
import { ReceiptCard } from "../components/mobile/ReceiptCard";
import { PhoneFrame } from "../components/mobile/PhoneFrame";
import { LiveTrace } from "../components/console/LiveTrace";
import { ScenarioBar } from "../components/console/ScenarioBar";
import { sendEvent, sendConsent, getCaseDetails, resetDatabase, CaseData, AuditEntry } from "../lib/api";
import { Smartphone } from "lucide-react";

const PERSONAS_CONFIG: Record<string, any> = {
  rohit: {
    name: "Rohit Kamble",
    city: "Pune",
    preferred_language: "mr",
    loan_amount: 50000,
    event: {
      event_id: "EVT-ROHIT-DEMO-01",
      event_type: "MANDATE_FAILED",
      customer_id: "CUST-ROHIT-401",
      timestamp: "2026-11-14T10:15:30Z",
      payload: {
        code: "AP15",
        attempt: 1,
        bank_account_masked: "HDFC Bank ending 9012",
        loan_id: "LN-ROHIT-50K"
      }
    }
  },
  asha: {
    name: "Asha Sharma",
    city: "Mumbai",
    preferred_language: "hi",
    loan_amount: 150000,
    event: {
      event_id: "EVT-ASHA-DEMO-01",
      event_type: "EMI_DEBITED_AFTER_CLOSURE",
      customer_id: "CUST-ASHA-102",
      timestamp: "2026-11-05T06:30:00Z",
      payload: {
        code: "LMS_POST_CLOSURE_DEBIT",
        loan_id: "LN-ASHA-PERSONAL-150K",
        closure_date: "2026-11-04",
        debit_date: "2026-11-05",
        excess_debit_amount: 4500,
        bank_account_masked: "ICICI Bank ending 7810"
      }
    }
  },
  sunita: {
    name: "Sunita Devi",
    city: "Jaipur",
    preferred_language: "hi",
    loan_amount: 35000,
    event: {
      event_id: "EVT-SUNITA-DEMO-01",
      event_type: "VKYC_DROPPED",
      customer_id: "CUST-SUNITA-204",
      timestamp: "2026-11-14T11:45:00Z",
      payload: {
        code: "VKYC_NET_DROP",
        call_id: "VKYC-CALL-98214",
        vkyc_stage: "IN_CALL_DROP",
        pan_verified: true,
        drop_reason: "Bandwidth drop below 100kbps during live agent feed",
        mobile_masked: "+91-98XXXX3210",
        resume_window_hours: 72
      }
    }
  }
};

export default function Home() {
  const [activePersonaId, setActivePersonaId] = useState<string>("rohit");
  const [isBeforeMode, setIsBeforeMode] = useState<boolean>(false);
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [cardStep, setCardStep] = useState<"EXPLAIN" | "CONSENT" | "RECEIPT">("EXPLAIN");
  const [currentLanguage, setCurrentLanguage] = useState<string>("mr");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  
  // Requirement 2: Count distinct cases with a successful action only; duplicates never count
  const [rescuedCaseIds, setRescuedCaseIds] = useState<string[]>([]);
  const consentLockRef = useRef(false);

  // Initial load triggers hero scenario
  useEffect(() => {
    handleTriggerScenario(activePersonaId);
  }, []);

  const handleTriggerScenario = async (personaId: string) => {
    const config = PERSONAS_CONFIG[personaId];
    if (!config) return;

    setActivePersonaId(personaId);
    setCurrentLanguage(config.preferred_language);
    setCardStep("EXPLAIN");
    setIsProcessing(true);
    consentLockRef.current = false;

    try {
      const data = await sendEvent(config.event);
      setCaseData(data);
    } catch (err) {
      console.error("Error triggering event:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLanguageChange = async (newLang: string) => {
    setCurrentLanguage(newLang);
    if (caseData) {
      try {
        const config = PERSONAS_CONFIG[activePersonaId];
        const updated = await sendEvent({
          ...config.event,
          event_id: `${config.event.event_id}-${newLang}`,
        });
        setCaseData(updated);
      } catch (e) {
        console.error("Failed to reload language:", e);
      }
    }
  };

  // Requirement 2: Consent must be sent ONLY from Confirm button's onClick. Guard against repeated calls.
  const handleConfirmConsent = async () => {
    if (consentLockRef.current || !caseData || !caseData.proposed_action) return;
    consentLockRef.current = true;
    setIsProcessing(true);

    try {
      const res = await sendConsent({
        case_id: caseData.case_id,
        action: caseData.proposed_action,
        consent_given: true,
        selected_params: caseData.action_params || {},
        idempotency_key: `IDEMP-${caseData.case_id}-${caseData.proposed_action}`,
      });

      const updatedCase = await getCaseDetails(caseData.case_id);
      setCaseData(updatedCase);
      setCardStep("RECEIPT");

      // Distinct cases counter
      setRescuedCaseIds((prev) => {
        if (prev.includes(caseData.case_id)) return prev;
        return [...prev, caseData.case_id];
      });
    } catch (err) {
      console.error("Consent confirmation failed:", err);
      alert("Action execution failed: " + err);
    } finally {
      setIsProcessing(false);
      consentLockRef.current = false;
    }
  };

  const handleDeclineConsent = async () => {
    if (!caseData || !caseData.proposed_action) return;
    try {
      await sendConsent({
        case_id: caseData.case_id,
        action: caseData.proposed_action,
        consent_given: false,
      });
      const updatedCase = await getCaseDetails(caseData.case_id);
      setCaseData(updatedCase);
      setCardStep("EXPLAIN");
    } catch (err) {
      console.error("Consent decline failed:", err);
    }
  };

  // Requirement 2: The reset button clears the trace, counter and case state
  const handleReset = async () => {
    try {
      await resetDatabase();
      setRescuedCaseIds([]);
      setCaseData(null);
      setCardStep("EXPLAIN");
      consentLockRef.current = false;
    } catch (e) {
      console.error("Reset failed:", e);
    }
  };

  // Requirement 4: Show "Failed – action needed" before consent and "Registered" after; never internal states like PROPOSED
  const getCustomerFriendlyStatus = () => {
    if (cardStep === "RECEIPT" || caseData?.status === "EXECUTED") {
      return {
        label: "Registered",
        colorClass: "bg-emerald-50 text-emerald-700 border-emerald-200"
      };
    }
    return {
      label: "Failed – action needed",
      colorClass: "bg-amber-50 text-amber-800 border-amber-200"
    };
  };

  const statusDisplay = getCustomerFriendlyStatus();

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Scenario & Mode Bar */}
      <ScenarioBar
        onSelectPersona={(id) => {
          setIsBeforeMode(false);
          handleTriggerScenario(id);
        }}
        activePersonaId={activePersonaId}
        isBeforeMode={isBeforeMode}
        onToggleBeforeMode={setIsBeforeMode}
        onReset={handleReset}
        rescuesCount={rescuedCaseIds.length}
      />

      {/* Main Dual View Area (Phone Left, Console Right) - Fits 1280px and 1440px widths with no horizontal scroll */}
      <main className="flex-1 min-h-0 w-full px-4 py-2 flex flex-row items-stretch gap-4 overflow-hidden">
        {/* Left Side: Fixed ~400px Phone Column (Requirement 1) */}
        <div className="w-[390px] flex-shrink-0 flex flex-col h-full min-h-0 items-center justify-center">
          <PhoneFrame>
            {/* Header */}
            <PaytmHeader
              title={
                activePersonaId === "asha"
                  ? "Loan Servicing"
                  : activePersonaId === "sunita"
                  ? "Video KYC"
                  : "e-Mandate Setup"
              }
            />

            {/* Journey Stepper */}
            <Stepper
              currentStep={activePersonaId === "sunita" ? 2 : 3}
              isFailed={cardStep !== "RECEIPT"}
            />

            {/* Screen Content: Standby vs Before vs After */}
            {!caseData ? (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-500 space-y-3 bg-slate-50">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-[#002970]">
                  <Smartphone size={24} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-700">Sudhaar Standby</h3>
                  <p className="text-xs text-slate-500 mt-1 max-w-[220px]">
                    Select a scenario from the bar above to simulate a loan moment.
                  </p>
                </div>
              </div>
            ) : isBeforeMode ? (
              <BeforeScreen onSwitchToSudhaar={() => setIsBeforeMode(false)} />
            ) : (
              <div className="flex-1 flex flex-col justify-between bg-slate-100/70 min-h-0">
                {/* Background Context */}
                <div className="p-3 space-y-2">
                  <div className="bg-white p-2.5 rounded-2xl border border-slate-200 shadow-xs">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500 font-medium">Applicant</span>
                      <span className="font-bold text-slate-800">
                        {caseData?.facts?.name || PERSONAS_CONFIG[activePersonaId]?.name}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs mt-1">
                      <span className="text-slate-500 font-medium">Lender</span>
                      <span className="font-semibold text-[#002970]">Nimbus Finance</span>
                    </div>
                    <div className="flex justify-between items-center text-xs mt-1">
                      <span className="text-slate-500 font-medium">Loan Amount</span>
                      <span className="font-bold text-slate-900">
                        ₹{(caseData?.facts?.loan_details?.loan_amount || PERSONAS_CONFIG[activePersonaId]?.loan_amount || 50000).toLocaleString("en-IN")}
                      </span>
                    </div>
                  </div>

                  {/* Customer Friendly Status (Requirement 4) */}
                  <div className={`border rounded-xl px-3 py-1.5 text-xs flex items-center justify-between font-semibold ${statusDisplay.colorClass}`}>
                    <span className="text-[11px] font-medium">Application Status:</span>
                    <span>{statusDisplay.label}</span>
                  </div>
                </div>

                {/* Bottom Sheet Card Component State Machine */}
                <div className="mt-auto">
                  {cardStep === "EXPLAIN" && caseData && (
                    <SudhaarCard
                      language={currentLanguage}
                      onLanguageChange={handleLanguageChange}
                      explanation={
                        caseData.cause_explanation ||
                        "Analyzing broken loan moment..."
                      }
                      actionLabel={caseData.action_label || "Fix this issue"}
                      visualData={caseData.visual_data}
                      onProposeAction={() => setCardStep("CONSENT")}
                      sourceMode={caseData.source_mode}
                    />
                  )}

                  {cardStep === "CONSENT" && caseData && (
                    <ConsentCard
                      actionName={caseData.proposed_action || "retry_mandate"}
                      targetAccount={caseData.action_params?.bank_name}
                      whatItDoes={
                        activePersonaId === "asha"
                          ? "Initiate an expedited refund of ₹4,500 to ICICI account ending 7810 and request official No-Dues Certificate (NOC)."
                          : activePersonaId === "sunita"
                          ? "Send a secure 72-hour direct video KYC resume link to your verified mobile ending 3210."
                          : "Set up auto-debit on your State Bank of India account ending 4521 for monthly EMI."
                      }
                      whatItDoesNotDo={
                        activePersonaId === "asha"
                          ? "Will not reopen your loan or negatively affect your CIBIL score."
                          : activePersonaId === "sunita"
                          ? "Does not require re-uploading documents already verified."
                          : "Will not deduct money right now. No setup fee is charged."
                      }
                      howToUndo={
                        activePersonaId === "asha"
                          ? "You can track ticket resolution in 24x7 Help section."
                          : activePersonaId === "sunita"
                          ? "You can also resume directly from your loan dashboard."
                          : "You can modify or cancel this mandate anytime in the app or via netbanking."
                      }
                      onConfirm={handleConfirmConsent}
                      onDecline={handleDeclineConsent}
                      isProcessing={isProcessing}
                    />
                  )}

                  {cardStep === "RECEIPT" && caseData?.receipt && (
                    <ReceiptCard
                      receipt={caseData.receipt}
                      onContinue={() => setCardStep("EXPLAIN")}
                    />
                  )}
                </div>
              </div>
            )}
          </PhoneFrame>
        </div>

        {/* Right Side: Operator Console taking remaining width (min-w-0, overflow-hidden) */}
        <div className="flex-1 min-w-0 h-full min-h-0 overflow-hidden flex flex-col">
          <LiveTrace
            auditTrail={caseData?.audit_trail || []}
            activeCaseId={caseData?.case_id}
            sourceMode={caseData?.source_mode}
          />
        </div>
      </main>
    </div>
  );
}
