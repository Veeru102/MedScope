"""
ArXiv paper similarity search service.
Provides functionality to find similar papers from the indexed arXiv dataset.
"""

import os
import faiss
import numpy as np
import sqlite3
from typing import List, Dict, Optional
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class ArxivSearchService:
    def __init__(self, 
                 index_path: str = "faiss_index/arxiv.index",
                 metadata_path: str = "data/metadata.db",
                 embedding_model: str = "openai"):
        """
        Initialize the ArXiv search service.
        
        Args:
            index_path: Path to the FAISS index
            metadata_path: Path to the metadata database
            embedding_model: Either "openai" or "huggingface"
        """
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # Initialize embeddings (must match what was used to build index)
        if embedding_model == "openai":
            self.embeddings = OpenAIEmbeddings()
        else:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        
        # Load FAISS index
        self.index = None
        self.load_index()
        
    def load_index(self):
        """Load the FAISS index from disk."""
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
                self.index = None
        else:
            logger.warning(f"FAISS index not found at {self.index_path}")
            
    def search_similar_papers(self, 
                            query_text: str, 
                            k: int = 3,
                            return_scores: bool = True) -> List[Dict]:
        """
        Search for similar papers based on query text.
        
        Args:
            query_text: Text to search for (e.g., paper summary or abstract)
            k: Number of similar papers to return
            return_scores: Whether to include similarity scores
            
        Returns:
            List of dictionaries containing paper metadata and scores
        """
        if self.index is None:
            logger.error("FAISS index not loaded")
            return []
            
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query_text)
            query_vector = np.array([query_embedding], dtype='float32')
            
            # Search in FAISS
            distances, indices = self.index.search(query_vector, k)
            
            # Fetch metadata for results
            results = []
            conn = sqlite3.connect(self.metadata_path)
            conn.row_factory = sqlite3.Row
            
            for idx, (distance, paper_idx) in enumerate(zip(distances[0], indices[0])):
                if paper_idx == -1:  # FAISS returns -1 for not found
                    continue
                    
                cursor = conn.execute(
                    'SELECT * FROM papers WHERE id = ?', 
                    (int(paper_idx),)
                )
                paper = cursor.fetchone()
                
                if paper:
                    result = {
                        'title': paper['title'],
                        'abstract': paper['abstract'],
                        'authors': paper['authors'],
                        'year': paper['year'],
                        'categories': paper['categories'],
                        'arxiv_id': paper['arxiv_id'],
                        'rank': idx + 1
                    }
                    
                    if return_scores:
                        # Convert L2 distance to similarity score (0-1)
                        # Lower distance = higher similarity
                        similarity = 1 / (1 + float(distance))
                        result['similarity_score'] = similarity
                        
                    results.append(result)
                    
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar papers: {e}")
            return []
    
    def get_arxiv_url(self, arxiv_id: str) -> str:
        """Generate arXiv URL from paper ID."""
        if arxiv_id:
            # Handle different ID formats
            if '/' in arxiv_id:  # Old format like 'cs.AI/0001234'
                return f"https://arxiv.org/abs/{arxiv_id}"
            else:  # New format like '1234.56789'
                return f"https://arxiv.org/abs/{arxiv_id}"
        return ""
    
    def format_results_for_display(self, results: List[Dict]) -> List[Dict]:
        """Format search results for frontend display."""
        formatted = []
        for paper in results:
            # Truncate abstract for display
            abstract_snippet = paper['abstract'][:200] + "..." if len(paper['abstract']) > 200 else paper['abstract']
            
            formatted.append({
                'title': paper['title'],
                'authors': paper['authors'] or 'Unknown',
                'year': paper['year'] or 'N/A',
                'abstract_snippet': abstract_snippet,
                'categories': paper['categories'] or 'Uncategorized',
                'similarity_score': paper.get('similarity_score', 0),
                'arxiv_url': self.get_arxiv_url(paper.get('arxiv_id', ''))
            })
            
        return formatted 