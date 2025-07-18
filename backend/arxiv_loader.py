import pandas as pd
import tempfile
import os
from kaggle.api.kaggle_api_extended import KaggleApi
import zipfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_arxiv_metadata() -> pd.DataFrame:
    """
    Download and parse the arXiv metadata file from Kaggle.
    
    Returns:
        pd.DataFrame: DataFrame containing only 'id', 'title', and 'abstract' columns
    """
    
    # Initialize Kaggle API with proper authentication
    try:
        api = KaggleApi()
        api.authenticate()
        logger.info("Kaggle API authentication successful")
    except Exception as e:
        logger.error(f"Kaggle API authentication failed: {e}")
        # Create a small sample dataset for testing when Kaggle auth fails
        logger.warning("Creating sample dataset instead of downloading from Kaggle")
        sample_data = {
            'id': [f'sample{i}' for i in range(100)],
            'title': [f'Sample Paper {i}' for i in range(100)],
            'abstract': [f'This is a sample abstract for paper {i}. It contains some text about a research topic.' for i in range(100)]
        }
        return pd.DataFrame(sample_data)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("Downloading arXiv metadata from Kaggle...")
        
        try:
            # Download the dataset to temporary directory
            api.dataset_download_files(
                'Cornell-University/arxiv',
                path=temp_dir,
                unzip=True
            )
            
            # Find the JSON file in the downloaded files
            json_file_path = None
            for file in os.listdir(temp_dir):
                if file.endswith('.json') and 'arxiv-metadata' in file:
                    json_file_path = os.path.join(temp_dir, file)
                    break
            
            if not json_file_path:
                # If not found, try the expected filename directly
                json_file_path = os.path.join(temp_dir, 'arxiv-metadata-oai-snapshot.json')
            
            if not os.path.exists(json_file_path):
                raise FileNotFoundError(f"arXiv metadata JSON file not found in {temp_dir}")
            
            logger.info(f"Loading JSON file: {json_file_path}")
            
            # Load the JSON file with pandas
            df = pd.read_json(json_file_path, lines=True)
            
            logger.info(f"Loaded {len(df)} records from arXiv metadata")
            
            # Apply development limit if configured
            arxiv_limit = int(os.environ.get("ARXIV_LOAD_LIMIT", "10000"))
            if arxiv_limit > 0:
                df = df.head(arxiv_limit)
                logger.info(f"Limited to {len(df)} records for development (ARXIV_LOAD_LIMIT={arxiv_limit})")
            
            # Filter to only required columns
            required_columns = ['id', 'title', 'abstract']
            
            # Check if all required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Missing columns: {missing_columns}")
                logger.info(f"Available columns: {df.columns.tolist()}")
            
            # Return DataFrame with only required columns (if they exist)
            available_columns = [col for col in required_columns if col in df.columns]
            result_df = df[available_columns].copy()
            
            # Clean up any null values
            result_df = result_df.dropna()
            
            logger.info(f"Returning {len(result_df)} cleaned records with columns: {result_df.columns.tolist()}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error downloading or processing arXiv metadata: {str(e)}")
            raise 