"""
Search Service - Semantic search over NetSuite documentation

Adapted from vectorization/query_docs.py for web application use.
"""

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class SearchResult:
    """Represents a single search result."""
    chunk_id: str
    score: float
    text: str
    source_file: str
    doc_category: str
    object_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Web-specific fields
    source_type: str = "doc"  # "doc", "code", "research", or "web"
    url: Optional[str] = None
    title: Optional[str] = None
    # AI-generated summary
    summary: Optional[str] = None


@dataclass
class SearchResponse:
    """Represents a complete search response."""
    query: str
    results: List[SearchResult]
    total_results: int
    
    def to_context_string(self, max_results: int = 5) -> str:
        """Convert top results to a context string for RAG."""
        context_parts = []
        for result in self.results[:max_results]:
            if result.source_type == "web" and result.url:
                context_parts.append(
                    f"[Web Source: {result.title or result.source_file}]\nURL: {result.url}\n{result.text}"
                )
            else:
                context_parts.append(
                    f"[Doc Source: {result.source_file}]\n{result.text}"
                )
        return "\n\n---\n\n".join(context_parts)
    
    def get_doc_results(self) -> List[SearchResult]:
        """Get only documentation results."""
        return [r for r in self.results if r.source_type == "doc"]
    
    def get_web_results(self) -> List[SearchResult]:
        """Get only web results."""
        return [r for r in self.results if r.source_type == "web"]


class SearchService:
    """Semantic search service for NetSuite documentation."""
    
    # Score boost multipliers for different source types
    # CODE and RESEARCH sources have cleaner, more actionable content
    SCORE_BOOST = {
        "code": 1.3,      # 30% boost for connector code
        "research": 1.25, # 25% boost for research docs
        "doc": 1.0,       # No change for PDFs
        "web": 1.1,       # 10% boost for web results
    }
    
    def __init__(self):
        """Initialize the search service with API clients."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "netsuite-docs")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        # Initialize clients
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pinecone_client.Index(self.index_name)
    
    def _apply_score_boost(self, score: float, source_type: str) -> float:
        """Apply score boost based on source type."""
        boost = self.SCORE_BOOST.get(source_type, 1.0)
        # Cap boosted score at 1.0 (100%)
        return min(score * boost, 1.0)
    
    def _generate_summary(self, text: str, source_type: str, source_file: str, query: str) -> str:
        """Generate an AI-powered summary for a search result."""
        # Customize prompt based on source type
        if source_type == "code":
            context = f"This is Java code from the NetSuite connector file '{source_file}'."
            instruction = "Explain what this code does in plain English. Focus on the NetSuite objects, their types, and how they're used for data replication."
        elif source_type == "research":
            context = f"This is from a research document '{source_file}' about NetSuite integration."
            instruction = "Summarize the key findings or recommendations from this content."
        elif source_type == "web":
            context = f"This is from a web page about NetSuite."
            instruction = "Summarize the relevant information about NetSuite from this content."
        else:
            context = f"This is from NetSuite documentation '{source_file}'."
            instruction = "Summarize the key information relevant to the search query."
        
        prompt = f"""You are a technical documentation assistant. {context}

User's search query: "{query}"

Content to summarize:
{text[:1500]}

{instruction}

Provide a concise 2-3 sentence summary that directly answers or relates to the user's query. Be specific about NetSuite objects, features, or capabilities mentioned."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective for summaries
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Summary unavailable: {str(e)}"
    
    def _summarize_results(self, results: List[SearchResult], query: str, max_results: int = 5) -> List[SearchResult]:
        """Add AI summaries to search results using parallel processing."""
        # Only summarize top results to save API calls
        results_to_summarize = results[:max_results]
        
        def summarize_single(result: SearchResult) -> SearchResult:
            summary = self._generate_summary(
                result.text, 
                result.source_type, 
                result.source_file,
                query
            )
            result.summary = summary
            return result
        
        # Use thread pool for parallel API calls
        with ThreadPoolExecutor(max_workers=5) as executor:
            summarized = list(executor.map(summarize_single, results_to_summarize))
        
        # Combine summarized results with remaining results
        return summarized + results[max_results:]
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        include_summaries: bool = False,
        max_summaries: int = 5
    ) -> SearchResponse:
        """
        Perform semantic search over the documentation.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            filter: Optional metadata filter (e.g., {"doc_category": {"$eq": "SOAP"}})
            include_metadata: Whether to include metadata in results
            include_summaries: Whether to generate AI summaries for results
            max_summaries: Maximum number of results to summarize (to control API costs)
            
        Returns:
            SearchResponse with ranked results
        """
        # Generate query embedding
        query_vector = self.generate_embedding(query)
        
        # Query Pinecone
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata
        )
        
        # Parse results and apply score boosting
        search_results = []
        for match in results.matches:
            metadata = match.metadata or {}
            source_type = metadata.get("source_type", "doc")
            
            # Apply score boost for CODE and RESEARCH sources
            boosted_score = self._apply_score_boost(match.score, source_type)
            
            search_results.append(SearchResult(
                chunk_id=match.id,
                score=boosted_score,
                text=metadata.get("text", ""),
                source_file=metadata.get("source_file", "Unknown"),
                doc_category=metadata.get("doc_category", "GENERAL"),
                object_type=metadata.get("object_type", "General"),
                metadata=metadata,
                source_type=source_type,
                url=metadata.get("url") if source_type == "web" else None,
                title=metadata.get("title") if source_type == "web" else None
            ))
        
        # Re-sort by boosted score (highest first)
        search_results.sort(key=lambda r: r.score, reverse=True)
        
        # Generate AI summaries if requested
        if include_summaries and search_results:
            search_results = self._summarize_results(search_results, query, max_summaries)
        
        return SearchResponse(
            query=query,
            results=search_results,
            total_results=len(search_results)
        )
    
    def search_docs_only(
        self,
        query: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_summaries: bool = False,
        max_summaries: int = 5
    ) -> SearchResponse:
        """Search only documentation (exclude web results)."""
        combined_filter = {"source_type": {"$ne": "web"}}
        if filter:
            combined_filter = {"$and": [combined_filter, filter]}
        return self.search(
            query, top_k, combined_filter, 
            include_summaries=include_summaries, 
            max_summaries=max_summaries
        )
    
    def search_web_only(
        self,
        query: str,
        top_k: int = 10
    ) -> SearchResponse:
        """Search only cached web results."""
        return self.search(query, top_k, {"source_type": {"$eq": "web"}})
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "index_name": self.index_name,
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "categories": ["SOAP", "REST", "GOVERNANCE", "PERMISSION", "RECORD", "SEARCH", "CUSTOM", "GENERAL", "WEB"],
                "status": "connected"
            }
        except Exception as e:
            return {
                "index_name": self.index_name,
                "total_vectors": 0,
                "dimension": 1536,
                "categories": [],
                "status": f"error: {str(e)}"
            }
