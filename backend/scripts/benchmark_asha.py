import os
import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.llm import generate_with_gemini
from src.validator import validate_llm_output
from src.context import load_code_table, build_context_packet

def run_asha_benchmark():
    facts = {
        "persona_id": "asha",
        "name": "Asha Sharma",
        "city": "Mumbai",
        "loan_id": "LN-ASHA-PERSONAL-150K",
        "loan_amount": 150000,
        "closure_date": "2026-11-04",
        "debit_date": "2026-11-05",
        "excess_debit_amount": 4500,
        "bank_account_masked": "ICICI Bank ending 7810"
    }
    allowed_actions = ["create_ticket", "request_noc", "request_bureau_correction", "set_reminder", "book_callback"]
    action_params = {
        "ticket_type": "REFUND_AND_NOC",
        "refund_amount": 4500,
        "account_last4": "7810"
    }
    
    code_entry = load_code_table().get("LMS_POST_CLOSURE_DEBIT", {})

    print(f"=== Running Asha Benchmark on {GEMINI_MODEL} ===")
    print(f"API Key present: {bool(GEMINI_API_KEY)}")

    runs = [("hi", i + 1) for i in range(10)] + [("en", i + 1) for i in range(5)]
    results = []

    for lang, idx in runs:
        lang_name = "Hindi" if lang == "hi" else "English"
        context_packet = build_context_packet(
            task="explain_and_propose",
            language=lang,
            moment="EMI_DEBITED_AFTER_CLOSURE",
            facts=facts,
            code_entry=code_entry,
            allowed_actions=allowed_actions
        )


        t0 = time.time()
        draft, latency, err = generate_with_gemini(
            context_packet,
            api_key=GEMINI_API_KEY,
            model_name=GEMINI_MODEL,
            timeout_sec=5.0
        )
        total_time = time.time() - t0

        if not draft:
            status = "TIMEOUT / ERROR"
            fail_reason = err or "no draft returned"
            passed = False
        else:
            val = validate_llm_output(
                draft,
                facts=facts,
                allowed_actions=allowed_actions,
                expected_language=lang,
                action_params=action_params
            )
            passed = val.passed
            if passed:
                status = "PASSED"
                fail_reason = "None (Passed Rule 2)"
            else:
                status = "REJECTED"
                fail_reason = val.errors[0] if val.errors else "Unknown validation error"

        res_entry = {
            "lang": lang_name,
            "run": idx,
            "status": status,
            "passed": passed,
            "latency_sec": round(total_time, 2),
            "reason": fail_reason,
            "explanation": draft.get("explanation") if draft else None
        }
        results.append(res_entry)
        print(f"[{lang_name:7} Run {idx:02d}] {status:10} | {total_time:.2f}s | {fail_reason}")
        time.sleep(0.5) # Gentle pause between calls

    # Summary
    hi_results = [r for r in results if r["lang"] == "Hindi"]
    en_results = [r for r in results if r["lang"] == "English"]

    hi_passed = sum(1 for r in hi_results if r["passed"])
    en_passed = sum(1 for r in en_results if r["passed"])

    avg_hi_lat = sum(r["latency_sec"] for r in hi_results) / len(hi_results)
    avg_en_lat = sum(r["latency_sec"] for r in en_results) / len(en_results)
    total_avg_lat = sum(r["latency_sec"] for r in results) / len(results)

    print("\n" + "=" * 60)
    print("ASHA BENCHMARK REPORT")
    print("=" * 60)
    print(f"Hindi (10 runs):   {hi_passed}/10 Passed ({hi_passed*10}%) | Avg Latency: {avg_hi_lat:.2f}s")
    print(f"English (5 runs):  {en_passed}/5 Passed ({en_passed*20}%) | Avg Latency: {avg_en_lat:.2f}s")
    print(f"Overall (15 runs): {hi_passed+en_passed}/15 Passed ({(hi_passed+en_passed)/15*100:.1f}%) | Avg Latency: {total_avg_lat:.2f}s")

    # Output JSON report
    report_path = Path(__file__).resolve().parent / "asha_benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved detailed results to {report_path}")

if __name__ == "__main__":
    run_asha_benchmark()
