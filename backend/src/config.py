import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_CACHE_DIR = DATA_DIR / "audio_cache"
DB_PATH = BASE_DIR / "sudhaar.db"

# Simple auto-loader for .env from project root or backend
for env_path in [ROOT_DIR / ".env", BASE_DIR / ".env"]:
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v

# Gemini settings: gemini-3.5-flash-lite is the active fast model on v1beta
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Sarvam settings: bulbul:v3 for natural Indic TTS
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

# Mode: defaults to "live" if API key present, else "offline"
DEMO_MODE = os.getenv("DEMO_MODE", "live" if GEMINI_API_KEY else "offline")

# Product metadata
PRODUCT_NAME = "Sudhaar"
LENDER_NAME = "Nimbus Finance"
DISCLAIMER = "Concept prototype for the Paytm Build for India AI Hackathon. Not the Paytm app."
