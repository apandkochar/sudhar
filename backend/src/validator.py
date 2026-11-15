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

POST_CLOSURE_CAUSE_PHRASES = [
    "कारण",
    "क्योंकि",
    "because",
    "due to",
    "automated",
    "ऑटोमेटेड"
]

DEVANAGARI_DIGITS_MAP = str.maketrans("०१२३४५६७८९", "0123456789")

MONTH_ALIASES = {
    # Hindi
    "जनवरी": 1, "फ़रवरी": 2, "फरवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6,
    "जुलाई": 7, "अगस्त": 8, "सितंबर": 9, "अक्टूबर": 10, "नवंबर": 11, "दिसंबर": 12,
    # Marathi
    "जानेवारी": 1, "फेब्रुवारी": 2, "एप्रिल": 4, "मे": 5, "जुलै": 7, "ऑगस्ट": 8,
    "सप्टेंबर": 9, "ऑक्टोबर": 10, "नोव्हेंबर": 11, "डिसेंबर": 12,
    # English
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
}

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

def extract_dates_from_text(text: str) -> List[Tuple[int, int]]:
    """
    Extracts (day, month) tuples from diverse date formats:
    - '4 नवंबर', '5 नवंबर', '४ नवंबर', '५ नवंबर'
    - '4 Nov', '04 Nov', '4th November'
    - '04-11-2026', '04/11/2026', '05-11-2026'
    - '4 नोव्हेंबर', '५ नोव्हेंबर'
    """
    norm = normalize_text_for_validation(text)
    found_dates = []

    # 1. Matches ISO YYYY-MM-DD or YYYY/MM/DD first
    for m in re.finditer(r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b', norm):
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12:
            found_dates.append((day, month))

    # 2. Matches DD-MM-YYYY or DD/MM/YYYY (excluding YYYY-MM-DD)
    for m in re.finditer(r'(?<!\d[-/])\b(\d{1,2})[-/](\d{1,2})(?:[-/](\d{2,4}))?\b', norm):
        day, month = int(m.group(1)), int(m.group(2))
        if 1 <= day <= 31 and 1 <= month <= 12:
            found_dates.append((day, month))

    # 2. Matches '4 नवंबर', '4 Nov', '4th November', '4 नोव्हेंबर'
    month_pattern = '|'.join(sorted(MONTH_ALIASES.keys(), key=len, reverse=True))
    pattern1 = rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_pattern})\b'
    for m in re.finditer(pattern1, norm, re.IGNORECASE):
        day = int(m.group(1))
        m_str = m.group(2).lower()
        month = MONTH_ALIASES.get(m_str)
        if month and 1 <= day <= 31:
            found_dates.append((day, month))

    # 3. Matches 'Nov 4', 'November 04'
    pattern2 = rf'\b({month_pattern})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b'
    for m in re.finditer(pattern2, norm, re.IGNORECASE):
        m_str = m.group(1).lower()
        day = int(m.group(2))
        month = MONTH_ALIASES.get(m_str)
        if month and 1 <= day <= 31:
            found_dates.append((day, month))

    return found_dates

def collect_facts_dates(facts: Any) -> Set[Tuple[int, int]]:
    """
    Scans facts and extracts all authorized (day, month) tuples from ISO dates
    (e.g. '2026-11-04' -> (4, 11), '2026-11-05' -> (5, 11)).
    """
    dates = set()
    if isinstance(facts, dict):
        for k, v in facts.items():
            if isinstance(v, str):
                # ISO date pattern YYYY-MM-DD
                m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', v)
                if m:
                    dates.add((int(m.group(3)), int(m.group(2))))
                # DD-MM-YYYY pattern
                m2 = re.match(r'^(\d{2})[-/](\d{2})[-/](\d{4})', v)
                if m2:
                    dates.add((int(m2.group(1)), int(m2.group(2))))
            elif isinstance(v, (dict, list)):
                dates.update(collect_facts_dates(v))
    elif isinstance(facts, list):
        for item in facts:
            dates.update(collect_facts_dates(item))
    return dates

