from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class EventPayload(BaseModel):
    model_config = {"extra": "allow"}
    code: str
    attempt: Optional[int] = 1
    bank_account_masked: Optional[str] = None
    account_id: Optional[str] = None
    loan_id: Optional[str] = None
    debit_amount: Optional[float] = None
    debit_date: Optional[str] = None
    approved_amount: Optional[float] = None
    disbursed_amount: Optional[float] = None
    disconnect_reason: Optional[str] = None
    language: Optional[str] = None
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EventRequest(BaseModel):
    event_id: str
    event_type: str
    customer_id: str
    timestamp: str
    payload: EventPayload

class ConsentRequest(BaseModel):
    case_id: str
    action: str
    consent_given: bool
    selected_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None

class AskRequest(BaseModel):
    case_id: str
    question: str

class AuditEntryModel(BaseModel):
    entry_id: str
    case_id: str
    timestamp: str
    stage: str
    layer: str
    is_ai: bool
    idempotency_key: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class CaseResponse(BaseModel):
    case_id: str
    customer_id: str
    persona_id: str
    status: str
    moment: str
    language: str
    facts: Dict[str, Any]
    cause_explanation: Optional[str] = None
    proposed_action: Optional[str] = None
    action_label: Optional[str] = None
    action_params: Optional[Dict[str, Any]] = None
    allowed_actions: List[str] = Field(default_factory=list)
    visual_data: Optional[Dict[str, Any]] = None
    source_mode: str = "template"
    receipt: Optional[Dict[str, Any]] = None
    audit_trail: List[AuditEntryModel] = Field(default_factory=list)

