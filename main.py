"""
SAVR Ranking Intelligence API
A standalone service for ranking grocery products based on relevance
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SAVR Ranking Intelligence API",
    description="Ranks grocery products by relevance without accessing main database",
    version="1.0.0"
)

# Configure CORS (allows your main app to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Add your production URLs later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import the ranking engine (you'll create this next)
from ranking_engine import RankingEngine

# Initialize the engine
engine = RankingEngine()

# Data models
class ProductInput(BaseModel):
    """Product information for ranking"""
    name: str
    brand: str = ""
    size: str = ""
    category: Optional[str] = None
    price: Optional[float] = None

class RankingRequest(BaseModel):
    """API request format"""
    search_term: str
    products: List[ProductInput]
    store_name: Optional[str] = None

class RankingResponse(BaseModel):
    """API response format"""
    scores: List[Dict]
    metadata: Dict

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SAVR Ranking Intelligence",
        "version": "1.0.0"
    }

@app.post("/rank", response_model=RankingResponse)
async def rank_products(request: RankingRequest):
    """
    Main ranking endpoint
    Returns relevance scores for each product
    """
    start_time = time.time()
    
    try:
        # Convert products to dicts for processing
        products_data = [p.dict() for p in request.products]
        
        # Get rankings from engine
        scores = engine.score_products(
            search_term=request.search_term,
            products=products_data,
            store_name=request.store_name
        )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        return RankingResponse(
            scores=scores,
            metadata={
                "model_version": engine.version,
                "processing_time_ms": processing_time,
                "products_analyzed": len(request.products)
            }
        )
    except Exception as e:
        logger.error(f"Ranking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "engine_loaded": engine.is_loaded,
        "categories_count": len(engine.categories),
        "version": engine.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
