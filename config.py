import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==== GENERAL SETTINGS ====
# Flask secret key (change in production)
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")

# ==== GEMINI / LLM SETTINGS ====
# Set environment variable GOOGLE_API_KEY with your Gemini API key.
# Valid model names: gemini-pro, gemini-1.5-pro, gemini-1.5-flash-latest
# Using gemini-pro as default (most stable and widely available)
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-pro")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
# ==== GOOGLE OAUTH SETTINGS (for Meet + real invites) ====
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")

# Where to store OAuth tokens after user authorizes once
GOOGLE_OAUTH_TOKEN_FILE = os.environ.get(
    "GOOGLE_OAUTH_TOKEN_FILE", "credentials/token.json"
)
# ==== GOOGLE CALENDAR SETTINGS ====
# Calendar to use (owner calendar)
# REQUIRED: Set GOOGLE_CALENDAR_ID in .env file
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID")
if not CALENDAR_ID:
    raise ValueError(
        "GOOGLE_CALENDAR_ID environment variable is required. "
        "Set it in your .env file or as an environment variable."
    )

# Default timezone for events (your business timezone)
DEFAULT_TIMEZONE = os.environ.get("DEFAULT_TIMEZONE", "Asia/Kolkata")
