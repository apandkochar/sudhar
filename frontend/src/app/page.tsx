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
  },
  meena: {
    name: "Meena Jadhav",
    city: "Pune",
    preferred_language: "mr",
    loan_amount: 100000,
    event: {
      event_id: "EVT-MEENA-DEMO-01",
      event_type: "DISBURSAL_CREDITED",
      customer_id: "CUST-MEENA-501",
      timestamp: "2026-11-15T09:00:00Z",
      payload: {
        code: "LMS_DISBURSAL_BREAKUP",
        loan_id: "LN-MEENA-100K",
        approved_amount: 100000,
        disbursed_amount: 96045,
        bank_account_masked: "Bank of Maharashtra ending 4412"
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

  const getDeterministicRows = (personaId: string, lang: string): AuditEntry[] => {
    const langNames: Record<string, string> = { mr: "Marathi", hi: "Hindi", en: "English" };
    const langName = langNames[lang] || "Marathi";
    const nowIso = new Date().toISOString();

    if (personaId === "meena") {
      return [
        {
          entry_id: "AUD-DET-01",
          case_id: "CASE-EVT-MEENA-DEMO-01",
          stage: "EVENT",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Disbursal credited · ₹96,045 of ₹1,00,000 · deductions query",
            event_type: "DISBURSAL_CREDITED",
            code: "LMS_DISBURSAL_BREAKUP"
          }
        },
        {
          entry_id: "AUD-DET-02",
          case_id: "CASE-EVT-MEENA-DEMO-01",
          stage: "PLAYBOOK",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Loan Disbursal Deduction Breakup & Transparency",
            playbook_name: "Loan Disbursal Deduction Breakup & Transparency"
          }
        },
        {
          entry_id: "AUD-DET-03",
          case_id: "CASE-EVT-MEENA-DEMO-01",
          stage: "FACTS",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: `Approved ₹1,00,000 · Disbursed ₹96,045 · Fee ₹2,000 · GST ₹360 · Broken Int ₹395 · Ins ₹1,200 · language ${langName}`,
            language: langName
          }
        },
        {
          entry_id: "AUD-DET-04",
          case_id: "CASE-EVT-MEENA-DEMO-01",
          stage: "CODE_LOOKUP",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "LMS_DISBURSAL_BREAKUP → Approved ₹1,00,000 disbursed as ₹96,045",
            code: "LMS_DISBURSAL_BREAKUP"
          }
        },
        {
          entry_id: "AUD-DET-05",
          case_id: "CASE-EVT-MEENA-DEMO-01",
          stage: "RULES",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Allowed actions: send_breakup_and_documents, raise_insurance_cancellation_request, book_callback",
            allowed_actions: ["send_breakup_and_documents", "raise_insurance_cancellation_request", "book_callback"]
          }
        }
      ];
    }

    if (personaId === "asha") {
      return [
        {
          entry_id: "AUD-DET-01",
          case_id: "CASE-EVT-ASHA-DEMO-01",
          stage: "EVENT",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "EMI debited after closure · ₹4,500 · 1 day late",
            event_type: "EMI_DEBITED_AFTER_CLOSURE",
            code: "LMS_POST_CLOSURE_DEBIT"
          }
        },
        {
          entry_id: "AUD-DET-02",
          case_id: "CASE-EVT-ASHA-DEMO-01",
          stage: "PLAYBOOK",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Post-Closure Erroneous EMI Debit Rescue",
            playbook_name: "Post-Closure Erroneous EMI Debit Rescue"
          }
        },
        {
          entry_id: "AUD-DET-03",
          case_id: "CASE-EVT-ASHA-DEMO-01",
          stage: "FACTS",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: `Loan closed 04 Nov · Debited 05 Nov · ₹4,500 excess · language ${langName}`,
            language: langName
          }
        },
        {
          entry_id: "AUD-DET-04",
          case_id: "CASE-EVT-ASHA-DEMO-01",
          stage: "CODE_LOOKUP",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "LMS_POST_CLOSURE_DEBIT → debit queued before settlement file sync",
            code: "LMS_POST_CLOSURE_DEBIT"
          }
        },
        {
          entry_id: "AUD-DET-05",
          case_id: "CASE-EVT-ASHA-DEMO-01",
          stage: "RULES",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Allowed actions: create_ticket, request_noc, request_bureau_correction",
            allowed_actions: ["create_ticket", "request_noc", "request_bureau_correction"]
          }
        }
      ];
    } else if (personaId === "sunita") {
      return [
        {
          entry_id: "AUD-DET-01",
          case_id: "CASE-EVT-SUNITA-DEMO-01",
          stage: "EVENT",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Video KYC session disconnected · 72h window",
            event_type: "VKYC_DROPPED",
            code: "VKYC_NET_DROP"
          }
        },
        {
          entry_id: "AUD-DET-02",
          case_id: "CASE-EVT-SUNITA-DEMO-01",
          stage: "PLAYBOOK",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Video KYC Interrupted Call Resume Playbook",
            playbook_name: "Video KYC Interrupted Call Resume Playbook"
          }
        },
        {
          entry_id: "AUD-DET-03",
          case_id: "CASE-EVT-SUNITA-DEMO-01",
          stage: "FACTS",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: `PAN verified ✓ · Bandwidth drop · language ${langName}`,
            language: langName
          }
        },
        {
          entry_id: "AUD-DET-04",
          case_id: "CASE-EVT-SUNITA-DEMO-01",
          stage: "CODE_LOOKUP",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "VKYC_NET_DROP → bandwidth drop below 100kbps threshold",
            code: "VKYC_NET_DROP"
          }
        },
        {
          entry_id: "AUD-DET-05",
          case_id: "CASE-EVT-SUNITA-DEMO-01",
          stage: "RULES",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Allowed actions: send_vkyc_resume_link, book_callback",
            allowed_actions: ["send_vkyc_resume_link", "book_callback"]
          }
        }
      ];
    } else {
      return [
        {
          entry_id: "AUD-DET-01",
          case_id: "CASE-EVT-ROHIT-DEMO-01",
          stage: "EVENT",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Mandate failed · code AP15 · attempt 1",
            code: "AP15",
            event_type: "MANDATE_FAILED"
          }
        },
        {
          entry_id: "AUD-DET-02",
          case_id: "CASE-EVT-ROHIT-DEMO-01",
          stage: "PLAYBOOK",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Mandate retry playbook",
            playbook_name: "Mandate retry playbook"
          }
        },
        {
          entry_id: "AUD-DET-03",
          case_id: "CASE-EVT-ROHIT-DEMO-01",
          stage: "FACTS",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: `HDFC ••9012 failed · SBI ••4521 available · language ${langName}`,
            language: langName
          }
        },
        {
          entry_id: "AUD-DET-04",
          case_id: "CASE-EVT-ROHIT-DEMO-01",
          stage: "CODE_LOOKUP",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "AP15 → required balance not maintained",
            code: "AP15",
            cause: "required balance not maintained"
          }
        },
        {
          entry_id: "AUD-DET-05",
          case_id: "CASE-EVT-ROHIT-DEMO-01",
          stage: "RULES",
          layer: "DETERMINISTIC_CODE",
          is_ai: false,
          timestamp: nowIso,
          details: {
            summary: "Allowed actions: retry_mandate, book_callback",
            allowed_actions: ["retry_mandate", "book_callback"]
          }
        }
      ];
    }
  };

  const handleTriggerScenario = async (personaId: string) => {
    const config = PERSONAS_CONFIG[personaId];
    if (!config) return;

    setActivePersonaId(personaId);
    setCurrentLanguage(config.preferred_language);
    setCardStep("EXPLAIN");
    setIsProcessing(true);
    consentLockRef.current = false;

    // Requirement 3: Progressive trace - deterministic rows appear instantly
    const initialAudit = getDeterministicRows(personaId, config.preferred_language);
    setCaseData({
      case_id: `CASE-${config.event.event_id}`,
      customer_id: config.event.customer_id,
      persona_id: personaId,
      status: "PROPOSED",
      moment: config.event.event_type,
      language: config.preferred_language,
      facts: { name: config.name, loan_details: { loan_amount: config.loan_amount }, ...config.event.payload },
      playbook_id: personaId === "meena" ? "PB-DISBURSAL-BREAKUP-01" : personaId === "asha" ? "PB-POST-CLOSURE-01" : personaId === "sunita" ? "PB-VKYC-01" : "PB-MANDATE-01",
      proposed_action: personaId === "meena" ? "send_breakup_and_documents" : personaId === "asha" ? "create_ticket" : personaId === "sunita" ? "send_vkyc_resume_link" : "retry_mandate",
      action_label: personaId === "meena" ? "तपशील व कागदपत्रे पाठवा" : personaId === "asha" ? "रिफंड (₹4,500) और NOC का अनुरोध करें" : personaId === "sunita" ? "केवाईसी रिज्यूम लिंक भेजें" : "ई-मँडेट पुन्हा सेट करा",
      action_params: {},
      allowed_actions: [],
      cause_explanation: "",
      visual_data: undefined,
      source_mode: "gemini",
      audit_trail: initialAudit,
    });

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
    setIsProcessing(true);
    if (caseData) {
      // Instant progressive feedback with new language
      const updatedAudit = getDeterministicRows(activePersonaId, newLang);
      setCaseData((prev) => prev ? { ...prev, language: newLang, audit_trail: updatedAudit } : null);
      try {
        const config = PERSONAS_CONFIG[activePersonaId];
        const updated = await sendEvent({
          ...config.event,
          event_id: `${config.event.event_id}-${newLang}`,
          payload: {
            ...config.event.payload,
            language: newLang,
          }
        });
        setCaseData(updated);
      } catch (e) {
        console.error("Failed to reload language:", e);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  // Requirement 2: Consent must be sent ONLY from Confirm button's onClick. Guard against repeated calls.
  const handleConfirmConsent = async (chosenAction?: string) => {
    const actionToRun = chosenAction || caseData?.proposed_action;
    if (consentLockRef.current || !caseData || !actionToRun) return;
    consentLockRef.current = true;
    setIsProcessing(true);

    try {
      const res = await sendConsent({
        case_id: caseData.case_id,
        action: actionToRun,
        consent_given: true,
        selected_params: caseData.action_params || {},
        idempotency_key: `IDEMP-${caseData.case_id}-${actionToRun}`,
      });

      const updatedCase = await getCaseDetails(caseData.case_id);
      if (!updatedCase.receipt && res) {
        updatedCase.receipt = res;
      }
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

  // Requirement 6: Log voice playback into the operator console trace
  const handleVoiceLogged = (traceSummary: string, isAi: boolean) => {
    setCaseData((prev: any) => {
      if (!prev) return prev;
      const nowIso = new Date().toISOString();
      const existing = prev.audit_trail || [];
      const newEntry: AuditEntry = {
        entry_id: `AUD-VOICE-${Date.now()}`,
        case_id: prev.case_id,
        stage: "VOICE",
        layer: isAi ? "AI_MODEL" : "DETERMINISTIC_CODE",
        is_ai: isAi,
        timestamp: nowIso,
        details: {
          summary: traceSummary,
          source: isAi ? "sarvam" : "browser_fallback"
        }
      };
      return {
        ...prev,
        audit_trail: [...existing, newEntry]
      };
    });
  };

  // Requirement 4: Show "Failed – action needed" before consent and "Registered" after; never internal states like PROPOSED
  const getCustomerFriendlyStatus = () => {
    if (cardStep === "RECEIPT" || caseData?.status === "EXECUTED") {
      if (activePersonaId === "meena") {
        return {
          label: "Breakup & Docs Sent",
          colorClass: "bg-emerald-50 text-emerald-700 border-emerald-200"
        };
      }
      if (activePersonaId === "asha") {
        return {
          label: "3 requests raised",
          colorClass: "bg-emerald-50 text-emerald-700 border-emerald-200"
        };
      }
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
                  : activePersonaId === "meena"
                  ? "Loan Disbursal"
                  : "e-Mandate Setup"
              }
            />

            {/* Journey Stepper */}
            <Stepper
              currentStep={activePersonaId === "sunita" ? 2 : activePersonaId === "meena" ? 4 : 3}
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
                      isDrafting={isProcessing}
                      onVoiceLogged={handleVoiceLogged}
                    />
                  )}

                  {cardStep === "CONSENT" && caseData && (
                    <ConsentCard
                      actionName={caseData.proposed_action || "retry_mandate"}
                      targetAccount={caseData.action_params?.bank_name}
                      secondaryOption={
                        activePersonaId === "meena"
                          ? {
                              action: "raise_insurance_cancellation_request",
                              label: "Raise insurance cancellation request",
                              description: "Optional cover (₹1,200) · lender decides within 48-72h"
                            }
                          : undefined
                      }
                      whatItDoes={
                        activePersonaId === "meena"
                          ? "Send full itemized deduction statement and official loan sanction documents to your registered email and app inbox."
                          : activePersonaId === "asha"
                          ? "1. Raise ₹4,500 refund ticket for excess debit to ICICI Bank ending 7810 (SLA 3-5 days)\n2. Expedite official No-Dues Certificate (NOC) dispatch\n3. Schedule credit bureau record check to protect CIBIL score"
                          : activePersonaId === "sunita"
                          ? "Send a secure 72-hour direct video KYC resume link to your verified mobile ending 3210."
                          : "Set up auto-debit on your State Bank of India account ending 4521 for monthly EMI."
                      }
                      whatItDoesNotDo={
                        activePersonaId === "meena"
                          ? "Will not charge any additional fee or alter your approved EMI schedule."
                          : activePersonaId === "asha"
                          ? "Will not reopen your closed loan. Does not require visiting a branch or re-uploading documents."
                          : activePersonaId === "sunita"
                          ? "Does not require re-uploading documents already verified."
                          : "Will not deduct money right now. No setup fee is charged."
                      }
                      howToUndo={
                        activePersonaId === "meena"
                          ? "You can view or download loan documents anytime in your loan dashboard or 24x7 Help."
                          : activePersonaId === "asha"
                          ? "You can track refund status and NOC dispatch anytime in the 24x7 Help section."
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
            isDrafting={isProcessing}
          />
        </div>
      </main>
    </div>
  );
}
