import pytest
from src.validator import validate_llm_output, extract_numbers_from_text

def test_validator_passes_valid_marathi_output():
    facts = {
        "loan_details": {"emi_amount": 4650, "loan_amount": 50000},
        "bank_accounts": [
            {"account_last4": "9012", "bank_name": "HDFC"},
            {"account_last4": "4521", "bank_name": "SBI"}
        ]
    }
    allowed_actions = ["retry_mandate", "book_callback"]
    
    llm_output = {
        "explanation": "तुमच्या HDFC खात्यात शिल्लक नसल्याने अडचण झाली. आपण SBI खात्यावरून पुन्हा प्रयत्न करू शकता.",
        "proposed_action": "retry_mandate",
        "action_label": "SBI खात्यावरून प्रयत्न करा",
        "confidence": 0.95
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="mr")
    assert res.passed is True
    assert len(res.errors) == 0

def test_validator_rejects_ungrounded_amount():
    facts = {
        "loan_details": {"emi_amount": 4650, "loan_amount": 50000}
    }
    allowed_actions = ["retry_mandate"]
    
    # Model hallucinated ₹99,999 which does not exist in facts
    llm_output = {
        "explanation": "तुमचे ₹99999 चे कर्ज मंजूर झाले आहे.",
        "proposed_action": "retry_mandate",
        "action_label": "पुढे जा"
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="mr")
    assert res.passed is False
    assert any("Ungrounded amount" in err for err in res.errors)

def test_validator_rejects_banned_phrases():
    facts = {"loan_details": {"loan_amount": 50000}}
    allowed_actions = ["retry_mandate"]
    
    # Model used banned phrase "guaranteed"
    llm_output = {
        "explanation": "Your loan approval is guaranteed once you retry.",
        "proposed_action": "retry_mandate",
        "action_label": "Retry"
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="en")
    assert res.passed is False
    assert any("Banned phrase detected" in err for err in res.errors)

def test_validator_rejects_unauthorized_action():
    facts = {"loan_details": {"loan_amount": 50000}}
    allowed_actions = ["retry_mandate"]
    
    # Model proposed "move_money" or "waive_charges"
    llm_output = {
        "explanation": "We will waive all charges for you.",
        "proposed_action": "waive_charges",
        "action_label": "Waive"
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="en")
    assert res.passed is False
    assert any("not in allowed actions" in err for err in res.errors)

def test_devanagari_digit_normalisation():
    from src.validator import normalize_text_for_validation
    raw = "खाते क्र. ९०१२ वरून ₹४,५०० व ४५२१"
    normalized = normalize_text_for_validation(raw)
    assert "9012" in normalized
    assert "4500" in normalized
    assert "4521" in normalized

def test_date_normalisation_matches_fact_dates():
    facts = {
        "closure_date": "2026-11-04",
        "debit_date": "2026-11-05",
        "excess_debit_amount": 4500,
        "loan_amount": 150000,
        "bank_account_masked": "ICICI Bank ending 7810"
    }
    allowed_actions = ["create_ticket", "request_noc", "request_bureau_correction"]
    action_params = {"account_last4": "7810", "refund_amount": 4500}

    # All these date variants must match the fact dates (4 Nov, 5 Nov)
    variants = [
        ("4 नवंबर", "आशा जी, आपका ऋण 4 नवंबर को बंद हुआ, 5 नवंबर को ₹4500 कटे (खाता 7810)।"),
        ("4 Nov", "Asha, your loan closed on 4 Nov, but ₹4500 debited on 5 Nov (account 7810)."),
        ("04-11-2026", "आशा जी, 04-11-2026 को ऋण बंद हुआ और 05-11-2026 को ₹4500 कटे (खाता 7810)।"),
        ("४ नवंबर", "आशा जी, आपका ऋण ४ नवंबर को बंद हुआ, ५ नवंबर को ₹४५०० कटे (खाता ७८१०)।")
    ]
    for label, text in variants:
        lang = "en" if "Asha" in text else "hi"
        res = validate_llm_output(
            {"explanation": text, "proposed_action": "create_ticket", "action_label": "Refund"},
            facts=facts,
            allowed_actions=allowed_actions,
            expected_language=lang,
            action_params=action_params
        )
        assert res.passed is True, f"Failed for variant {label}: {res.errors}"

