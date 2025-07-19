import nltk
import ssl
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

def download_nltk_data():
    """Download NLTK data only if not already present"""
    try:
        # Check if punkt data is already available
        nltk.data.find('tokenizers/punkt')
        logger.info("NLTK punkt data already available, skipping download")
        return True
    except LookupError:
        logger.info("NLTK punkt data not found, downloading...")
        try:
            nltk.download('punkt', quiet=False)
            logger.info("NLTK punkt data downloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to download NLTK punkt data: {e}")
            return False

if __name__ == "__main__":
    logger.info("Starting NLTK data download process...")
    success = download_nltk_data()
    if success:
        logger.info("NLTK data download completed successfully")
    else:
        logger.error("NLTK data download failed")
        exit(1) 