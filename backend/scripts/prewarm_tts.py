import json
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from src.config import DATA_DIR
from src.tts import is_cached, synthesize

def main():
    templates_dir = DATA_DIR / "templates"
    llm_cache_path = DATA_DIR / "llm_cache.json"

    items = []

    # 1. Load templates for mr, hi, en
    for lang in ["mr", "hi", "en"]:
        t_file = templates_dir / f"{lang}.json"
        if not t_file.exists():
            continue
        with open(t_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            templates = data.get("templates", {})
            for t_key, t_val in templates.items():
                explanation = t_val.get("explanation", "").strip()
                if explanation:
                    items.append({
                        "id": f"template:{t_key}:{lang}",
                        "lang": lang,
                        "text": explanation,
                    })

    # 2. Load llm_cache.json
    if llm_cache_path.exists():
        with open(llm_cache_path, "r", encoding="utf-8") as f:
            llm_cache = json.load(f)
            for cache_key, cache_val in llm_cache.items():
                explanation = cache_val.get("explanation", "").strip()
                lang = cache_key.split(":")[1] if ":" in cache_key else "en"
                if explanation:
                    items.append({
                        "id": f"llm_cache:{cache_key}",
                        "lang": lang,
                        "text": explanation,
                    })

    results = []
    total_chars_sent = 0

    for item in items:
        msg_id = item["id"]
        lang = item["lang"]
        text = item["text"]
        char_count = len(text)

        was_cached = is_cached(text, lang)
        audio = synthesize(text, lang, timeout_sec=10.0)
        is_now_cached = is_cached(text, lang)

        if not was_cached and audio:
            total_chars_sent += char_count

        results.append({
            "id": msg_id,
            "lang": lang,
            "chars": char_count,
            "cached": "yes" if is_now_cached else "no",
            "source": "cache-hit" if was_cached else "sarvam-live" if audio else "failed"
        })

    # Print Table
    header_fmt = "{:<34} | {:<5} | {:<6} | {:<8} | {:<12}"
    divider = "-" * 75
    print(header_fmt.format("Message ID", "Lang", "Chars", "Cached", "Source"))
    print(divider)
    for r in results:
        print(header_fmt.format(r["id"], r["lang"], r["chars"], r["cached"], r["source"]))
    print(divider)

    cached_count = sum(1 for r in results if r["cached"] == "yes")
    print(f"\nTotal messages: {len(results)}")
    print(f"Cached: {cached_count}/{len(results)}")
    print(f"Total characters sent to Sarvam: {total_chars_sent}")

if __name__ == "__main__":
    main()

