import pandas as pd
import numpy as np
import os
from sentence_transformers import SentenceTransformer
import faiss
import logging
from typing import Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_faiss_index(dataframe: pd.DataFrame) -> Tuple[faiss.IndexFlatIP, pd.DataFrame]:
    """
    Build a FAISS similarity index from arXiv metadata DataFrame.
    
    Args:
        dataframe: DataFrame with 'title' and 'abstract' columns
        
    Returns:
        Tuple of (FAISS index, metadata DataFrame with same order as index)
    """
    
    if dataframe.empty:
        logger.warning("Empty DataFrame provided")
        # Return empty index and DataFrame
        empty_index = faiss.IndexFlatIP(384)  # MiniLM embedding dimension
        return empty_index, dataframe.copy()
    
    # Validate required columns
    required_columns = ['title', 'abstract']
    missing_columns = [col for col in required_columns if col not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Apply development limit to conserve memory
    limit = int(os.environ.get("ARXIV_LOAD_LIMIT", "1000"))
    if limit > 0 and len(dataframe) > limit:
        logger.info(f"Limiting to {limit} papers to conserve memory")
        dataframe = dataframe.head(limit)
    
    logger.info(f"Building FAISS index for {len(dataframe)} papers")
    
    # Clean the data and prepare text for embedding
    clean_df = dataframe.copy()
    clean_df['title'] = clean_df['title'].fillna('')
    clean_df['abstract'] = clean_df['abstract'].fillna('')
    
    # Concatenate title and abstract
    combined_texts = []
    for _, row in clean_df.iterrows():
        # Combine title and abstract with a separator
        combined_text = f"{row['title']} {row['abstract']}"
        combined_texts.append(combined_text.strip())
    
    logger.info("Loading SentenceTransformer model...")
    
    # Load the sentence transformer model with minimal memory footprint
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    
    logger.info("Generating embeddings...")
    
    # Generate embeddings for all texts in smaller batches to reduce memory usage
    embeddings = model.encode(
        combined_texts,
        convert_to_numpy=True,
        show_progress_bar=True,
        batch_size=16  # Smaller batch size to reduce memory usage
    )
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    logger.info(f"Generated {embeddings.shape[0]} embeddings with dimension {embeddings.shape[1]}")
    
    # Create FAISS index (Inner Product for normalized vectors = cosine similarity)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    
    # Add embeddings to index
    index.add(embeddings.astype(np.float32))
    
    logger.info(f"FAISS index built successfully with {index.ntotal} vectors")
    
    # Return index and corresponding metadata
    return index, clean_df.reset_index(drop=True)


def search_similar_papers(index: faiss.IndexFlatIP, 
                         metadata_df: pd.DataFrame, 
                         query_text: str, 
                         model: SentenceTransformer = None, 
                         k: int = 10) -> pd.DataFrame:
    """
    Search for similar papers using the FAISS index.
    
    Args:
        index: FAISS index
        metadata_df: DataFrame with paper metadata
        query_text: Text to search for similar papers
        model: Optional pre-loaded SentenceTransformer model
        k: Number of similar papers to return
        
    Returns:
        DataFrame with similar papers and similarity scores
    """
    
    if model is None:
        logger.info("Loading SentenceTransformer model for search...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Generate query embedding
    query_embedding = model.encode([query_text], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    
    # Search for similar papers
    similarities, indices = index.search(query_embedding.astype(np.float32), k)
    
    # Prepare results
    results = []
    for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
        if idx < len(metadata_df):
            paper_info = metadata_df.iloc[idx].to_dict()
            paper_info['similarity_score'] = float(similarity)
            paper_info['rank'] = i + 1
            results.append(paper_info)
    
    return pd.DataFrame(results) 