import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
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

# Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Mode: "live" if explicitly requested or API key present; defaults to "live" when API key is set, else "offline"
DEMO_MODE = os.getenv("DEMO_MODE", "live" if GEMINI_API_KEY else "offline")

# Product metadata
PRODUCT_NAME = "Sudhaar"
LENDER_NAME = "Nimbus Finance"
DISCLAIMER = "Concept prototype for the Paytm Build for India AI Hackathon. Not the Paytm app."
