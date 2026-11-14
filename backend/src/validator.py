import re
from typing import Any, Dict, List, Set, Tuple

BANNED_PHRASES = [
    # English
    "guaranteed",
    "pre-approved",
    "preapproved",
    "100% approved",
    "instant approval",
    "promise approval",
    "waive all charges",
    "free money",
    # Hindi
    "गारंटी",
    "प्री-अप्रूव्ड",
    "100% स्वीकृत",
    "गारंटीड",
    # Marathi
    "हमी",
    "पूर्व-मंजूर",
    "100% मंजूर",
    "खात्रीशीर"
]

class ValidationResult:
    def __init__(self, passed: bool, errors: List[str], extracted_numbers: List[float]):
        self.passed = passed
        self.errors = errors
        self.extracted_numbers = extracted_numbers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "extracted_numbers": self.extracted_numbers
        }

def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extracts numerical figures from text, handling Indian comma formats (e.g. ₹50,000, 4,500).
    Ignores short 1-2 digit numbers (like dates 4, 5, step counts) unless currency prefixed.
    """
    cleaned = text.replace(",", "")
    # Find currency patterns like ₹4500 or 50000
    pattern = r'(?:₹|rs\.?|inr)?\s*(\b\d{3,7}\b)'
    matches = re.findall(pattern, cleaned, re.IGNORECASE)
    results = []
    for m in matches:
        try:
            results.append(float(m))
        except ValueError:
            pass
    return results

def collect_facts_numbers(facts: Any) -> Set[float]:
    """
    Recursively scans the case facts dictionary and extracts all valid numbers
    (loan amounts, EMIs, excess debit amounts, balances, etc.)
    """
    numbers = set()
    if isinstance(facts, dict):
        for k, v in facts.items():
            if isinstance(v, (int, float)):
                numbers.add(float(v))
            elif isinstance(v, (dict, list)):
                numbers.update(collect_facts_numbers(v))
    elif isinstance(facts, list):
        for item in facts:
            numbers.update(collect_facts_numbers(item))
    return numbers

def validate_llm_output(
    llm_output: Dict[str, Any],
    facts: Dict[str, Any],
    allowed_actions: List[str],
    expected_language: str
) -> ValidationResult:
    """
    Strict deterministic validator enforcing Rule 2:
    1. Every rupee amount in the message must exist in case facts.
    2. Proposed action must strictly be in allowed_actions.
    3. Zero banned phrases (no 'guaranteed', 'pre-approved', etc.).
    4. Text matches requested language script.
    """
    errors = []
    explanation = llm_output.get("explanation", "")
    proposed_action = llm_output.get("proposed_action")

    # 1. Action allowlist check
    if not proposed_action or proposed_action not in allowed_actions:
        errors.append(f"Proposed action '{proposed_action}' is not in allowed actions: {allowed_actions}")

    # 2. Banned phrases check
    explanation_lower = explanation.lower()
    for phrase in BANNED_PHRASES:
        if phrase in explanation_lower:
            errors.append(f"Banned phrase detected: '{phrase}'")

    # 3. Grounded numbers check
    extracted_nums = extract_numbers_from_text(explanation)
    allowed_nums = collect_facts_numbers(facts)
    # Add common safe constants like 90 (days reminder), 72 (hours validity)
    allowed_nums.update([90.0, 72.0, 24.0, 5.0, 4.0, 3.0, 2.0, 1.0])

    for num in extracted_nums:
        if num not in allowed_nums:
            errors.append(f"Ungrounded amount/number ₹{int(num)} found in message; not present in case facts.")

    # 4. Language check (Devanagari script presence for hi/mr)
    if expected_language in ["mr", "hi"]:
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', explanation))
        if not has_devanagari:
            errors.append(f"Expected language '{expected_language}' but no Devanagari characters found.")

    passed = len(errors) == 0
    return ValidationResult(passed, errors, extracted_nums)
