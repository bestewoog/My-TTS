import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VOICE_DIR = DATA_DIR / "voice_files"
MODEL_DIR = DATA_DIR / "models"
OUTPUT_DIR = DATA_DIR / "outputs"

# Create directories
VOICE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = "sqlite:///./wadio.db"

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "wadio-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Admin
ADMIN_EMAIL = "palsuseo@gmail.com"  # Set admin email to auto-approve

# Qwen3-TTS Model
QWEN_MODEL_PATH = os.getenv("QWEN_MODEL_PATH", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
QWEN_DEVICE = "cuda:0"
QWEN_DTYPE = "bfloat16"

# Server
API_HOST = "0.0.0.0"
API_PORT = 8000
UI_HOST = "0.0.0.0"
UI_PORT = 7860
