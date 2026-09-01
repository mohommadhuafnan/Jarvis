import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from root or backend directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# AI Config - Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
# Ensure both environment variables are set in process for child libraries (LiveKit / GenAI)
if GOOGLE_API_KEY and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
if GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
LIVE_MODEL = os.getenv("LIVE_MODEL", os.getenv("DEFAULT_LIVE_MODEL", "gemini-3.1-flash-live-preview"))

# LiveKit Cloud Realtime Voice Configuration (SERVER-ONLY: Never expose secrets to frontend)
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

# Google OAuth Config for Gmail & Calendar
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
GOOGLE_AUTH_URI = os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")

# Assistant Identity & Voice Config
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "JARVIS")
WAKE_WORD = os.getenv("WAKE_WORD", "Jarvis")
WAKE_PHRASE = os.getenv("WAKE_PHRASE", "Hello JARVIS")
WAKE_WORD_SENSITIVITY = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.5"))
INACTIVITY_TIMEOUT_SECS = int(os.getenv("INACTIVITY_TIMEOUT_SECS", "30"))
USER_NAME = os.getenv("USER_NAME", "RAVIT")
LANGUAGE = os.getenv("LANGUAGE", "en") # 'en', 'ta', 'si'
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "Puck")

# Workspace Path for sandboxed file management & code execution
WORKSPACE_DIR = BASE_DIR / "workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# Logs & Single-Instance Lock Paths
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOGS_DIR / "jarvis.log"
INSTANCE_LOCK_PATH = BASE_DIR / "jarvis_instance.lock"

# Database
DB_PATH = BASE_DIR / "jarvis_data.db"

# MongoDB Database Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "jarvis")

# VALSEA Voice Intelligence Configuration
VALSEA_API_KEY = os.getenv("VALSEA_API_KEY", "")
VALSEA_BASE_URL = os.getenv("VALSEA_BASE_URL", "https://api.valsea.ai/v1")

def mask_secret(secret: str, show_chars: int = 4) -> str:
    """Safely mask connection strings or keys for logs and diagnostics."""
    if not secret:
        return "<not-set>"
    if len(secret) <= show_chars * 2:
        return "***"
    return f"{secret[:show_chars]}...{secret[-show_chars:]}"

def is_livekit_configured() -> bool:
    """Check if all LiveKit required credentials are present."""
    return bool(LIVEKIT_URL and LIVEKIT_API_KEY and LIVEKIT_API_SECRET)

def is_gemini_configured() -> bool:
    """Check if Gemini API key is configured."""
    return bool(GOOGLE_API_KEY or GEMINI_API_KEY)
