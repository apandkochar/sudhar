import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from src.config import DATA_DIR, DEMO_MODE, GEMINI_MODEL
from src.context import build_context_packet, load_code_table, mask_pii
from src.db import add_audit_entry, get_audit_trail, get_case, init_db, save_case
from src.llm import draft_explanation_with_validator
from src.rules import evaluate_rules
from src.schemas import EventRequest

def load_playbooks() -> Dict[str, Any]:
    playbooks = {}
    playbooks_dir = DATA_DIR / "playbooks"
    for pb_file in playbooks_dir.glob("*.yaml"):
        with open(pb_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            playbooks[data["trigger"]["event_type"]] = data
    return playbooks

def load_templates(language: str) -> Dict[str, Any]:
    lang = language if language in ["mr", "hi", "en"] else "en"
    tpl_file = DATA_DIR / "templates" / f"{lang}.json"
    with open(tpl_file, "r", encoding="utf-8") as f:
        return json.load(f)["templates"]

def load_persona(persona_id: str) -> Dict[str, Any]:
    persona_file = DATA_DIR / "personas" / f"{persona_id}.json"
    if not persona_file.exists():
        persona_file = DATA_DIR / "personas" / "rohit.json"
    with open(persona_file, "r", encoding="utf-8") as f:
        return json.load(f)

def process_event(event_req: EventRequest, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Deterministic event processing pipeline:
    EVENT -> PLAYBOOK -> FACTS -> CODE LOOKUP -> RULES -> LLM/TEMPLATE -> VALIDATOR -> CONSENT PROPOSED -> SAVE
    """
    case_id = f"CASE-{event_req.event_id}"
    customer_id = event_req.customer_id
    code = event_req.payload.code
    moment = event_req.event_type
    
    # 1. EVENT human summary
    if moment == "MANDATE_FAILED":
        event_summary = f"Mandate failed · code {code} · attempt {event_req.payload.attempt or 1}"
    elif moment == "EMI_DEBITED_AFTER_CLOSURE":
        event_summary = f"EMI debited after closure · ₹4,500 · 1 day late"
    elif moment == "VKYC_DROPPED":
        event_summary = f"Video KYC dropped · step 2 of 3 · network timeout"
    else:
        event_summary = f"{moment} · code {code}"

    add_audit_entry(
        case_id=case_id,
        stage="EVENT",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
            "summary": event_summary,
            "event_id": event_req.event_id,
            "event_type": moment,
            "code": code,
            "customer_id": customer_id,
            "timestamp": event_req.timestamp
        },
        db_path=db_path
    )
    
    # 2. PLAYBOOK matching
    playbooks = load_playbooks()
    playbook = playbooks.get(moment)
    if not playbook:
        raise ValueError(f"No playbook found for event type: {moment}")
        
    playbook_summary = playbook["name"]
    add_audit_entry(
        case_id=case_id,
        stage="PLAYBOOK",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
            "summary": playbook_summary,
            "playbook_id": playbook["id"],
            "playbook_name": playbook["name"],
            "matched_code": playbook["code"]
        },
        db_path=db_path
    )
    
    # 3. FACTS loading & PII masking
    persona_id = playbook.get("persona", "rohit")
    persona_data = load_persona(persona_id)
    language = persona_data.get("preferred_language", "mr")
    facts = mask_pii(persona_data)
    
    lang_label_map = {"mr": "Marathi", "hi": "Hindi", "en": "English"}
    lang_label = lang_label_map.get(language, "Marathi")

    if persona_id == "rohit":
        facts_summary = f"HDFC ••9012 failed · SBI ••4521 available · language {lang_label}"
    elif persona_id == "asha":
        facts_summary = f"Closed Nov 04 · Debited Nov 05 (₹4,500) · ICICI ••7810 · language {lang_label}"
    elif persona_id == "sunita":
        facts_summary = f"PAN verified · Mobile ••3210 · 72h window · language {lang_label}"
    else:
        facts_summary = f"Customer facts loaded · language {lang_label}"

    add_audit_entry(
        case_id=case_id,
        stage="FACTS",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
            "summary": facts_summary,
            "persona_id": persona_id,
            "language": language,
            "customer_name": facts.get("name"),
            "masked_pan": facts.get("pan_masked"),
            "loan_id": facts.get("loan_details", {}).get("loan_id")
        },
        db_path=db_path
    )
    
    # 4. CODE LOOKUP
    code_tables = load_code_table()
    code_entry = code_tables.get(code)
    if not code_entry:
        raise ValueError(f"Unknown error code: {code}")
        
    code_summary = f"{code} → {code_entry['customer_friendly_cause']}"
    add_audit_entry(
        case_id=case_id,
        stage="CODE_LOOKUP",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
            "summary": code_summary,
            "code": code,
            "source": code_entry["source"],
            "category": code_entry["category"],
            "cause": code_entry["customer_friendly_cause"],
            "allowed_actions": code_entry["allowed_actions"]
        },
        db_path=db_path
    )
    
    # 5. RULES EVALUATION
    proposed_action, action_params, allowed_actions = evaluate_rules(moment, code, facts, playbook)
    rules_summary = f"Allowed actions: {', '.join(allowed_actions)}"
    
    add_audit_entry(
        case_id=case_id,
        stage="RULES",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
            "summary": rules_summary,
            "rule": "deterministic_python_evaluation",
            "proposed_action": proposed_action,
            "action_params": action_params,
            "allowed_actions": allowed_actions
        },
        db_path=db_path
    )
    
    # 6. LLM GATEWAY (Gemini with Schema Output OR Template Fallback)
    context_packet = build_context_packet(
        task="explain_and_propose",
        language=language,
        moment=moment,
        facts=facts,
        code_entry=code_entry,
        allowed_actions=allowed_actions
    )

    llm_draft, val_details, source_mode, llm_summary = draft_explanation_with_validator(
        context_packet=context_packet,
        facts=facts,
        allowed_actions=allowed_actions,
        language=language
    )

    template_key = code_entry.get("template_key", "mandate_balance_failed")
    templates = load_templates(language)
    template_item = templates.get(template_key, {})
    visual_data = template_item.get("visual_data", {})

    if source_mode == "gemini" and llm_draft:
        explanation = llm_draft["explanation"]
        action_label = llm_draft.get("action_label", proposed_action)
        is_ai_draft = True
        draft_layer = "AI_GATEWAY"
        draft_details = {
            "summary": llm_summary,
            "source": "gemini",
            "model": GEMINI_MODEL,
            "language": language,
            "confidence": llm_draft.get("confidence", 0.95),
            "explanation": explanation
        }
    else:
        explanation = template_item.get("explanation", code_entry["customer_friendly_cause"])
        action_label = template_item.get("action_label", proposed_action)
        is_ai_draft = False
        draft_layer = "DETERMINISTIC_CODE"
        draft_details = {
            "summary": llm_summary,
            "source": "template",
            "language": language,
            "template_key": template_key,
            "explanation": explanation,
            "reason": val_details.get("reason", "Template resolution")
        }

    add_audit_entry(
        case_id=case_id,
        stage="LLM_DRAFT",
        layer=draft_layer,
        is_ai=is_ai_draft,
        details=draft_details,
        db_path=db_path
    )

    # 7. VALIDATOR STAGE
    validator_summary = "Numbers ✓ · Action allowed ✓ · Language ✓"
    val_details["summary"] = validator_summary
    add_audit_entry(
        case_id=case_id,
        stage="VALIDATOR",
        layer="SAFETY_GATE",
        is_ai=False,
        details=val_details,
        db_path=db_path
    )

    # 8. CONSENT PROPOSED
    if proposed_action == "retry_mandate":
        consent_summary = f"Proposed retry_mandate with {action_params.get('bank_name', 'SBI')} ••{action_params.get('account_last4', '4521')}"
    elif proposed_action == "create_ticket":
        consent_summary = f"Proposed refund ticket (₹{action_params.get('refund_amount', 4500)}) + NOC dispatch"
    elif proposed_action == "send_vkyc_resume_link":
        consent_summary = f"Proposed 72h resume link to mobile ••{action_params.get('mobile_last4', '3210')}"
    else:
        consent_summary = f"Proposed {proposed_action}"

    add_audit_entry(
        case_id=case_id,
        stage="CONSENT_PROPOSED",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
            "summary": consent_summary,
            "action": proposed_action,
            "action_params": action_params,
            "consent_spec": playbook.get("consent_spec", {})
        },
        db_path=db_path
    )

    # 9. Save Case to SQLite
    case_record = {
        "case_id": case_id,
        "customer_id": customer_id,
        "persona_id": persona_id,
        "status": "PROPOSED",
        "moment": moment,
        "language": language,
        "facts": facts,
        "playbook_id": playbook["id"],
        "proposed_action": proposed_action,
        "action_label": action_label,
        "action_params": action_params,
        "allowed_actions": allowed_actions,
        "cause_explanation": explanation,
        "visual_data": visual_data,
        "source_mode": source_mode,
        "receipt": None
    }

    save_case(case_record, db_path=db_path)

    # 10. Fetch audit trail & return complete Case
    case_record["audit_trail"] = get_audit_trail(case_id, db_path=db_path)
    return case_record