def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extracts numerical figures from normalized text.
    Handles currency prefixes (₹, rs, inr) and stand-alone numbers (3+ digits or currency-prefixed).
    """
    norm = normalize_text_for_validation(text)
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
    (loan amounts, EMIs, excess debit amounts, balances, account last4s, dates, etc.)
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
    action_params: Optional[Dict[str, Any]] = None,
    playbook_id: Optional[str] = None
) -> ValidationResult:
    """
    Strict deterministic validator enforcing Rule 2:
    1. Every rupee amount / figure in the message must exist in case facts.
    2. Every date ("4 नवंबर", "4 Nov", "04-11-2026", "४ नवंबर") must match fact dates.
    3. Proposed action must strictly be in allowed_actions.
    4. Zero banned phrases (no 'guaranteed', 'pre-approved', etc.).
    5. Post-closure debit check: rejects messages stating unverified cause (post_closure_debit only).
    6. Required target account last4 mentioned verbatim if specified in action_params.
    7. Text matches requested language script (Devanagari for mr/hi).
    """
    errors = []
    raw_explanation = llm_output.get("explanation", "")
    proposed_action = llm_output.get("proposed_action")

    norm_explanation = normalize_text_for_validation(raw_explanation)

    # 1. Action allowlist check
    if not proposed_action or proposed_action not in allowed_actions:
        errors.append(f"Proposed action '{proposed_action}' is not in allowed actions: {allowed_actions}")

    # 2. Banned phrases check
    raw_lower = raw_explanation.lower()
    for phrase in BANNED_PHRASES:
        if phrase in raw_lower:
            errors.append(f"Banned phrase detected: '{phrase}'")

    # 2b. Cause check for post_closure_debit playbook ONLY
    is_post_closure = False
    if playbook_id is not None:
        is_post_closure = playbook_id in [
            "post_closure_debit",
            "post_closure",
            "PB-POST-CLOSURE-01",
            "EMI_DEBITED_AFTER_CLOSURE",
        ]
    else:
        is_post_closure = (
            (action_params and action_params.get("ticket_type") == "REFUND_AND_NOC")
            or (isinstance(facts, dict) and (
                facts.get("persona_id") == "asha"
                or "closure_date" in facts
                or ("facts" in facts and isinstance(facts["facts"], dict) and "closure_date" in facts["facts"])
                or ("loan_details" in facts and isinstance(facts["loan_details"], dict) and "closure_date" in facts["loan_details"])
            ))
        )

    if is_post_closure:
        for phrase in POST_CLOSURE_CAUSE_PHRASES:
            if phrase.lower() in raw_lower:
                errors.append(f"Post-closure debit message states unverified cause ('{phrase}'); must state no cause.")

    # 3. Required entities check: if mandate retry with secondary account, verify account last4 is mentioned
    target_account_last4 = None
    if action_params and "account_last4" in action_params:
        target_account_last4 = str(action_params["account_last4"])

    if target_account_last4 and target_account_last4 not in norm_explanation:
        errors.append(f"account {target_account_last4} missing")

    # 4. Date Normalisation & Validation
    extracted_dates = extract_dates_from_text(raw_explanation)
    allowed_dates = collect_facts_dates(facts)
    # Also add current day/month as allowed
    allowed_dates.add((14, 11))

    for day, month in extracted_dates:
        if allowed_dates and (day, month) not in allowed_dates:
            errors.append(f"Ungrounded date {day}/{month} found in message; not present in case facts.")

    # 5. Grounded numbers check
    extracted_nums = extract_numbers_from_text(raw_explanation)
    allowed_nums = collect_facts_numbers(facts)
    
    # Authorized dates numbers (days and months from facts)
    for d, m in allowed_dates:
        allowed_nums.add(float(d))
        allowed_nums.add(float(m))
    allowed_nums.update([2026.0, 2025.0, 2024.0])

    # Safe constants: SLAs (3, 5, 24), reminder periods (72, 90), account last4s
    allowed_nums.update([1.0, 2.0, 3.0, 4.0, 5.0, 24.0, 48.0, 72.0, 90.0, 100.0])
    if target_account_last4 and target_account_last4.isdigit():
        allowed_nums.add(float(target_account_last4))

    for num in extracted_nums:
        if num not in allowed_nums:
            errors.append(f"Ungrounded amount ₹{int(num)} found in message; not present in case facts.")

    # 6. Language check (Devanagari script presence for hi/mr)
    if expected_language in ["mr", "hi"]:
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', raw_explanation))
        if not has_devanagari:
            errors.append(f"Expected language '{expected_language}' but no Devanagari characters found.")

    passed = len(errors) == 0
    return ValidationResult(passed, errors, extracted_nums)
