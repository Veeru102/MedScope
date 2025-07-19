#!/usr/bin/env python3
"""
Startup script for the MedPub backend server
This script ensures proper initialization and can be used for local testing
"""

import os
import sys
import logging
import subprocess
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if all requirements are met"""
    logger.info("Checking requirements...")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        return False
    
    # Check if required directories exist
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        logger.info(f"Creating {upload_dir} directory")
        os.makedirs(upload_dir, exist_ok=True)
    
    return True

def download_nltk_data():
    """Download NLTK data if not already present"""
    logger.info("Ensuring NLTK data is available...")
    try:
        result = subprocess.run([sys.executable, "download_nltk.py"], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logger.info("NLTK data check completed successfully")
        else:
            logger.warning(f"NLTK data check had issues: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.warning("NLTK data download timed out")
    except Exception as e:
        logger.error(f"Error checking NLTK data: {e}")

def start_server():
    """Start the FastAPI server"""
    logger.info("Starting FastAPI server...")
    
    # Set environment variables for better performance
    os.environ.setdefault("PYTHONPATH", os.getcwd())
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("ARXIV_LOAD_LIMIT", "50")
    
    # Start the server
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", os.environ.get("PORT", "8000"),
            "--timeout-keep-alive", "120",
            "--log-level", "info"
        ]
        
        logger.info(f"Starting server with command: {' '.join(cmd)}")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    logger.info("=== MedPub Backend Startup ===")
    
    # Change to backend directory if not already there
    if not os.path.exists("main.py"):
        if os.path.exists("backend/main.py"):
            os.chdir("backend")
            logger.info("Changed to backend directory")
        else:
            logger.error("Could not find main.py file")
            return False
    
    # Check requirements
    if not check_requirements():
        logger.error("Requirements check failed")
        return False
    
    # Download NLTK data
    download_nltk_data()
    
    # Start server
    return start_server()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 