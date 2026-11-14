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
6. Question for permission: End the explanation with a polite question asking for permission to proceed (e.g. Marathi: "...त्या खात्यावरून ई-मँडेट पुन्हा सेट करू का?", Hindi: "...क्या हम उस खाते से ई-मैंडेट दोबारा शुरू करें?", English: "...Shall we set up auto-debit using that account?").
7. Western Arabic digits ONLY: You MUST write ALL numbers and amounts using Western Arabic numerals (0, 1, 2, 3, 4, 5, 6, 7, 8, 9). Do NOT write Devanagari numerals (०, १, २, etc.).
8. Verbatim account endings: You MUST include the exact masked account numbers and last 4 digits verbatim from facts (e.g. '9012' for the failed account and '4521' for the suggested SBI account).

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
    timeout_sec: float = 4.0
) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
    """
    Invokes Gemini API with strict timeout.
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

CRITICAL: Use Western digits (0-9) only. Include account ending numbers verbatim.
{context_packet.get('validation_error', '')}

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
    action_params: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], str, Dict[str, Any]]:
    """
    Executes the LLM gateway with strict latency budget and Rule 2 validation:
    - Total Gemini budget: <= 6.0 seconds total.
    - If attempt 1 takes > 4.0s, skip retry and fall back to template.
    - Log exact failure reason for each rejected attempt (AI MODEL purple badge).
    - If template used, separate row 'Approved template used' (deterministic badge).
    Returns: (output_draft_dict, trace_attempts_list, source_mode, val_details)
    """
    lang_map = {"mr": "Marathi", "hi": "Hindi", "en": "English"}
    lang_name = lang_map.get(language, "Marathi")
    trace_attempts: List[Dict[str, Any]] = []

    # If offline mode, directly use template
    if DEMO_MODE == "offline" or not (api_key or GEMINI_API_KEY):
        template_entry = {
            "stage": "TEMPLATE_FALLBACK",
            "layer": "DETERMINISTIC_CODE",
            "is_ai": False,
            "summary": "Approved template used",
            "details": {
                "summary": "Approved template used",
                "source": "template",
                "reason": "Offline mode / pre-approved templates active",
                "latency_sec": 0.0
            }
        }
        val_details = {
            "passed": True,
            "attempt": 0,
            "source": "template",
            "latency_sec": 0.0,
            "summary": "Numbers ✓ · Action allowed ✓ · Language ✓"
        }
        return None, [template_entry], "template", val_details

    # Attempt 1 (4.0s timeout budget)
    t_start = time.time()
    attempt_1_timeout = 4.0
    draft_1, latency_1, err_1 = generate_with_gemini(
        context_packet, api_key=api_key, model_name=model_name, timeout_sec=attempt_1_timeout
    )

    if draft_1:
        val_1 = validate_llm_output(draft_1, facts, allowed_actions, language, action_params)
        if val_1.passed:
            summary = f"Gemini wrote the {lang_name} message ({latency_1:.1f} s)"
            trace_attempts.append({
                "stage": "LLM_DRAFT",
                "layer": "AI_GATEWAY",
                "is_ai": True,
                "summary": summary,
                "details": {
                    "summary": summary,
                    "source": "gemini",
                    "model": model_name or GEMINI_MODEL,
                    "attempt": 1,
                    "latency_sec": round(latency_1, 2),
                    "draft": draft_1
                }
            })
            val_details = {
                "passed": True,
                "attempt": 1,
                "source": "gemini",
                "latency_sec": round(latency_1, 2),
                "summary": "Numbers ✓ · Action allowed ✓ · Language ✓"
            }
            return draft_1, trace_attempts, "gemini", val_details

        # Attempt 1 rejected by safety validator: Log exact failure reason with purple AI badge
        reason_1 = val_1.errors[0] if val_1.errors else "validation failed"
        err_summary_1 = f"Gemini draft rejected · {reason_1}"
        trace_attempts.append({
            "stage": "LLM_DRAFT",
            "layer": "AI_GATEWAY",
            "is_ai": True,
            "summary": err_summary_1,
            "details": {
                "summary": err_summary_1,
                "source": "gemini",
                "model": model_name or GEMINI_MODEL,
                "attempt": 1,
                "latency_sec": round(latency_1, 2),
                "error": reason_1,
                "errors": val_1.errors,
                "rejected_draft": draft_1
            }
        })
    else:
        # Error or timeout on attempt 1
        err_desc = "Gemini timeout" if err_1 == "timeout" else (err_1 or "API error")
        err_summary_1 = f"Gemini draft rejected · {err_desc} ({latency_1:.1f} s)"
        trace_attempts.append({
            "stage": "LLM_DRAFT",
            "layer": "AI_GATEWAY",
            "is_ai": True,
            "summary": err_summary_1,
            "details": {
                "summary": err_summary_1,
                "source": "gemini",
                "model": model_name or GEMINI_MODEL,
                "attempt": 1,
                "latency_sec": round(latency_1, 2),
                "error": err_desc
            }
        })

    # Latency budget check: at most 6s total; if attempt 1 took over 4s, skip retry
    elapsed_so_far = time.time() - t_start
    if latency_1 > 4.0 or elapsed_so_far >= 4.0 or (6.0 - elapsed_so_far) < 1.5:
        # Budget exhausted, skip retry and use template
        template_entry = {
            "stage": "TEMPLATE_FALLBACK",
            "layer": "DETERMINISTIC_CODE",
            "is_ai": False,
            "summary": "Approved template used",
            "details": {
                "summary": "Approved template used",
                "source": "template",
                "reason": "Latency budget exceeded or first attempt > 4s",
                "latency_sec": round(elapsed_so_far, 2)
            }
        }
        trace_attempts.append(template_entry)
        val_details = {
            "passed": True,
            "attempt": 1,
            "source": "template",
            "latency_sec": round(elapsed_so_far, 2),
            "summary": "Numbers ✓ · Action allowed ✓ · Language ✓"
        }
        return None, trace_attempts, "template", val_details

    # Attempt 2 (Retry within remaining budget <= 6.0s total)
    remaining_budget = max(1.0, 6.0 - elapsed_so_far)
    retry_packet = dict(context_packet)
    feedback = f"Previous attempt failed safety validation. Fix: ensure all numbers are Western Arabic digits (0-9) and match facts exactly. Include account ending numbers verbatim."
    retry_packet["validation_error"] = feedback

    draft_2, latency_2, err_2 = generate_with_gemini(
        retry_packet, api_key=api_key, model_name=model_name, timeout_sec=remaining_budget
    )
    total_latency = round(latency_1 + latency_2, 2)

    if draft_2:
        val_2 = validate_llm_output(draft_2, facts, allowed_actions, language, action_params)
        if val_2.passed:
            summary = f"Gemini wrote the {lang_name} message ({total_latency:.1f} s · retry)"
            trace_attempts.append({
                "stage": "LLM_DRAFT",
                "layer": "AI_GATEWAY",
                "is_ai": True,
                "summary": summary,
                "details": {
                    "summary": summary,
                    "source": "gemini",
                    "model": model_name or GEMINI_MODEL,
                    "attempt": 2,
                    "latency_sec": total_latency,
                    "draft": draft_2
                }
            })
            val_details = {
                "passed": True,
                "attempt": 2,
                "source": "gemini",
                "latency_sec": total_latency,
                "summary": "Numbers ✓ · Action allowed ✓ · Language ✓"
            }
            return draft_2, trace_attempts, "gemini", val_details

        # Attempt 2 failed validation
        reason_2 = val_2.errors[0] if val_2.errors else "validation failed on retry"
        err_summary_2 = f"Gemini draft rejected · {reason_2}"
        trace_attempts.append({
            "stage": "LLM_DRAFT",
            "layer": "AI_GATEWAY",
            "is_ai": True,
            "summary": err_summary_2,
            "details": {
                "summary": err_summary_2,
                "source": "gemini",
                "model": model_name or GEMINI_MODEL,
                "attempt": 2,
                "latency_sec": total_latency,
                "error": reason_2,
                "errors": val_2.errors,
                "rejected_draft": draft_2
            }
        })
    else:
        err_desc_2 = "Gemini timeout on retry" if err_2 == "timeout" else (err_2 or "API error on retry")
        err_summary_2 = f"Gemini draft rejected · {err_desc_2}"
        trace_attempts.append({
            "stage": "LLM_DRAFT",
            "layer": "AI_GATEWAY",
            "is_ai": True,
            "summary": err_summary_2,
            "details": {
                "summary": err_summary_2,
                "source": "gemini",
                "model": model_name or GEMINI_MODEL,
                "attempt": 2,
                "latency_sec": total_latency,
                "error": err_desc_2
            }
        })

    # Both attempts failed: Fall back to approved template
    template_entry = {
        "stage": "TEMPLATE_FALLBACK",
        "layer": "DETERMINISTIC_CODE",
        "is_ai": False,
        "summary": "Approved template used",
        "details": {
            "summary": "Approved template used",
            "source": "template",
            "reason": "Gemini validation failed after 2 attempts",
            "latency_sec": total_latency
        }
    }
    trace_attempts.append(template_entry)
    val_details = {
        "passed": True,
        "attempt": 2,
        "source": "template",
        "latency_sec": total_latency,
        "summary": "Numbers ✓ · Action allowed ✓ · Language ✓"
    }
    return None, trace_attempts, "template", val_details
