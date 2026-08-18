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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-flash-latest")

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
USER_NAME = os.getenv("USER_NAME", "RAVIT")
LANGUAGE = os.getenv("LANGUAGE", "en") # 'en', 'ta', 'si'

# Workspace Path for sandboxed file management & code execution
WORKSPACE_DIR = BASE_DIR / "workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

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


