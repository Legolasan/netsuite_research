"""Services package for Connector Research Platform webapp."""

from .search import SearchService, SearchResult, SearchResponse
from .chat import ChatService
from .web_search import WebSearchService, WebSearchResult, WebSearchResponse
from .prd import PRDService
from .connector_manager import ConnectorManager, Connector, ConnectorStatus, get_connector_manager
from .github_cloner import GitHubCloner, ExtractedCode, get_github_cloner
from .research_agent import ResearchAgent, get_research_agent
from .pinecone_manager import PineconeManager, get_pinecone_manager

__all__ = [
    # Original services
    "SearchService", 
    "SearchResult", 
    "SearchResponse",
    "ChatService",
    "WebSearchService",
    "WebSearchResult",
    "WebSearchResponse",
    "PRDService",
    # Connector services
    "ConnectorManager",
    "Connector",
    "ConnectorStatus",
    "get_connector_manager",
    "GitHubCloner",
    "ExtractedCode",
    "get_github_cloner",
    "ResearchAgent",
    "get_research_agent",
    "PineconeManager",
    "get_pinecone_manager",
]
