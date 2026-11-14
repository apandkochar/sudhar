import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from src.config import DATA_DIR, DEMO_MODE
from src.context import build_context_packet, load_code_table, mask_pii
from src.db import add_audit_entry, get_audit_trail, get_case, init_db, save_case
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
        # Fallback to rohit
        persona_file = DATA_DIR / "personas" / "rohit.json"
    with open(persona_file, "r", encoding="utf-8") as f:
        return json.load(f)

def process_event(event_req: EventRequest, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Deterministic event processing pipeline:
    EVENT -> PLAYBOOK -> FACTS -> CODE LOOKUP -> RULES -> TEMPLATE/LLM -> VALIDATOR -> CONSENT PROPOSED -> SAVE
    """
    case_id = f"CASE-{event_req.event_id}"
    customer_id = event_req.customer_id
    code = event_req.payload.code
    moment = event_req.event_type
    
    # 1. EVENT audit
    add_audit_entry(
        case_id=case_id,
        stage="EVENT",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
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
        
    add_audit_entry(
        case_id=case_id,
        stage="PLAYBOOK",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
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
    
    add_audit_entry(
        case_id=case_id,
        stage="FACTS",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
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
        
    add_audit_entry(
        case_id=case_id,
        stage="CODE_LOOKUP",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
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
    
    add_audit_entry(
        case_id=case_id,
        stage="RULES",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
            "rule": "deterministic_python_evaluation",
            "proposed_action": proposed_action,
            "action_params": action_params,
            "allowed_actions": allowed_actions
        },
        db_path=db_path
    )
    
    # 6. TEMPLATE RESOLUTION (Phase 2 uses approved templates; Phase 4 will call Gemini if LIVE)
    template_key = code_entry.get("template_key", "mandate_balance_failed")
    templates = load_templates(language)
    template_item = templates.get(template_key)
    
    explanation = template_item["explanation"] if template_item else code_entry["customer_friendly_cause"]
    action_label = template_item["action_label"] if template_item else proposed_action
    visual_data = template_item.get("visual_data", {}) if template_item else {}
    source_mode = "template"
    
    add_audit_entry(
        case_id=case_id,
        stage="LLM_DRAFT",
        layer="DETERMINISTIC_CODE", # In Phase 2 template mode
        is_ai=False,
        details={
            "source": source_mode,
            "language": language,
            "template_key": template_key,
            "explanation": explanation
        },
        db_path=db_path
    )
    
    # 7. VALIDATOR
    # Ensure proposed action is in allowed actions
    is_valid = proposed_action in allowed_actions
    add_audit_entry(
        case_id=case_id,
        stage="VALIDATOR",
        layer="SAFETY_GATE",
        is_ai=False,
        details={
            "passed": is_valid,
            "allowed_actions_checked": allowed_actions,
            "proposed_action_checked": proposed_action,
            "banned_phrases_found": []
        },
        db_path=db_path
    )
    
    # 8. CONSENT PROPOSED
    add_audit_entry(
        case_id=case_id,
        stage="CONSENT_PROPOSED",
        layer="DETERMINISTIC_CODE",
        is_ai=False,
        details={
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

