import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "sudhaar.db"

# Mode: "offline" (templates only) or "live" (Gemini LLM enabled)
DEMO_MODE = os.getenv("DEMO_MODE", "offline")

# Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Product metadata
PRODUCT_NAME = "Sudhaar"
LENDER_NAME = "Nimbus Finance"
DISCLAIMER = "Concept prototype for the Paytm Build for India AI Hackathon. Not the Paytm app."

