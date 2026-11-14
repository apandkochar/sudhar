"use client";

import React, { useState, useEffect } from "react";
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
      timestamp: new Date().toISOString(),
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
      customer_id: "CUST-ASHA-802",
      timestamp: new Date().toISOString(),
      payload: {
        code: "LMS_POST_CLOSURE_DEBIT",
        loan_id: "LN-ASHA-150K",
        debit_amount: 4500,
        debit_date: "2026-11-05",
        bank_account_masked: "ICICI Bank ending 7810"
      }
    }
  },
  sunita: {
    name: "Sunita Deshmukh",
    city: "Nashik",
    preferred_language: "mr",
    loan_amount: 75000,
    event: {
      event_id: "EVT-SUNITA-DEMO-01",
      event_type: "VKYC_DROPPED",
      customer_id: "CUST-SUNITA-103",
      timestamp: new Date().toISOString(),
      payload: {
        code: "VKYC_NET_DROP",
        application_id: "APP-SUNITA-75K",
        attempt: 1,
        disconnect_reason: "SOCKET_TIMEOUT"
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
  const [rescuesCount, setRescuesCount] = useState<number>(0);

  // Trigger event when active persona changes
  useEffect(() => {
    handleTriggerScenario(activePersonaId);
  }, [activePersonaId]);

  const handleTriggerScenario = async (personaId: string) => {
    const config = PERSONAS_CONFIG[personaId];
    if (!config) return;

    setCurrentLanguage(config.preferred_language);
    setCardStep("EXPLAIN");
    setIsProcessing(true);

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

  const handleConfirmConsent = async () => {
    if (!caseData || !caseData.proposed_action) return;
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
      setRescuesCount((prev) => prev + 1);
    } catch (err) {
      console.error("Consent confirmation failed:", err);
      alert("Action execution failed: " + err);
    } finally {
      setIsProcessing(false);
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

  const handleReset = async () => {
    try {
      await resetDatabase();
      setRescuesCount(0);
      handleTriggerScenario(activePersonaId);
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
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Scenario & Mode Bar */}
      <ScenarioBar
        onSelectPersona={(id) => {
          setActivePersonaId(id);
          setIsBeforeMode(false);
        }}
        activePersonaId={activePersonaId}
        isBeforeMode={isBeforeMode}
        onToggleBeforeMode={setIsBeforeMode}
        onReset={handleReset}
        rescuesCount={rescuesCount}
      />

      {/* Main Dual View Area (Phone Left, Console Right) - Fits at 1280x800 */}
      <div className="flex-1 flex flex-row items-center justify-center p-3 lg:p-6 gap-6 overflow-hidden max-w-7xl mx-auto w-full">
        {/* Left Side: 390px Mobile Phone */}
        <div className="flex-shrink-0">
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

            {/* Screen Content: Before vs After */}
            {isBeforeMode ? (
              <BeforeScreen onSwitchToSudhaar={() => setIsBeforeMode(false)} />
            ) : (
              <div className="flex-1 flex flex-col justify-between bg-slate-100/70">
                {/* Background Context */}
                <div className="p-3 space-y-2.5">
                  <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500 font-medium">Applicant</span>
                      <span className="font-bold text-slate-800">
                        {caseData?.facts?.name || PERSONAS_CONFIG[activePersonaId].name}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs mt-1">
                      <span className="text-slate-500 font-medium">Lender</span>
                      <span className="font-semibold text-[#002970]">Nimbus Finance</span>
                    </div>
                    <div className="flex justify-between items-center text-xs mt-1">
                      <span className="text-slate-500 font-medium">Loan Amount</span>
                      <span className="font-bold text-slate-900">
                        ₹{(caseData?.facts?.loan_details?.loan_amount || PERSONAS_CONFIG[activePersonaId].loan_amount).toLocaleString("en-IN")}
                      </span>
                    </div>
                  </div>

                  {/* Customer Friendly Status (Requirement 4) */}
                  <div className={`border rounded-xl px-3 py-2 text-xs flex items-center justify-between font-semibold ${statusDisplay.colorClass}`}>
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

        {/* Right Side: Operator Console with Live Trace (Fits at 1280x800) */}
        <div className="flex-1 w-full h-[810px] flex flex-col">
          <LiveTrace
            auditTrail={caseData?.audit_trail || []}
            activeCaseId={caseData?.case_id}
            sourceMode={caseData?.source_mode}
          />
        </div>
      </div>
    </div>
  );
}
