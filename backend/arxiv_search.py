import asyncio
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import threading
from datetime import datetime

from arxiv_loader import load_arxiv_metadata
from arxiv_indexer import build_faiss_index, search_similar_papers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request models
class ArxivSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    limit: Optional[int] = Field(5, ge=1, le=20, description="Number of results to return")

class ArxivSearchResponse(BaseModel):
    papers: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float
    query: str

class ArxivStatusResponse(BaseModel):
    status: str
    total_papers: int
    index_ready: bool
    last_updated: Optional[str]

# Global state for arXiv search
class ArxivSearchState:
    def __init__(self):
        self.faiss_index: Optional[faiss.IndexFlatIP] = None
        self.metadata_df: Optional[pd.DataFrame] = None
        self.sentence_model: Optional[SentenceTransformer] = None
        self.is_initialized = False
        self.is_loading = False
        self.last_updated: Optional[str] = None
        self.total_papers = 0
        self.lock = threading.Lock()

# Global instance
arxiv_state = ArxivSearchState()

# FastAPI router
router = APIRouter(prefix="/arxiv", tags=["arxiv"])

async def initialize_arxiv_search():
    """
    Initialize arXiv search system by loading metadata and building FAISS index
    """
    global arxiv_state
    
    with arxiv_state.lock:
        if arxiv_state.is_initialized or arxiv_state.is_loading:
            logger.info("ArXiv search already initialized or loading")
            return
        
        arxiv_state.is_loading = True
        logger.info("Starting arXiv search initialization...")
        
    try:
        # Pre-download and cache the model to avoid timeout issues
        logger.info("Pre-downloading SentenceTransformer model...")
        SentenceTransformer("all-MiniLM-L6-v2", cache_folder="/tmp/sentence_transformers")
        
        # Load arXiv metadata
        logger.info("Loading arXiv metadata from Kaggle...")
        metadata_df = load_arxiv_metadata()
        
        if metadata_df.empty:
            logger.warning("No arXiv metadata loaded")
            return
        
        logger.info(f"Loaded {len(metadata_df)} arXiv papers")
        
        # Build FAISS index
        logger.info("Building FAISS index for arXiv papers...")
        faiss_index, processed_df = build_faiss_index(metadata_df)
        
        # Load sentence transformer model
        logger.info("Loading SentenceTransformer model...")
        sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Update global state
        with arxiv_state.lock:
            arxiv_state.faiss_index = faiss_index
            arxiv_state.metadata_df = processed_df
            arxiv_state.sentence_model = sentence_model
            arxiv_state.is_initialized = True
            arxiv_state.is_loading = False
            arxiv_state.last_updated = datetime.now().isoformat()
            arxiv_state.total_papers = len(processed_df)
        
        logger.info(f"ArXiv search initialized successfully with {len(processed_df)} papers")
        
    except Exception as e:
        logger.error(f"Failed to initialize arXiv search: {e}")
        with arxiv_state.lock:
            arxiv_state.is_loading = False
        raise

@router.post("/search", response_model=ArxivSearchResponse)
async def search_arxiv_papers(request: ArxivSearchRequest):
    """
    Search for similar arXiv papers using semantic similarity
    """
    logger.info(f"ArXiv search request: '{request.query}' (limit: {request.limit})")
    
    # Check if system is initialized
    if not arxiv_state.is_initialized:
        if arxiv_state.is_loading:
            raise HTTPException(
                status_code=503, 
                detail="ArXiv search system is still loading. Please try again in a moment."
            )
        else:
            raise HTTPException(
                status_code=503, 
                detail="ArXiv search system not initialized. Please contact administrator."
            )
    
    # Validate query
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        start_time = pd.Timestamp.now()
        
        # Search for similar papers
        results_df = search_similar_papers(
            index=arxiv_state.faiss_index,
            metadata_df=arxiv_state.metadata_df,
            query_text=request.query.strip(),
            model=arxiv_state.sentence_model,
            k=request.limit
        )
        
        # Format results
        papers = []
        for _, row in results_df.iterrows():
            paper = {
                "id": row.get("id", ""),
                "title": row.get("title", ""),
                "abstract": row.get("abstract", ""),
                "similarity_score": row.get("similarity_score", 0.0),
                "rank": row.get("rank", 0),
                "arxiv_url": f"https://arxiv.org/abs/{row.get('id', '')}" if row.get("id") else None
            }
            papers.append(paper)
        
        search_time_ms = (pd.Timestamp.now() - start_time).total_seconds() * 1000
        
        logger.info(f"ArXiv search completed in {search_time_ms:.2f}ms, found {len(papers)} results")
        
        return ArxivSearchResponse(
            papers=papers,
            total_found=len(papers),
            search_time_ms=search_time_ms,
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error during arXiv search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/status", response_model=ArxivStatusResponse)
async def get_arxiv_status():
    """
    Get the current status of the arXiv search system
    """
    return ArxivStatusResponse(
        status="ready" if arxiv_state.is_initialized else ("loading" if arxiv_state.is_loading else "not_initialized"),
        total_papers=arxiv_state.total_papers,
        index_ready=arxiv_state.is_initialized,
        last_updated=arxiv_state.last_updated
    )

@router.post("/initialize")
async def trigger_initialization(background_tasks: BackgroundTasks):
    """
    Manually trigger arXiv search initialization (for admin use)
    """
    if arxiv_state.is_initialized:
        return {"message": "ArXiv search already initialized"}
    
    if arxiv_state.is_loading:
        return {"message": "ArXiv search initialization already in progress"}
    
    # Run initialization in background
    background_tasks.add_task(initialize_arxiv_search)
    
    return {"message": "ArXiv search initialization started"}

# Function to be called during FastAPI startup
async def startup_arxiv_search():
    """
    Startup function to initialize arXiv search system
    Call this from your main FastAPI app's startup event
    """
    logger.info("Starting arXiv search initialization during app startup...")
    
    # Run initialization in background to avoid blocking app startup
    asyncio.create_task(initialize_arxiv_search())
    
    logger.info("ArXiv search initialization task created") 