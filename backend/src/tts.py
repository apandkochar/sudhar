import base64
import hashlib
import logging
import os
from pathlib import Path
from typing import Optional
import httpx

from src.config import AUDIO_CACHE_DIR, DEMO_MODE, SARVAM_API_KEY

logger = logging.getLogger(__name__)

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_MODEL = "bulbul:v4-flash"

# Conversational persona-based female speakers in bulbul:v4-flash
CONVERSATIONAL_SPEAKERS = {
    "mr-IN": "ishita_mr_conversational",
    "hi-IN": "kavya_hi_conversational",
    "en-IN": "ishita_en_customer",
}

# Mapping input lang code to Sarvam BCP-47 target_language_code
LANG_MAP = {
    "mr": "mr-IN",
    "mr-in": "mr-IN",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "en": "en-IN",
    "en-in": "en-IN",
}

def get_cache_key(lang: str, text: str, model: str = SARVAM_MODEL, speaker: Optional[str] = None) -> str:
    """Computes sha256(model+speaker+lang+text) hex digest."""
    target_lang_code = LANG_MAP.get(lang.lower(), "en-IN")
    sp = speaker or CONVERSATIONAL_SPEAKERS.get(target_lang_code, "kavya_hi_conversational")
    payload_str = f"{model}:{sp}:{lang}:{text}"
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

def get_cache_path(text: str, lang: str, model: str = SARVAM_MODEL, speaker: Optional[str] = None) -> Path:
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = get_cache_key(lang, text, model=model, speaker=speaker)
    return AUDIO_CACHE_DIR / f"{cache_key}.wav"

def is_cached(text: str, lang: str, model: str = SARVAM_MODEL, speaker: Optional[str] = None) -> bool:
    path = get_cache_path(text, lang, model=model, speaker=speaker)
    return path.exists() and path.stat().st_size > 0

def synthesize(text: str, lang: str, timeout_sec: float = 3.0) -> Optional[bytes]:
    """
    Synthesizes speech for the given text and language using Sarvam TTS (Bulbul v4-flash).
    - Checks disk cache: data/audio_cache/<sha256(lang+text)>.wav. Cache hit = no network call.
    - If DEMO_MODE=offline: serves cached audio only, never calls the network.
    - If SARVAM_API_KEY is not set or network call fails/times out: returns None (204).
    - Never logs the API key.
    - Default timeout: 3.0s for live API calls.
    """
    if not text or not text.strip():
        return None

    # 1. Check disk cache: data/audio_cache/<sha256(lang+text)>.wav
    cache_path = get_cache_path(text, lang)
    if cache_path.exists() and cache_path.stat().st_size > 0:
        try:
            return cache_path.read_bytes()
        except Exception as e:
            logger.warning("Failed to read audio cache: %s", type(e).__name__)

    # 2. Offline mode check
    current_demo_mode = os.getenv("DEMO_MODE", DEMO_MODE).lower()
    if current_demo_mode == "offline":
        return None

    # 3. Check Sarvam API key (never log the key)
    api_key = os.getenv("SARVAM_API_KEY", SARVAM_API_KEY).strip()
    if not api_key:
        return None

    target_lang_code = LANG_MAP.get(lang.lower(), "en-IN")
    speaker = CONVERSATIONAL_SPEAKERS.get(target_lang_code, "kavya_hi_conversational")

    payload = {
        "text": text,
        "target_language_code": target_lang_code,
        "speaker": speaker,
        "model": SARVAM_MODEL,
        "pace": 0.95,
        "output_audio_codec": "wav"
    }

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.post(SARVAM_TTS_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.warning("Sarvam TTS returned status code: %d", resp.status_code)
                return None

            data = resp.json()
            audios = data.get("audios")
            if not audios or not isinstance(audios, list) or len(audios) == 0:
                return None

            audio_bytes = base64.b64decode(audios[0])
            try:
                cache_path.write_bytes(audio_bytes)
            except Exception as e:
                logger.warning("Failed to save audio to cache: %s", type(e).__name__)

            return audio_bytes
    except Exception as e:
        # Never log the key or auth headers
        logger.warning("Sarvam TTS request failed: %s", type(e).__name__)
        return None

