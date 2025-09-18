"""
Main application launcher for Excel Mock Interviewer.
Starts both FastAPI backend and Streamlit frontend.
"""

import os
import sys
import subprocess
import logging
import time
import signal
from pathlib import Path
from multiprocessing import Process

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('excel_interviewer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment is properly configured."""
    issues = []
    
    # Check Gemini API key
    if not settings.GEMINI_API_KEY:
        issues.append("GEMINI_API_KEY environment variable not set")
    
    # Check required directories exist
    required_dirs = [
        settings.DATA_DIR,
        settings.QUESTIONS_DIR, 
        settings.RUBRICS_DIR,
        settings.TRANSCRIPTS_DIR
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    if issues:
        logger.error("Environment configuration issues:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False
    
    logger.info("Environment check passed ✓")
    return True

def start_fastapi_backend():
    """Start the FastAPI backend server."""
    logger.info("Starting FastAPI backend...")
    try:
        cmd = [
            sys.executable, "fastapi_backend.py"
        ]
        subprocess.run(cmd)
    except Exception as e:
        logger.error(f"Failed to start FastAPI backend: {e}")

def start_streamlit_frontend():
    """Start the Streamlit frontend."""
    logger.info("Starting Streamlit frontend...")
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_frontend.py",
            "--server.port", str(settings.STREAMLIT_PORT),
            "--server.address", settings.STREAMLIT_HOST
        ]
        subprocess.run(cmd)
    except Exception as e:
        logger.error(f"Failed to start Streamlit frontend: {e}")

def main():
    """Main application entry point."""
    logger.info("Starting Excel Mock Interviewer with Gemini AI...")
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Please fix issues before continuing.")
        logger.error("Make sure to set your GEMINI_API_KEY in a .env file")
        return 1
    
    try:
        # Start FastAPI backend in a separate process
        backend_process = Process(target=start_fastapi_backend)
        backend_process.start()
        
        # Wait a moment for backend to start
        time.sleep(3)
        
        logger.info("=" * 60)
        logger.info("🚀 Excel Mock Interviewer Started Successfully!")
        logger.info("=" * 60)
        logger.info(f"📡 FastAPI Backend: http://{settings.API_HOST}:{settings.API_PORT}")
        logger.info(f"🖥️  Streamlit Frontend: http://{settings.STREAMLIT_HOST}:{settings.STREAMLIT_PORT}")
        logger.info("=" * 60)
        logger.info("To stop the application, press Ctrl+C")
        logger.info("=" * 60)
        
        # Start Streamlit frontend (this will block)
        start_streamlit_frontend()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        backend_process.terminate()
        backend_process.join()
        logger.info("Application stopped")
        return 0
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        if 'backend_process' in locals():
            backend_process.terminate()
            backend_process.join()
        return 1

if __name__ == "__main__":
    sys.exit(main())