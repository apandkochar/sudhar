import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import DATA_DIR

def load_code_table() -> Dict[str, Any]:
    with open(DATA_DIR / "code_tables.json", "r", encoding="utf-8") as f:
        return json.load(f)["codes"]

def mask_pii(data: Any) -> Any:
    """
    Recursively masks sensitive account numbers, PANs, and Aadhaar numbers.
    Preserves last 4 characters for customer recognition.
    """
    if isinstance(data, dict):
        masked_dict = {}
        for k, v in data.items():
            if "pan" in k.lower() and isinstance(v, str) and len(v) == 10:
                masked_dict[k] = f"XXXXX{v[-4:]}"
            elif "aadhaar" in k.lower() and isinstance(v, str) and len(v) >= 12:
                masked_dict[k] = f"XXXXXXXX{v[-4:]}"
            elif ("account" in k.lower() or "acc" in k.lower()) and isinstance(v, str) and len(v) > 4 and not v.startswith("ACC-"):
                masked_dict[k] = f"...{v[-4:]}"
            else:
                masked_dict[k] = mask_pii(v)
        return masked_dict
    elif isinstance(data, list):
        return [mask_pii(item) for item in data]
    return data

def build_context_packet(
    task: str,
    language: str,
    moment: str,
    facts: Dict[str, Any],
    code_entry: Dict[str, Any],
    allowed_actions: List[str]
) -> Dict[str, Any]:
    """
    Constructs the minimal, strictly PII-masked context packet for LLM rendering.
    """
    sanitized_facts = mask_pii(facts)
    
    cause_val = code_entry.get("customer_friendly_cause", code_entry.get("description"))
    if moment == "EMI_DEBITED_AFTER_CLOSURE":
        cause_val = "Debit occurred after confirmed loan closure date (unverified cause)."
    elif moment == "DISBURSAL_CREDITED":
        cause_val = "Scheduled upfront deductions as per loan terms."

    return {
        "task": task,
        "language": language,
        "moment": moment,
        "facts": sanitized_facts,
        "cause": cause_val,
        "recommended_fix": code_entry.get("recommended_fix"),
        "allowed_actions": allowed_actions,
        "must_not": [
            "promise approval or guarantee loan disbursal",
            "state amounts or dates not explicitly provided in facts",
            "perform any financial debit or charge fees"
        ],
        "max_words": 60,
        "output_schema": "SudhaarMessage_v1"
    }

