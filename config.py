"""
Configuration module - Load environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    # Server
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # OCR Configuration
    OCR_LANG = ["en"]  # Languages to recognize
    OCR_USE_ANGLE_CLS = True  # Use angle classification for rotation
    OCR_SHOW_LOG = False  # Suppress PaddleOCR logs

    # Processing
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB max
    TIMEOUT_SECONDS = 30  # Request timeout

    # Preprocessing
    CONTRAST_THRESHOLD = 1.5  # Image contrast enhancement
    DENOISE_STRENGTH = 10  # Non-local means denoising

    # Validation
    AMOUNT_TOLERANCE = 0.05  # 5% tolerance for amount = qty × rate
    CONFIDENCE_MIN = 0.5  # Minimum confidence score

    # Paths
    BASE_DIR = Path(__file__).parent.parent
    TEMP_DIR = BASE_DIR / "temp"

    @classmethod
    def ensure_paths(cls):
        """Create necessary directories"""
        cls.TEMP_DIR.mkdir(exist_ok=True)

# Initialize configuration
Config.ensure_paths()
