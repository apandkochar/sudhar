import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx

from src.config import DEMO_MODE, GEMINI_API_KEY, GEMINI_MODEL
from src.validator import validate_llm_output, ValidationResult

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

LLM_SYSTEM_PROMPT = """You are Sudhaar, an empathetic, transparent, consent-first AI assistant inside Paytm's loan journeys (lender: Nimbus Finance).
Your job: Explain why a loan moment broke in clear, reassuring language, and propose the single verified fix decided by deterministic rules.

NON-NEGOTIABLE SAFETY RULES:
1. Rules decide, you only speak. The allowed action and facts are given to you. NEVER invent a new action, interest rate, fee, or outcome.
2. Grounded facts ONLY. NEVER invent, round, or alter any numbers, rupee amounts, or dates. Only reference numbers that exist in facts.
3. NEVER promise loan approval, guarantee disbursal, or use banned phrases like "guaranteed", "pre-approved", or "100% approved".
4. You NEVER move money, waive charges, or edit KYC. All actions require customer consent.
5. Language: You MUST write the explanation and action_label strictly in the requested language (Marathi for 'mr', Hindi for 'hi', English for 'en'). Use natural, culturally respectful phrasing.

You MUST respond strictly with a valid JSON object matching this schema:
{
  "explanation": "concise explanation in requested language (max 60 words)",
  "proposed_action": "must match an item in allowed_actions exactly",
  "action_label": "CTA button label in requested language",
  "confidence": 0.95
}
"""

def generate_with_gemini(
    context_packet: Dict[str, Any],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    key = api_key or GEMINI_API_KEY
    model = model_name or GEMINI_MODEL
    
    if not key or DEMO_MODE == "offline":
        # Offline mode or no API key -> signal fallback to approved template
        return None

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

    try:
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return None
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}")
        return None

def draft_explanation_with_validator(
    context_packet: Dict[str, Any],
    facts: Dict[str, Any],
    allowed_actions: List[str],
    language: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any], str]:
    """
    Executes the LLM gateway with strict 2-attempt validation:
    1. First Gemini call.
    2. Validator check.
    3. If failed: Retry once with feedback.
    4. If still failed or offline: Fall back to approved template.
    Returns: (output_dict, validation_trace_details, source_mode)
    """
    # 1. First Attempt
    llm_draft = generate_with_gemini(context_packet, api_key=api_key, model_name=model_name)
    
    if llm_draft:
        val_result = validate_llm_output(llm_draft, facts, allowed_actions, language)
        if val_result.passed:
            return llm_draft, {
                "passed": True,
                "attempt": 1,
                "source": "gemini",
                "errors": []
            }, "gemini"
        
        # 2. Retry Attempt with validation error feedback
        retry_packet = dict(context_packet)
        retry_packet["validation_error"] = f"Previous attempt failed safety validation: {'; '.join(val_result.errors)}. Correct these errors immediately."
        retry_draft = generate_with_gemini(retry_packet, api_key=api_key, model_name=model_name)
        
        if retry_draft:
            retry_val = validate_llm_output(retry_draft, facts, allowed_actions, language)
            if retry_val.passed:
                return retry_draft, {
                    "passed": True,
                    "attempt": 2,
                    "source": "gemini",
                    "errors": []
                }, "gemini"
            
            # Second attempt failed -> fall back to template
            return None, {
                "passed": False,
                "attempt": 2,
                "source": "template_fallback",
                "errors": retry_val.errors,
                "reason": "Model failed validation twice. Reverted safely to approved template."
            }, "template"

    # Offline mode or API unreachable
    return None, {
        "passed": True,
        "attempt": 0,
        "source": "template",
        "errors": [],
        "reason": "Offline mode active or API key absent. Serving pre-approved template."
    }, "template"
