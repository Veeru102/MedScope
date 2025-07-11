#!/usr/bin/env python3
"""
Build FAISS index from arXiv dataset for similarity search.
This script processes a CSV file containing arXiv paper metadata,
generates embeddings, and creates a searchable FAISS index.
"""

import os
import sys
import pandas as pd
import numpy as np
import faiss
import json
import sqlite3
from typing import List, Dict, Optional
import logging
from tqdm import tqdm
import argparse

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArxivIndexBuilder:
    def __init__(self, 
                 csv_path: str,
                 index_path: str = "faiss_index/arxiv.index",
                 metadata_path: str = "data/metadata.db",
                 embedding_model: str = "openai",
                 batch_size: int = 100,
                 max_papers: int = 1000):
        """
        Initialize the ArXiv index builder.
        
        Args:
            csv_path: Path to the arXiv CSV file
            index_path: Path to save the FAISS index
            metadata_path: Path to save the metadata database
            embedding_model: Either "openai" or "huggingface"
            batch_size: Number of papers to process at once
            max_papers: Maximum number of papers to index
        """
        self.csv_path = csv_path
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.batch_size = batch_size
        self.max_papers = max_papers
        
        # Initialize embeddings
        if embedding_model == "openai":
            self.embeddings = OpenAIEmbeddings()
            self.embedding_dim = 1536  # OpenAI ada-002 dimension
        else:
            # Use sentence-transformers model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            self.embedding_dim = 384  # MiniLM dimension
        
        logger.info(f"Using {embedding_model} embeddings with dimension {self.embedding_dim}")
        
    def load_and_filter_data(self) -> pd.DataFrame:
        """Load and filter the arXiv dataset."""
        logger.info(f"Loading data from {self.csv_path}")
        
        # Load CSV
        df = pd.read_csv(self.csv_path)
        logger.info(f"Loaded {len(df)} papers")
        
        # Check available columns
        logger.info(f"Available columns: {df.columns.tolist()}")
        
        # Filter by category if available
        if 'categories' in df.columns:
            # Filter for AI/ML related categories
            ml_categories = ['cs.AI', 'cs.LG', 'stat.ML', 'cs.CV', 'cs.CL']
            mask = df['categories'].str.contains('|'.join(ml_categories), na=False)
            filtered_df = df[mask]
            logger.info(f"Filtered to {len(filtered_df)} ML/AI papers")
        else:
            filtered_df = df
            
        # Limit to max_papers
        if len(filtered_df) > self.max_papers:
            filtered_df = filtered_df.sample(n=self.max_papers, random_state=42)
            logger.info(f"Sampled {self.max_papers} papers")
            
        # Ensure required columns exist
        required_columns = ['title', 'abstract']
        for col in required_columns:
            if col not in filtered_df.columns:
                raise ValueError(f"Required column '{col}' not found in CSV")
                
        # Clean data
        filtered_df = filtered_df.dropna(subset=required_columns)
        logger.info(f"Final dataset size: {len(filtered_df)} papers")
        
        return filtered_df
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        embeddings = self.embeddings.embed_documents(texts)
        return np.array(embeddings, dtype='float32')
    
    def build_index(self):
        """Build the FAISS index and save metadata."""
        # Load data
        df = self.load_and_filter_data()
        
        # Prepare texts for embedding (title + abstract)
        logger.info("Preparing texts for embedding...")
        texts = []
        for _, row in df.iterrows():
            text = f"{row['title']}\n\n{row['abstract']}"
            texts.append(text)
        
        # Generate embeddings in batches
        logger.info("Generating embeddings...")
        all_embeddings = []
        
        for i in tqdm(range(0, len(texts), self.batch_size)):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self.create_embeddings(batch_texts)
            all_embeddings.append(batch_embeddings)
            
        # Combine all embeddings
        embeddings_matrix = np.vstack(all_embeddings)
        logger.info(f"Generated embeddings shape: {embeddings_matrix.shape}")
        
        # Create FAISS index
        logger.info("Building FAISS index...")
        index = faiss.IndexFlatL2(self.embedding_dim)
        index.add(embeddings_matrix)
        
        # Save FAISS index
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(index, self.index_path)
        logger.info(f"Saved FAISS index to {self.index_path}")
        
        # Save metadata to SQLite
        self.save_metadata(df)
        
    def save_metadata(self, df: pd.DataFrame):
        """Save paper metadata to SQLite database."""
        logger.info("Saving metadata to database...")
        
        # Create database directory
        os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
        
        # Connect to SQLite
        conn = sqlite3.connect(self.metadata_path)
        
        # Create table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                abstract TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                categories TEXT,
                arxiv_id TEXT
            )
        ''')
        
        # Clear existing data
        conn.execute('DELETE FROM papers')
        
        # Insert data
        for idx, row in df.iterrows():
            conn.execute('''
                INSERT INTO papers (id, title, abstract, authors, year, categories, arxiv_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                idx,
                row.get('title', ''),
                row.get('abstract', ''),
                row.get('authors', ''),
                int(row.get('year', 0)) if pd.notna(row.get('year')) else None,
                row.get('categories', ''),
                row.get('id', '')  # arXiv ID if available
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved metadata for {len(df)} papers to {self.metadata_path}")

def main():
    parser = argparse.ArgumentParser(description='Build FAISS index from arXiv dataset')
    parser.add_argument('--csv', type=str, default='data/arxiv_sample.csv',
                        help='Path to arXiv CSV file')
    parser.add_argument('--model', type=str, default='openai',
                        choices=['openai', 'huggingface'],
                        help='Embedding model to use')
    parser.add_argument('--batch-size', type=int, default=100,
                        help='Batch size for embedding generation')
    parser.add_argument('--max-papers', type=int, default=1000,
                        help='Maximum number of papers to index')
    
    args = parser.parse_args()
    
    # Check if CSV exists
    if not os.path.exists(args.csv):
        print("ERROR: arxiv_sample.csv is missing, malformed, or contains too few entries (<100). "
              "Please provide a valid dataset before proceeding.")
        sys.exit(1)

    # Validate dataset before proceeding
    try:
        df_validation = pd.read_csv(args.csv)
    except Exception:
        print("ERROR: arxiv_sample.csv is missing, malformed, or contains too few entries (<100). "
              "Please provide a valid dataset before proceeding.")
        sys.exit(1)

    required_cols = {"id", "title", "abstract", "authors", "year", "categories"}
    if not required_cols.issubset(set(df_validation.columns)) or len(df_validation) < 100:
        print("ERROR: arxiv_sample.csv is missing, malformed, or contains too few entries (<100). "
              "Please provide a valid dataset before proceeding.")
        sys.exit(1)

    logger.info(f"Loaded arxiv_sample.csv with {len(df_validation)} valid entries.")
    
    # Build index
    builder = ArxivIndexBuilder(
        csv_path=args.csv,
        embedding_model=args.model,
        batch_size=args.batch_size,
        max_papers=args.max_papers
    )
    
    try:
        builder.build_index()
        logger.info("Index building completed successfully!")
    except Exception as e:
        logger.error(f"Error building index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 