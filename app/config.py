import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-ai-copilot")
    TEMPLATES_AUTO_RELOAD = True
    
    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Storage Paths
    UPLOAD_FOLDER = BASE_DIR / "data" / "pdfs"
    CHROMA_PERSIST_DIR = BASE_DIR / "data" / "vectordb"
    METADATA_FILE = BASE_DIR / "data" / "papers_metadata.json"
    
    # Upload limits: 50MB
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf"}

# Ensure required data directories exist
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
Config.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
