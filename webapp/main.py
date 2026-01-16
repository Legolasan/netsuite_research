"""
Connector Research Platform - FastAPI Web Application

A modern platform for creating, managing, and searching connector research documents.
Supports multi-connector research with per-connector Pinecone indices.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
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
from services.connector_manager import get_connector_manager, ConnectorManager, ConnectorStatus
from services.github_cloner import get_github_cloner, GitHubCloner
from services.research_agent import get_research_agent, ResearchAgent
from services.pinecone_manager import get_pinecone_manager, PineconeManager


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None
    object_type: Optional[str] = None
    include_web: bool = False  # Include cached web results
    include_summaries: bool = True  # Generate AI summaries for results
    max_summaries: int = 5  # Max results to summarize


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
    summary: Optional[str] = None  # AI-generated summary


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


# =====================
# Connector API Models
# =====================

class ConnectorCreateRequest(BaseModel):
    name: str
    connector_type: str
    github_url: Optional[str] = None
    description: str = ""


class ConnectorProgressResponse(BaseModel):
    current_section: int
    total_sections: int
    current_phase: int
    sections_completed: List[int]
    percentage: float
    current_section_name: str


class ConnectorResponse(BaseModel):
    id: str
    name: str
    connector_type: str
    status: str
    github_url: Optional[str]
    description: str
    objects_count: int
    vectors_count: int
    fivetran_parity: Optional[float]
    progress: ConnectorProgressResponse
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    pinecone_index: str


class ConnectorListResponse(BaseModel):
    connectors: List[ConnectorResponse]
    total: int


class ConnectorSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class ConnectorSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int


# Services (initialized on startup)
search_service: Optional[SearchService] = None
chat_service: Optional[ChatService] = None
web_search_service: Optional[WebSearchService] = None
prd_service: Optional[PRDService] = None
connector_manager: Optional[ConnectorManager] = None
github_cloner: Optional[GitHubCloner] = None
research_agent: Optional[ResearchAgent] = None
pinecone_manager: Optional[PineconeManager] = None

# Background tasks tracking
_running_research_tasks: Dict[str, asyncio.Task] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global search_service, chat_service, web_search_service, prd_service
    global connector_manager, github_cloner, research_agent, pinecone_manager
    
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
    
    # Initialize connector services
    try:
        connector_manager = get_connector_manager()
        print("✓ Connector Manager initialized")
    except Exception as e:
        print(f"⚠ Connector Manager not available: {e}")
        connector_manager = None
    
    try:
        github_cloner = get_github_cloner()
        print("✓ GitHub Cloner initialized")
    except Exception as e:
        print(f"⚠ GitHub Cloner not available: {e}")
        github_cloner = None
    
    try:
        research_agent = get_research_agent()
        print("✓ Research Agent initialized")
    except Exception as e:
        print(f"⚠ Research Agent not available: {e}")
        research_agent = None
    
    try:
        pinecone_manager = get_pinecone_manager()
        print("✓ Pinecone Manager initialized")
    except Exception as e:
        print(f"⚠ Pinecone Manager not available: {e}")
        pinecone_manager = None
    
    yield
    
    # Cancel any running research tasks
    for task in _running_research_tasks.values():
        task.cancel()
    
    print("Shutting down services...")


# Create FastAPI app
app = FastAPI(
    title="Connector Research Platform",
    description="Multi-connector research platform with per-connector Pinecone indices, RAG chat, and web search",
    version="3.0.0",
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
                filter=filter_dict if filter_dict else None,
                include_summaries=request.include_summaries,
                max_summaries=request.max_summaries
            )
        else:
            results = search_service.search_docs_only(
                query=request.query,
                top_k=request.top_k,
                filter=filter_dict if filter_dict else None,
                include_summaries=request.include_summaries,
                max_summaries=request.max_summaries
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
                    title=r.title,
                    summary=r.summary
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


# =====================
# Connector API Endpoints
# =====================

def _connector_to_response(connector) -> ConnectorResponse:
    """Convert Connector object to response model."""
    return ConnectorResponse(
        id=connector.id,
        name=connector.name,
        connector_type=connector.connector_type,
        status=connector.status,
        github_url=connector.github_url,
        description=connector.description,
        objects_count=connector.objects_count,
        vectors_count=connector.vectors_count,
        fivetran_parity=connector.fivetran_parity,
        progress=ConnectorProgressResponse(
            current_section=connector.progress.current_section,
            total_sections=connector.progress.total_sections,
            current_phase=connector.progress.current_phase,
            sections_completed=connector.progress.sections_completed,
            percentage=connector.progress.percentage,
            current_section_name=connector.progress.current_section_name
        ),
        created_at=connector.created_at,
        updated_at=connector.updated_at,
        completed_at=connector.completed_at,
        pinecone_index=connector.pinecone_index
    )


@app.get("/api/connectors", response_model=ConnectorListResponse)
async def list_connectors():
    """List all connector research projects."""
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector Manager not initialized")
    
    connectors = connector_manager.list_connectors()
    return ConnectorListResponse(
        connectors=[_connector_to_response(c) for c in connectors],
        total=len(connectors)
    )


@app.post("/api/connectors", response_model=ConnectorResponse)
async def create_connector(request: ConnectorCreateRequest):
    """Create a new connector research project."""
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector Manager not initialized")
    
    try:
        connector = connector_manager.create_connector(
            name=request.name,
            connector_type=request.connector_type,
            github_url=request.github_url,
            description=request.description
        )
        return _connector_to_response(connector)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/connectors/{connector_id}", response_model=ConnectorResponse)
async def get_connector(connector_id: str):
    """Get a specific connector by ID."""
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector Manager not initialized")
    
    connector = connector_manager.get_connector(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")
    
    return _connector_to_response(connector)


@app.delete("/api/connectors/{connector_id}")
async def delete_connector(connector_id: str):
    """Delete a connector research project."""
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector Manager not initialized")
    
    # Cancel any running research
    if connector_id in _running_research_tasks:
        _running_research_tasks[connector_id].cancel()
        del _running_research_tasks[connector_id]
    
    success = connector_manager.delete_connector(connector_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")
    
    # Optionally delete Pinecone index
    if pinecone_manager:
        pinecone_manager.delete_index(connector_id)
    
    return {"message": f"Connector '{connector_id}' deleted"}


@app.post("/api/connectors/{connector_id}/generate")
async def generate_research(connector_id: str, background_tasks: BackgroundTasks):
    """Start research generation for a connector (runs in background)."""
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector Manager not initialized")
    if not research_agent:
        raise HTTPException(status_code=503, detail="Research Agent not initialized")
    
    connector = connector_manager.get_connector(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")
    
    # Check if already running
    if connector_id in _running_research_tasks:
        return {"message": "Research generation already in progress", "status": "running"}
    
    # Update status
    connector_manager.update_connector(connector_id, status=ConnectorStatus.RESEARCHING.value)
    
    async def run_research():
        """Background task to run research generation."""
        try:
            github_context = None
            
            # Clone GitHub repo if URL provided
            if connector.github_url and github_cloner:
                connector_manager.update_connector(connector_id, status=ConnectorStatus.CLONING.value)
                extracted = await github_cloner.clone_and_extract(connector.github_url, connector_id)
                github_context = extracted.to_dict()
            
            # Update status to researching
            connector_manager.update_connector(connector_id, status=ConnectorStatus.RESEARCHING.value)
            
            # Generate research
            def on_progress(progress):
                connector_manager.update_progress(
                    connector_id,
                    section=progress.current_section,
                    section_name=progress.current_content[:50] if progress.current_content else "",
                    completed=(progress.current_section in progress.sections_completed)
                )
            
            research_content = await research_agent.generate_research(
                connector_id=connector_id,
                connector_name=connector.name,
                connector_type=connector.connector_type,
                github_context=github_context,
                on_progress=on_progress
            )
            
            # Save research document
            doc_path = connector_manager.get_research_document_path(connector_id)
            if doc_path:
                with open(doc_path, 'w') as f:
                    f.write(research_content)
            
            # Vectorize into Pinecone
            vectors_count = 0
            if pinecone_manager:
                vectors_count = pinecone_manager.vectorize_research(
                    connector_id=connector_id,
                    connector_name=connector.name,
                    research_content=research_content
                )
            
            # Update connector with final stats
            connector_manager.update_connector(
                connector_id,
                status=ConnectorStatus.COMPLETE.value,
                vectors_count=vectors_count
            )
            
        except asyncio.CancelledError:
            connector_manager.update_connector(connector_id, status=ConnectorStatus.CANCELLED.value)
        except Exception as e:
            print(f"Research generation failed: {e}")
            connector_manager.update_connector(connector_id, status=ConnectorStatus.FAILED.value)
        finally:
            if connector_id in _running_research_tasks:
                del _running_research_tasks[connector_id]
    
    # Start background task
    task = asyncio.create_task(run_research())
    _running_research_tasks[connector_id] = task
    
    return {"message": "Research generation started", "status": "started", "connector_id": connector_id}


@app.get("/api/connectors/{connector_id}/status")
async def get_research_status(connector_id: str):
    """Get research generation status for a connector."""
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector Manager not initialized")
    
    connector = connector_manager.get_connector(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")
    
    is_running = connector_id in _running_research_tasks
    
    return {
        "connector_id": connector_id,
        "status": connector.status,
        "is_running": is_running,
        "progress": {
            "current_section": connector.progress.current_section,
            "total_sections": connector.progress.total_sections,
            "sections_completed": connector.progress.sections_completed,
            "percentage": connector.progress.percentage,
            "current_section_name": connector.progress.current_section_name
        }
    }


@app.post("/api/connectors/{connector_id}/cancel")
async def cancel_research(connector_id: str):
    """Cancel research generation for a connector."""
    if connector_id not in _running_research_tasks:
        raise HTTPException(status_code=400, detail="No research generation running for this connector")
    
    _running_research_tasks[connector_id].cancel()
    
    if connector_manager:
        connector_manager.update_connector(connector_id, status=ConnectorStatus.CANCELLED.value)
    
    return {"message": "Research generation cancelled", "connector_id": connector_id}


@app.get("/api/connectors/{connector_id}/research")
async def get_research_document(connector_id: str):
    """Get the research document content for a connector."""
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector Manager not initialized")
    
    content = connector_manager.get_research_document(connector_id)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Research document not found for '{connector_id}'")
    
    return {"connector_id": connector_id, "content": content}


@app.post("/api/connectors/{connector_id}/search", response_model=ConnectorSearchResponse)
async def search_connector(connector_id: str, request: ConnectorSearchRequest):
    """Search within a specific connector's index."""
    if not pinecone_manager:
        raise HTTPException(status_code=503, detail="Pinecone Manager not initialized")
    
    if not pinecone_manager.index_exists(connector_id):
        raise HTTPException(status_code=404, detail=f"No index found for connector '{connector_id}'")
    
    results = pinecone_manager.search(
        connector_id=connector_id,
        query=request.query,
        top_k=request.top_k
    )
    
    return ConnectorSearchResponse(
        query=request.query,
        results=results,
        total_results=len(results)
    )


@app.post("/api/connectors/search-all", response_model=ConnectorSearchResponse)
async def search_all_connectors(request: ConnectorSearchRequest):
    """Search across all connector indices."""
    if not pinecone_manager or not connector_manager:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    # Get all connector IDs
    connectors = connector_manager.list_connectors()
    connector_ids = [c.id for c in connectors if c.status == ConnectorStatus.COMPLETE.value]
    
    if not connector_ids:
        return ConnectorSearchResponse(query=request.query, results=[], total_results=0)
    
    results = pinecone_manager.search_all_connectors(
        query=request.query,
        connector_ids=connector_ids,
        top_k=request.top_k
    )
    
    return ConnectorSearchResponse(
        query=request.query,
        results=results,
        total_results=len(results)
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
