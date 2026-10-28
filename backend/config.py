"""Central configuration, read from environment (see .env.example)."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Minimal .env loader (KEY=VALUE lines); does not override real env vars."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()

# --- Gnani ---
GNANI_API_KEY = os.getenv("GNANI_API_KEY", "")
GNANI_BASE_URL = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai")
GNANI_STT_MODEL = os.getenv("GNANI_STT_MODEL", "gnani-prisma-v2.5")
GNANI_TTS_MODEL = os.getenv("GNANI_TTS_MODEL", "timbre-v3.0")
GNANI_TTS_VOICE_FEMALE = os.getenv("GNANI_TTS_VOICE_FEMALE", "Shivani")
GNANI_TTS_VOICE_MALE = os.getenv("GNANI_TTS_VOICE_MALE", "Avinash")
GNANI_BOT_VOICE = os.getenv("GNANI_BOT_VOICE", "Kalpana")
GNANI_CONCURRENCY = int(os.getenv("GNANI_CONCURRENCY", "1"))

# --- LLM ---
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_MOCK = os.getenv("LLM_MOCK", "0") in ("1", "true", "TRUE")

# --- Runner ---
CREDIT_LIMIT = int(os.getenv("VOICEQA_CREDIT_LIMIT", "800"))
MAX_CONCURRENT_CALLS = int(os.getenv("VOICEQA_MAX_CONCURRENT_CALLS", "5"))
MAX_TURNS = int(os.getenv("VOICEQA_MAX_TURNS", "10"))
CALL_TIMEOUT_S = int(os.getenv("VOICEQA_CALL_TIMEOUT_S", "180"))

# --- Bolo Khata ---
# Google Sign-In client ID (public value; goes in frontend as NEXT_PUBLIC_GOOGLE_CLIENT_ID too)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
# Telegram bot token from @BotFather; empty disables receipt sending (status shown in UI)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Frontend origin for CORS + Sign-In
SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")
# 1 = allow /api/auth/dev local login (creates a demo owner; for local runs only)
BOLO_DEV_LOGIN = os.getenv("BOLO_DEV_LOGIN", "1" if not GOOGLE_CLIENT_ID else "0") in ("1", "true")
# Default spoken language hint for STT
STT_LANGUAGE = os.getenv("BOLO_STT_LANGUAGE", "hi-IN")

# --- Data ---
DB_PATH = REPO_ROOT / os.getenv("VOICEQA_DB_PATH", "data/voiceqa.db")
AUDIO_DIR = REPO_ROOT / os.getenv("VOICEQA_AUDIO_DIR", "data/audio")
NOISE_DIR = REPO_ROOT / os.getenv("VOICEQA_NOISE_DIR", "data/noise")
PROMPTS_DIR = REPO_ROOT / "prompts"

# --- Gnani voice catalog per persona language (timbre-v3.0 voices speak all languages;
#     timbre-v2.5 voices are language-bound). Gender -> voice name. ---
LANG_TO_VOICES: dict[str, dict[str, str]] = {
    "hi": {"female": GNANI_TTS_VOICE_FEMALE, "male": GNANI_TTS_VOICE_MALE},
    "ta": {"female": GNANI_TTS_VOICE_FEMALE, "male": GNANI_TTS_VOICE_MALE},
    "mr": {"female": GNANI_TTS_VOICE_FEMALE, "male": GNANI_TTS_VOICE_MALE},
    "kn": {"female": GNANI_TTS_VOICE_FEMALE, "male": GNANI_TTS_VOICE_MALE},
    "en": {"female": "Lakshmi", "male": "Prakash"},
}

# Persona language label -> Gnani codes (STT language_code / TTS language)
LANG_CODES: dict[str, str] = {
    "hi": "hi-IN", "ta": "ta-IN", "mr": "mr-IN", "kn": "kn-IN",
    "te": "te-IN", "bn": "bn-IN", "en": "en-IN",
}
SUPPORTED_PERSONA_LANGS = ["hi", "ta", "mr", "kn", "en"]


def ensure_dirs() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    NOISE_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def db_url() -> str:
    return f"sqlite:///{DB_PATH}"
