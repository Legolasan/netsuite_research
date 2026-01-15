"""
NetSuite Documentation Search & Chat - FastAPI Web Application

A modern dashboard for searching and chatting with vectorized NetSuite documentation,
with integrated web search capabilities.
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
from services.web_search import WebSearchService
from services.prd import PRDService


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None
    object_type: Optional[str] = None
    include_web: bool = False  # Include cached web results


class SearchResultItem(BaseModel):
    chunk_id: str
    score: float
    text: str
    source_file: str
    doc_category: str
    object_type: str
    source_type: str = "doc"
    url: Optional[str] = None
    title: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_results: int


class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    force_refresh: bool = False  # Force fresh web search


class WebSourceItem(BaseModel):
    name: str
    url: str
    is_cached: bool = False


class WebSearchResponse(BaseModel):
    query: str
    results: List[WebSourceItem]
    total_results: int
    cached_count: int
    fresh_count: int


class ChatRequest(BaseModel):
    message: str
    top_k: int = 5
    category: Optional[str] = None
    include_web: bool = True  # Include web search in RAG
    force_web_refresh: bool = False  # Force fresh web search


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    doc_sources: List[str] = []
    web_sources: List[Dict[str, Any]] = []
    model: str
    include_web: bool = False


class StatsResponse(BaseModel):
    index_name: str
    total_vectors: int
    dimension: int
    categories: List[str]
    status: str


class ServiceStatus(BaseModel):
    search: bool
    chat: bool
    web_search: bool


# Services (initialized on startup)
search_service: Optional[SearchService] = None
chat_service: Optional[ChatService] = None
web_search_service: Optional[WebSearchService] = None
prd_service: Optional[PRDService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global search_service, chat_service, web_search_service, prd_service
    
    try:
        search_service = SearchService()
        chat_service = ChatService()
        print("✓ Search and Chat services initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize core services: {e}")
    
    try:
        web_search_service = WebSearchService()
        if web_search_service.is_available():
            print("✓ Web Search service initialized")
        else:
            print("⚠ Web Search available (cached only - no Tavily API key)")
    except Exception as e:
        print(f"⚠ Web Search service not available: {e}")
        web_search_service = None
    
    try:
        prd_service = PRDService()
        print("✓ PRD service initialized")
    except Exception as e:
        print(f"⚠ PRD service not available: {e}")
        prd_service = None
    
    yield
    
    print("Shutting down services...")


# Create FastAPI app
app = FastAPI(
    title="NetSuite Documentation Search",
    description="Search and chat with NetSuite API documentation with web search integration",
    version="2.0.0",
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
            "chat": chat_service is not None,
            "web_search": web_search_service is not None and web_search_service.is_available()
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
        
        # Use appropriate search method
        if request.include_web:
            results = search_service.search(
                query=request.query,
                top_k=request.top_k,
                filter=filter_dict if filter_dict else None
            )
        else:
            results = search_service.search_docs_only(
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
                    object_type=r.object_type,
                    source_type=r.source_type,
                    url=r.url,
                    title=r.title
                )
                for r in results.results
            ],
            total_results=results.total_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/web-search", response_model=WebSearchResponse)
async def web_search(request: WebSearchRequest):
    """Perform web search with auto-vectorization."""
    if not web_search_service:
        raise HTTPException(
            status_code=503,
            detail="Web search service not initialized. Check TAVILY_API_KEY."
        )
    
    try:
        results = web_search_service.search(
            query=request.query,
            top_k=request.top_k,
            force_refresh=request.force_refresh
        )
        
        return WebSearchResponse(
            query=results.query,
            results=[
                WebSourceItem(
                    name=r.title,
                    url=r.url,
                    is_cached=r.is_cached
                )
                for r in results.results
            ],
            total_results=results.total_results,
            cached_count=results.cached_count,
            fresh_count=results.fresh_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refresh-web")
async def refresh_web_search(request: WebSearchRequest):
    """Force fresh web search and re-vectorize results."""
    if not web_search_service:
        raise HTTPException(
            status_code=503,
            detail="Web search service not initialized. Check TAVILY_API_KEY."
        )
    
    try:
        results = web_search_service.search(
            query=request.query,
            top_k=request.top_k,
            force_refresh=True
        )
        
        return {
            "message": f"Refreshed {results.fresh_count} web results",
            "query": results.query,
            "fresh_count": results.fresh_count,
            "total_results": results.total_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with documentation using RAG, optionally including web search."""
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
            filter=filter_dict if filter_dict else None,
            include_web=request.include_web,
            force_web_refresh=request.force_web_refresh
        )
        
        return ChatResponse(
            question=response.question,
            answer=response.answer,
            sources=response.sources,
            doc_sources=response.doc_sources,
            web_sources=response.web_sources,
            model=response.model,
            include_web=response.include_web
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
            {"id": "WEB", "label": "Web", "description": "Cached web search results"},
            {"id": "GENERAL", "label": "General", "description": "General documentation"},
        ]
    }


@app.get("/api/web-search-status")
async def web_search_status():
    """Check if web search is available and configured."""
    if not web_search_service:
        return {
            "available": False,
            "has_tavily": False,
            "has_cache": False,
            "message": "Web search service not initialized"
        }
    
    return {
        "available": web_search_service.is_available(),
        "has_tavily": web_search_service.tavily_client is not None,
        "has_cache": web_search_service.index is not None,
        "message": "Web search is fully available" if web_search_service.tavily_client else "Web search available (cached results only)"
    }


# =====================
# PRD API Endpoints
# =====================

@app.get("/api/prd/summary")
async def prd_summary():
    """Get PRD summary data - implementation overview."""
    if not prd_service:
        raise HTTPException(
            status_code=503,
            detail="PRD service not initialized."
        )
    return prd_service.get_summary()


@app.get("/api/prd/comparison")
async def prd_comparison():
    """Get PRD comparison data - current vs available."""
    if not prd_service:
        raise HTTPException(
            status_code=503,
            detail="PRD service not initialized."
        )
    return prd_service.get_comparison()


@app.get("/api/prd/roadmap")
async def prd_roadmap():
    """Get PRD roadmap data - prioritized enhancements."""
    if not prd_service:
        raise HTTPException(
            status_code=503,
            detail="PRD service not initialized."
        )
    return prd_service.get_roadmap()


@app.get("/api/prd/objects")
async def prd_objects(category: Optional[str] = None):
    """Get detailed objects list with status."""
    if not prd_service:
        raise HTTPException(
            status_code=503,
            detail="PRD service not initialized."
        )
    return prd_service.get_objects(category)


@app.get("/api/prd/all")
async def prd_all():
    """Get all PRD data in one call."""
    if not prd_service:
        raise HTTPException(
            status_code=503,
            detail="PRD service not initialized."
        )
    return prd_service.get_all_prd_data()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