def test_validator_rejects_ungrounded_dates():
    facts = {
        "closure_date": "2026-11-04",
        "debit_date": "2026-11-05",
        "excess_debit_amount": 4500,
        "bank_account_masked": "ICICI Bank ending 7810"
    }
    allowed_actions = ["create_ticket"]
    action_params = {"account_last4": "7810"}

    # Ungrounded date: 12 December
    res = validate_llm_output(
        {"explanation": "आशा जी, आपका ऋण 12 दिसंबर को बंद हुआ और खाता 7810 से पैसे कटे।", "proposed_action": "create_ticket"},
        facts=facts,
        allowed_actions=allowed_actions,
        expected_language="hi",
        action_params=action_params
    )
    assert res.passed is False
    assert any("Ungrounded date 12/12" in err for err in res.errors)

def test_post_closure_validator_rejects_cause_phrases():
    facts = {
        "closure_date": "2026-11-04",
        "debit_date": "2026-11-05",
        "excess_debit_amount": 4500,
        "bank_account_masked": "ICICI Bank ending 7810"
    }
    allowed_actions = ["create_ticket", "request_noc", "request_bureau_correction"]
    action_params = {"account_last4": "7810", "refund_amount": 4500}

    # Test each blocked cause phrase for post-closure debit
    blocked_phrases = ["कारण", "क्योंकि", "because", "due to", "automated", "ऑटोमेटेड"]
    for phrase in blocked_phrases:
        if phrase in ["because", "due to", "automated"]:
            lang = "en"
            text = f"Your loan closed on 04 Nov 2026, but ₹4500 debited on 05 Nov from 7810 {phrase} clearing cycle."
        elif phrase in ["कारण", "ऑटोमेटेड"]:
            lang = "mr"
            text = f"कर्ज 04-11-2026 रोजी बंद झाले, पण 7810 खात्यातून 05-11-2026 रोजी ₹4500 कापले {phrase}."
        else:
            lang = "hi"
            text = f"लोन 04-11-2026 को बंद हुआ, पर 7810 खाते से 05-11-2026 को ₹4500 कटे {phrase}।"

        res = validate_llm_output(
            {"explanation": text, "proposed_action": "create_ticket"},
            facts=facts,
            allowed_actions=allowed_actions,
            expected_language=lang,
            action_params=action_params,
            playbook_id="post_closure_debit"
        )
        assert res.passed is False, f"Expected rejection for phrase: '{phrase}'"
        assert any("unverified cause" in err for err in res.errors)

def test_mandate_validator_allows_karan_phrase():
    facts = {
        "loan_details": {"emi_amount": 4650, "loan_amount": 50000},
        "bank_accounts": [
            {"account_last4": "9012", "bank_name": "HDFC"},
            {"account_last4": "4521", "bank_name": "SBI"}
        ]
    }
    allowed_actions = ["retry_mandate", "book_callback"]
    action_params = {"account_last4": "4521"}

    # Rohit mandate explanation explicitly using 'कारण'
    llm_output = {
        "explanation": "तुमच्या HDFC खात्यात (9012) अपुरी शिल्लक हे ई-मँडेट अयशस्वी होण्याचे कारण आहे. आपण SBI खात्यावरून (4521) पुन्हा प्रयत्न करू का?",
        "proposed_action": "retry_mandate",
        "action_label": "पुन्हा प्रयत्न करा"
    }
    res = validate_llm_output(
        llm_output,
        facts=facts,
        allowed_actions=allowed_actions,
        expected_language="mr",
        action_params=action_params,
        playbook_id="mandate_retry"
    )
    assert res.passed is True
    assert len(res.errors) == 0


