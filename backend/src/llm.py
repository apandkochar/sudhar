import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

from src.config import DEMO_MODE, GEMINI_API_KEY, GEMINI_MODEL
from src.validator import validate_llm_output, ValidationResult

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

LLM_SYSTEM_PROMPT = """You are Sudhaar, an empathetic, transparent, consent-first AI assistant inside Paytm's loan journeys (lender: Nimbus Finance).
Your job: Explain why a loan moment broke in clear, reassuring language, and ask permission to execute the verified fix decided by deterministic rules.

NON-NEGOTIABLE SAFETY RULES:
1. Rules decide, you only speak. The allowed action and facts are given to you. NEVER invent a new action, interest rate, fee, or outcome.
2. Grounded facts ONLY. NEVER invent, round, or alter any numbers, rupee amounts, or dates. Only reference numbers that exist in facts.
3. NEVER promise loan approval, guarantee disbursal, or use banned phrases like "guaranteed", "pre-approved", or "100% approved".
4. You NEVER move money, waive charges, or edit KYC. All actions require customer consent.
5. Language: You MUST write the explanation and action_label strictly in the requested language (Marathi for 'mr', Hindi for 'hi', English for 'en'). Use natural, culturally respectful phrasing.
6. Question for permission: End the explanation with a polite question asking for permission to proceed (e.g. Marathi: "...त्या खात्यावरून ई-मँडेट पुन्हा सेट करू का?", Hindi: "...क्या हम उस खाते से ई-मैंडेट दोबारा सेट करें?").

You MUST respond strictly with a valid JSON object matching this schema:
{
  "explanation": "concise explanation ending with permission question in requested language (max 60 words)",
  "proposed_action": "must match an item in allowed_actions exactly",
  "action_label": "CTA button label in requested language",
  "confidence": 0.95
}
"""

def generate_with_gemini(
    context_packet: Dict[str, Any],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout_sec: float = 5.0
) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
    """
    Invokes Gemini API with strict 5.0-second timeout.
    Returns: (result_dict_or_None, latency_seconds, error_reason_or_None)
    """
    key = api_key or GEMINI_API_KEY
    model = model_name or GEMINI_MODEL
    
    if not key or DEMO_MODE == "offline":
        return None, 0.0, "offline_mode"

    url = f"{GEMINI_API_URL}/{model}:generateContent?key={key}"
    
    user_prompt = f"""Task: {context_packet.get('task')}
Language: {context_packet.get('language')}
Moment: {context_packet.get('moment')}
Cause from Code Table: {context_packet.get('cause')}
Allowed Actions: {json.dumps(context_packet.get('allowed_actions'))}
Case Facts: {json.dumps(context_packet.get('facts'))}

Produce the structured JSON response in {context_packet.get('language')}."""

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": LLM_SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
            "maxOutputTokens": 300
        }
    }

    t0 = time.time()
    try:
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.post(url, json=payload)
            latency = time.time() - t0
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text), latency, None
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return None, latency, f"status_{resp.status_code}"
    except httpx.TimeoutException:
        latency = time.time() - t0
        logger.warning(f"Gemini API call timed out after {latency:.1f}s")
        return None, latency, "timeout"
    except Exception as e:
        latency = time.time() - t0
        logger.warning(f"Gemini API call failed: {e}")
        return None, latency, str(e)

def draft_explanation_with_validator(
    context_packet: Dict[str, Any],
    facts: Dict[str, Any],
    allowed_actions: List[str],
    language: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any], str, str]:
    """
    Executes the LLM gateway with strict 5-second timeout and validation:
    1. First Gemini call (5s timeout).
    2. Validator check.
    3. If failed: Retry once with feedback.
    4. If timeout or double failure: Fall back to approved template.
    Returns: (output_dict, validation_trace_details, source_mode, trace_summary)
    """
    lang_map = {"mr": "Marathi", "hi": "Hindi", "en": "English"}
    lang_name = lang_map.get(language, "Marathi")

    # 1. First Attempt with 5.0s timeout
    llm_draft, latency, err = generate_with_gemini(
        context_packet, api_key=api_key, model_name=model_name, timeout_sec=5.0
    )
    
    if llm_draft:
        val_result = validate_llm_output(llm_draft, facts, allowed_actions, language)
        if val_result.passed:
            summary = f"Gemini wrote the {lang_name} message ({latency:.1f} s)"
            return llm_draft, {
                "passed": True,
                "attempt": 1,
                "source": "gemini",
                "latency_sec": round(latency, 2),
                "summary": summary
            }, "gemini", summary
        
        # 2. Retry Attempt if validation failed
        retry_packet = dict(context_packet)
        retry_packet["validation_error"] = f"Previous attempt failed safety validation: {'; '.join(val_result.errors)}. Correct these errors immediately."
        retry_draft, r_latency, r_err = generate_with_gemini(
            retry_packet, api_key=api_key, model_name=model_name, timeout_sec=5.0
        )
        total_latency = latency + r_latency
        
        if retry_draft:
            retry_val = validate_llm_output(retry_draft, facts, allowed_actions, language)
            if retry_val.passed:
                summary = f"Gemini wrote the {lang_name} message ({total_latency:.1f} s · retry 2)"
                return retry_draft, {
                    "passed": True,
                    "attempt": 2,
                    "source": "gemini",
                    "latency_sec": round(total_latency, 2),
                    "summary": summary
                }, "gemini", summary
            
            summary = "Template fallback · Gemini validation failed twice"
            return None, {
                "passed": False,
                "attempt": 2,
                "source": "template_fallback",
                "latency_sec": round(total_latency, 2),
                "summary": summary
            }, "template", summary

    # Error or timeout fallback
    if err == "timeout":
        summary = f"Template · Gemini timeout ({latency:.1f} s)"
    elif err == "offline_mode":
        summary = "Template · Offline mode"
    else:
        summary = f"Template · Fallback ({err or 'API unavailable'})"

    return None, {
        "passed": True,
        "attempt": 0,
        "source": "template",
        "latency_sec": round(latency, 2),
        "reason": summary,
        "summary": summary
    }, "template", summary
