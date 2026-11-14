import os

# Ensure tests run deterministically in offline mode
os.environ["DEMO_MODE"] = "offline"
os.environ["GEMINI_API_KEY"] = ""
