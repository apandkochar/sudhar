import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "llm_cache.json"

DEFAULT_SEED_CACHE = {
    "rohit:mr": {
        "explanation": "रोहितजी, निंबस फायनान्सच्या तुमच्या कर्जाचा ई-मँडेट (खाते क्रमांक 9012) शिल्लक अपुरी असल्याने अयशस्वी झाला. तुमच्या स्टेट बँक ऑफ इंडिया खात्यामध्ये (क्रमांक 4521) पुरेशी शिल्लक उपलब्ध आहे. काय आपण त्या खात्यावरून ई-मँडेट पुन्हा सेट करू का?",
        "proposed_action": "retry_mandate",
        "action_label": "ई-मँडेट पुन्हा सेट करा",
        "confidence": 0.95,
        "cached_at": "2026-11-14T12:00:00Z"
    },
    "rohit:hi": {
        "explanation": "रोहित जी, आपके HDFC बैंक खाते (अंतिम अंक 9012) में न्यूनतम शेष राशि न होने से ई-मैंडेट पंजीकरण विफल रहा। आपके SBI खाते (अंतिम अंक 4521) में पर्याप्त राशि उपलब्ध है। क्या हम उस खाते से ई-मैंडेट दोबारा शुरू करें?",
        "proposed_action": "retry_mandate",
        "action_label": "ई-मैंडेट दोबारा शुरू करें",
        "confidence": 0.95,
        "cached_at": "2026-11-14T12:00:00Z"
    },
    "rohit:en": {
        "explanation": "Rohit, your e-mandate on HDFC Bank ending 9012 failed due to insufficient balance. Your State Bank of India account ending 4521 has sufficient balance. Shall we set up auto-debit using that account?",
        "proposed_action": "retry_mandate",
        "action_label": "Retry with SBI Account",
        "confidence": 0.95,
        "cached_at": "2026-11-14T12:00:00Z"
    },
    "asha:hi": {
        "explanation": "आशा जी, आपका व्यक्तिगत ऋण 04 नवंबर 2026 को पूर्ण रूप से बंद हो चुका था, परंतु 05 नवंबर को ₹4500 की EMI बैंक समाशोधन चक्र के कारण कट गई। क्या हम आपके ICICI खाते (अंतिम अंक 7810) में ₹4500 की धनवापसी और नो-ड्यूज प्रमाणपत्र (NOC) का अनुरोध शुरू करें?",
        "proposed_action": "create_ticket",
        "action_label": "रिफंड व NOC अनुरोध करें",
        "confidence": 0.95,
        "cached_at": "2026-11-14T12:00:00Z"
    },
    "asha:en": {
        "explanation": "Asha, your loan was closed on 04 Nov 2026, but an EMI of ₹4500 was debited on 05 Nov due to the clearing cycle. Shall we initiate a full refund of ₹4500 to ICICI account ending 7810 and request your No-Dues Certificate (NOC)?",
        "proposed_action": "create_ticket",
        "action_label": "Initiate Refund & NOC",
        "confidence": 0.95,
        "cached_at": "2026-11-14T12:00:00Z"
    },
    "sunita:hi": {
        "explanation": "सुनीता जी, नेटवर्क ड्रॉप के कारण आपका वीडियो KYC कॉल बीच में छूट गया। आपका पैन कार्ड सत्यापन पहले ही सफल हो चुका है। क्या हम आपके मोबाइल (अंतिम अंक 3210) पर 72 घंटे के लिए मान्य डायरेक्ट रिज्यूम लिंक भेजें?",
        "proposed_action": "send_vkyc_resume_link",
        "action_label": "रिज्यूम लिंक भेजें",
        "confidence": 0.95,
        "cached_at": "2026-11-14T12:00:00Z"
    }
}

def load_cache() -> Dict[str, Any]:
    if not CACHE_FILE.exists():
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SEED_CACHE, f, ensure_ascii=False, indent=2)
        return dict(DEFAULT_SEED_CACHE)
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load cache file: {e}")
        return dict(DEFAULT_SEED_CACHE)

def get_cached_llm_response(persona_id: str, language: str) -> Optional[Dict[str, Any]]:
    """
    Returns last validated Gemini response for (persona_id, language).
    """
    cache = load_cache()
    key = f"{persona_id.lower()}:{language.lower()}"
    return cache.get(key)

def save_cached_llm_response(persona_id: str, language: str, response: Dict[str, Any]) -> None:
    """
    Saves a validated Gemini response to disk cache.
    """
    cache = load_cache()
    key = f"{persona_id.lower()}:{language.lower()}"
    cache[key] = response
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to persist LLM cache: {e}")
