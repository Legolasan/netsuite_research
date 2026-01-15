"""
NetSuite Documentation Search & Chat - FastAPI Web Application

A modern dashboard for searching and chatting with vectorized NetSuite documentation.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "vectorization"))

from services.search import SearchService
from services.chat import ChatService


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None
    object_type: Optional[str] = None


class SearchResultItem(BaseModel):
    chunk_id: str
    score: float
    text: str
    source_file: str
    doc_category: str
    object_type: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_results: int


class ChatRequest(BaseModel):
    message: str
    top_k: int = 5
    category: Optional[str] = None


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    model: str


class StatsResponse(BaseModel):
    index_name: str
    total_vectors: int
    dimension: int
    categories: List[str]
    status: str


# Services (initialized on startup)
search_service: Optional[SearchService] = None
chat_service: Optional[ChatService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global search_service, chat_service
    
    try:
        search_service = SearchService()
        chat_service = ChatService()
        print("✓ Services initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize services: {e}")
        print("  The app will run but search/chat will not work without API keys.")
    
    yield
    
    # Cleanup (if needed)
    print("Shutting down services...")


# Create FastAPI app
app = FastAPI(
    title="NetSuite Documentation Search",
    description="Search and chat with NetSuite API documentation",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "NetSuite Docs"
    })


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {
        "status": "healthy",
        "services": {
            "search": search_service is not None,
            "chat": chat_service is not None
        }
    }


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Perform semantic search over documentation."""
    if not search_service:
        raise HTTPException(
            status_code=503,
            detail="Search service not initialized. Check API keys."
        )
    
    try:
        # Build filter
        filter_dict = {}
        if request.category:
            filter_dict["doc_category"] = {"$eq": request.category}
        if request.object_type:
            filter_dict["object_type"] = {"$eq": request.object_type}
        
        results = search_service.search(
            query=request.query,
            top_k=request.top_k,
            filter=filter_dict if filter_dict else None
        )
        
        return SearchResponse(
            query=results.query,
            results=[
                SearchResultItem(
                    chunk_id=r.chunk_id,
                    score=r.score,
                    text=r.text,
                    source_file=r.source_file,
                    doc_category=r.doc_category,
                    object_type=r.object_type
                )
                for r in results.results
            ],
            total_results=results.total_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with documentation using RAG."""
    if not chat_service:
        raise HTTPException(
            status_code=503,
            detail="Chat service not initialized. Check API keys."
        )
    
    try:
        # Build filter
        filter_dict = {}
        if request.category:
            filter_dict["doc_category"] = {"$eq": request.category}
        
        response = chat_service.ask(
            question=request.message,
            top_k=request.top_k,
            filter=filter_dict if filter_dict else None
        )
        
        return ChatResponse(
            question=response.question,
            answer=response.answer,
            sources=response.sources,
            model=response.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get index statistics."""
    if not search_service:
        raise HTTPException(
            status_code=503,
            detail="Search service not initialized. Check API keys."
        )
    
    try:
        stats = search_service.get_index_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
async def get_categories():
    """Get available document categories."""
    return {
        "categories": [
            {"id": "SOAP", "label": "SOAP API", "description": "SOAP Web Services documentation"},
            {"id": "REST", "label": "REST API", "description": "REST Web Services documentation"},
            {"id": "GOVERNANCE", "label": "Governance", "description": "API limits and governance"},
            {"id": "PERMISSION", "label": "Permissions", "description": "Roles and permissions"},
            {"id": "RECORD", "label": "Records", "description": "Record types and entities"},
            {"id": "SEARCH", "label": "Search", "description": "Search and SuiteQL"},
            {"id": "CUSTOM", "label": "Customization", "description": "Custom records and fields"},
            {"id": "GENERAL", "label": "General", "description": "General documentation"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
