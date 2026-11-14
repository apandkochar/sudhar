const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export interface AuditEntry {
  entry_id: string;
  case_id: string;
  timestamp: string;
  stage: string;
  layer: string;
  is_ai: boolean;
  idempotency_key?: string | null;
  details: Record<string, any>;
}

export interface CaseData {
  case_id: string;
  customer_id: string;
  persona_id: string;
  status: string;
  moment: string;
  language: string;
  facts: Record<string, any>;
  playbook_id?: string;
  cause_explanation?: string;
  proposed_action?: string;
  action_label?: string;
  action_params?: Record<string, any>;
  allowed_actions: string[];
  visual_data?: Record<string, any>;
  source_mode: string;
  receipt?: Record<string, any> | null;
  audit_trail: AuditEntry[];
}

export async function sendEvent(eventPayload: {
  event_id: string;
  event_type: string;
  customer_id: string;
  timestamp: string;
  payload: Record<string, any>;
}): Promise<CaseData> {
  const res = await fetch(`${API_BASE}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(eventPayload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to trigger event");
  }
  return res.json();
}

export async function getCaseDetails(caseId: string): Promise<CaseData> {
  const res = await fetch(`${API_BASE}/cases/${caseId}`);
  if (!res.ok) {
    throw new Error("Failed to fetch case");
  }
  return res.json();
}

export async function sendConsent(payload: {
  case_id: string;
  action: string;
  consent_given: boolean;
  selected_params?: Record<string, any>;
  idempotency_key?: string;
}): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE}/consent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to submit consent");
  }
  return res.json();
}

export async function resetDatabase(): Promise<void> {
  await fetch(`${API_BASE}/scenarios/reset`, { method: "POST" });
}

export interface AuditStats {
  status: string;
  persistent: boolean;
  storage: string;
  db_path: string;
  integrity: string;
  total_cases: number;
  total_audit_entries: number;
  executed_rescues: number;
}

export async function fetchAuditStats(): Promise<AuditStats> {
  const res = await fetch(`${API_BASE}/audit/stats`);
  if (!res.ok) {
    throw new Error("Failed to fetch audit stats");
  }
  return res.json();
}

export interface CaseSummary {
  case_id: string;
  customer_id: string;
  persona_id: string;
  status: string;
  moment: string;
  source_mode: string;
  created_at: string;
  updated_at: string;
}

export async function fetchRecentCases(): Promise<CaseSummary[]> {
  const res = await fetch(`${API_BASE}/cases`);
  if (!res.ok) {
    throw new Error("Failed to fetch recent cases");
  }
  return res.json();
}

