import re
from typing import Any, Dict, List, Optional, Set, Tuple

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

DEVANAGARI_DIGITS_MAP = str.maketrans("०१२३४५६७८९", "0123456789")

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

def normalize_text_for_validation(text: str) -> str:
    """
    Normalizes text for financial safety validation:
    1. Normalizes Devanagari digits (०-९ -> 0-9).
    2. Normalizes Indian number formats (e.g. ₹50,000 -> 50000, 4,500 -> 4500).
    """
    # 1. Translate Devanagari digits
    normalized = text.translate(DEVANAGARI_DIGITS_MAP)
    # 2. Remove commas inside numbers (Indian format 1,50,000 or Western 50,000)
    normalized = re.sub(r'(?<=\d),(?=\d)', '', normalized)
    return normalized

def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extracts numerical figures from normalized text.
    Handles currency prefixes (₹, rs, inr) and stand-alone numbers (3+ digits or currency-prefixed).
    """
    norm = normalize_text_for_validation(text)
    # Find currency patterns like ₹4500 or plain 4500, 50000
    pattern = r'(?:₹|rs\.?|inr)?\s*(\b\d{2,7}\b)'
    matches = re.findall(pattern, norm, re.IGNORECASE)
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
    (loan amounts, EMIs, excess debit amounts, balances, account last4s, etc.)
    """
    numbers = set()
    if isinstance(facts, dict):
        for k, v in facts.items():
            if isinstance(v, (int, float)):
                numbers.add(float(v))
            elif isinstance(v, str) and v.isdigit():
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
    expected_language: str,
    action_params: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Strict deterministic validator enforcing Rule 2:
    1. Every rupee amount / figure in the message must exist in case facts.
    2. Proposed action must strictly be in allowed_actions.
    3. Zero banned phrases (no 'guaranteed', 'pre-approved', etc.).
    4. Required target account last4 mentioned verbatim if retry_mandate with action_params.
    5. Text matches requested language script (Devanagari for mr/hi).
    """
    errors = []
    raw_explanation = llm_output.get("explanation", "")
    proposed_action = llm_output.get("proposed_action")

    # Normalize text (Devanagari numerals -> Western digits, strip commas)
    norm_explanation = normalize_text_for_validation(raw_explanation)

    # 1. Action allowlist check
    if not proposed_action or proposed_action not in allowed_actions:
        errors.append(f"Proposed action '{proposed_action}' is not in allowed actions: {allowed_actions}")

    # 2. Banned phrases check
    raw_lower = raw_explanation.lower()
    for phrase in BANNED_PHRASES:
        if phrase in raw_lower:
            errors.append(f"Banned phrase detected: '{phrase}'")

    # 3. Required entities check: if mandate retry with secondary account, verify account last4 is mentioned
    target_account_last4 = None
    if action_params and "account_last4" in action_params:
        target_account_last4 = str(action_params["account_last4"])

    if target_account_last4 and target_account_last4 not in norm_explanation:
        errors.append(f"account {target_account_last4} missing")

    # 4. Grounded numbers check
    extracted_nums = extract_numbers_from_text(raw_explanation)
    allowed_nums = collect_facts_numbers(facts)
    # Add common safe constants like 90 (days reminder), 72 (hours validity), 24, dates 1-31
    allowed_nums.update([float(x) for x in range(1, 32)])
    allowed_nums.update([90.0, 72.0, 48.0, 24.0, 100.0])
    if target_account_last4 and target_account_last4.isdigit():
        allowed_nums.add(float(target_account_last4))

    for num in extracted_nums:
        if num not in allowed_nums:
            errors.append(f"Ungrounded amount ₹{int(num)} found in message; not present in case facts.")

    # 5. Language check (Devanagari script presence for hi/mr)
    if expected_language in ["mr", "hi"]:
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', raw_explanation))
        if not has_devanagari:
            errors.append(f"Expected language '{expected_language}' but no Devanagari characters found.")

    passed = len(errors) == 0
    return ValidationResult(passed, errors, extracted_nums)
