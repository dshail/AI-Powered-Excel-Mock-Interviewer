"""
Configuration settings for the Excel Mock Interviewer.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Encourage UTF-8 on Windows consoles to avoid logging UnicodeEncodeError
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import sys
try:
    # reconfigure available on modern Python to force UTF-8 on stdout/stderr
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    # best-effort; if not available, environment vars still help
    pass


class Settings:
    """Application settings and configuration."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-pro")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    # Use a local/mock LLM for development/testing (streamlit_frontend checks this)
    USE_MOCK_LLM: bool = os.getenv("USE_MOCK_LLM", "True").lower() == "true"
    MOCK_LLM_RESPONSES_FILE: str = os.getenv("MOCK_LLM_RESPONSES_FILE", "data/mock_llm_responses.json")
    
    # FastAPI Configuration
    API_HOST: str = os.getenv("API_HOST", "localhost")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # Streamlit Configuration
    STREAMLIT_HOST: str = os.getenv("STREAMLIT_HOST", "localhost")
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # Interview Configuration
    MAX_QUESTIONS_PER_INTERVIEW: int = 7
    MIN_QUESTIONS_PER_INTERVIEW: int = 5
    QUESTION_TIME_LIMIT: int = 300  # seconds
    ADAPTIVE_DIFFICULTY: bool = True
    
    # Scoring Configuration
    PASSING_SCORE_PERCENTAGE: float = 60.0
    ACCURACY_WEIGHT: float = 0.4
    EXPLANATION_WEIGHT: float = 0.3
    EFFICIENCY_WEIGHT: float = 0.3
    
    # File Paths
    DATA_DIR: str = "data"
    QUESTIONS_DIR: str = f"{DATA_DIR}/questions"
    RUBRICS_DIR: str = f"{DATA_DIR}/rubrics"
    TRANSCRIPTS_DIR: str = f"{DATA_DIR}/transcripts"
    
    # Application Configuration
    APP_TITLE: str = "Excel Mock Interviewer"
    APP_ICON: str = "📊"
    SIDEBAR_LOGO: str = "🎯"
    # ASCII-safe fallbacks for consoles that cannot render emoji
    APP_ICON_SAFE: str = os.getenv("APP_ICON_SAFE", "[APP]")
    SIDEBAR_LOGO_SAFE: str = os.getenv("SIDEBAR_LOGO_SAFE", ">>")
    
    # API Endpoints
    API_BASE_URL: str = f"http://{API_HOST}:{API_PORT}"
    
    # Difficulty Progression Rules
    DIFFICULTY_PROGRESSION: Dict[str, Any] = {
        "basic_to_intermediate_threshold": 7.0,  # out of 10
        "intermediate_to_advanced_threshold": 8.0,
        "regression_threshold": 5.0,  # regress difficulty if score drops
        "max_consecutive_wrong": 2  # max wrong answers before offering hints
    }

    def as_dict(self) -> Dict[str, Any]:
        """Return settings as a plain dict (useful for templates/debug)."""
        return {
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
            "LLM_MODEL": self.LLM_MODEL,
            "LLM_TEMPERATURE": self.LLM_TEMPERATURE,
            "MAX_TOKENS": self.MAX_TOKENS,
            "USE_MOCK_LLM": self.USE_MOCK_LLM,
            "MOCK_LLM_RESPONSES_FILE": self.MOCK_LLM_RESPONSES_FILE,
            "API_HOST": self.API_HOST,
            "API_PORT": self.API_PORT,
            "STREAMLIT_HOST": self.STREAMLIT_HOST,
            "STREAMLIT_PORT": self.STREAMLIT_PORT,
            "APP_TITLE": self.APP_TITLE,
            "APP_ICON": self.APP_ICON,
            "APP_ICON_SAFE": self.APP_ICON_SAFE,
            "SIDEBAR_LOGO": self.SIDEBAR_LOGO,
            "SIDEBAR_LOGO_SAFE": self.SIDEBAR_LOGO_SAFE,
            "API_BASE_URL": self.API_BASE_URL,
        }


settings = Settings()


# Basic validation to avoid surprise runs
import logging
if not settings.USE_MOCK_LLM and not settings.GEMINI_API_KEY:
    logging.warning("USE_MOCK_LLM=False but GEMINI_API_KEY is empty. Set GEMINI_API_KEY in your environment or enable USE_MOCK_LLM for dev.")

  