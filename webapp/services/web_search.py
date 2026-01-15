"""
Web Search Service - Tavily web search with auto-vectorization to Pinecone

Searches the web for NetSuite-related content and automatically stores
results in Pinecone for future retrieval.
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from openai import OpenAI
from pinecone import Pinecone
from tavily import TavilyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class WebSearchResult:
    """Represents a single web search result."""
    url: str
    title: str
    content: str
    score: float
    source_type: str = "web"
    search_date: str = field(default_factory=lambda: datetime.now().isoformat()[:10])
    is_cached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "score": self.score,
            "source_type": self.source_type,
            "search_date": self.search_date,
            "is_cached": self.is_cached
        }


@dataclass
class WebSearchResponse:
    """Represents a complete web search response."""
    query: str
    results: List[WebSearchResult]
    total_results: int
    cached_count: int = 0
    fresh_count: int = 0
    
    def to_context_string(self, max_results: int = 5) -> str:
        """Convert top results to a context string for RAG."""
        context_parts = []
        for result in self.results[:max_results]:
            context_parts.append(
                f"[Web Source: {result.title}]\nURL: {result.url}\n{result.content}"
            )
        return "\n\n---\n\n".join(context_parts)


class WebSearchService:
    """Web search service with auto-vectorization to Pinecone."""
    
    def __init__(self):
        """Initialize the web search service."""
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "netsuite-docs")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.cache_days = int(os.getenv("WEB_CACHE_DAYS", "7"))
        
        # Tavily is optional - service works without it using only cached results
        self.tavily_client = None
        if self.tavily_api_key:
            self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
        
        # OpenAI and Pinecone are required for vectorization
        if self.openai_api_key and self.pinecone_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            self.index = self.pinecone_client.Index(self.index_name)
        else:
            self.openai_client = None
            self.pinecone_client = None
            self.index = None
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate a unique hash for a URL."""
        return f"web_{hashlib.sha256(url.encode()).hexdigest()[:24]}"
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text[:8000]  # Limit text length for embedding
        )
        return response.data[0].embedding
    
    def _is_content_stale(self, search_date: str) -> bool:
        """Check if cached content is older than cache_days."""
        try:
            cached_date = datetime.fromisoformat(search_date)
            return datetime.now() - cached_date > timedelta(days=self.cache_days)
        except:
            return True
    
    def search_cached(
        self,
        query: str,
        top_k: int = 5
    ) -> List[WebSearchResult]:
        """Search for cached web content in Pinecone."""
        if not self.index:
            return []
        
        try:
            query_vector = self._generate_embedding(query)
            
            # Search with filter for web content
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter={"source_type": {"$eq": "web"}},
                include_metadata=True
            )
            
            cached_results = []
            for match in results.matches:
                metadata = match.metadata or {}
                cached_results.append(WebSearchResult(
                    url=metadata.get("url", ""),
                    title=metadata.get("title", "Unknown"),
                    content=metadata.get("text", ""),
                    score=match.score,
                    source_type="web",
                    search_date=metadata.get("search_date", ""),
                    is_cached=True
                ))
            
            return cached_results
        except Exception as e:
            print(f"Error searching cached content: {e}")
            return []
    
    def search_web(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> List[WebSearchResult]:
        """Perform fresh web search using Tavily."""
        if not self.tavily_client:
            return []
        
        try:
            # Add NetSuite context to query for better results
            enhanced_query = f"NetSuite {query}"
            
            response = self.tavily_client.search(
                query=enhanced_query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=False
            )
            
            web_results = []
            for result in response.get("results", []):
                web_results.append(WebSearchResult(
                    url=result.get("url", ""),
                    title=result.get("title", "Unknown"),
                    content=result.get("content", ""),
                    score=result.get("score", 0.0),
                    source_type="web",
                    search_date=datetime.now().isoformat()[:10],
                    is_cached=False
                ))
            
            return web_results
        except Exception as e:
            print(f"Error performing web search: {e}")
            return []
    
    def vectorize_and_store(
        self,
        results: List[WebSearchResult],
        original_query: str
    ) -> int:
        """Vectorize web search results and store in Pinecone."""
        if not self.index or not self.openai_client:
            return 0
        
        vectors_to_upsert = []
        
        for result in results:
            if not result.content or result.is_cached:
                continue
            
            try:
                # Generate unique ID based on URL
                vector_id = self._generate_url_hash(result.url)
                
                # Generate embedding
                embedding = self._generate_embedding(result.content)
                
                # Prepare metadata
                metadata = {
                    "text": result.content[:1000],  # Store truncated text
                    "source_type": "web",
                    "source_file": "web_search",
                    "url": result.url,
                    "title": result.title,
                    "search_query": original_query,
                    "search_date": result.search_date,
                    "doc_category": "WEB",
                    "object_type": "General"
                }
                
                vectors_to_upsert.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            except Exception as e:
                print(f"Error vectorizing result {result.url}: {e}")
                continue
        
        if vectors_to_upsert:
            try:
                self.index.upsert(vectors=vectors_to_upsert)
                return len(vectors_to_upsert)
            except Exception as e:
                print(f"Error upserting vectors: {e}")
                return 0
        
        return 0
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        force_refresh: bool = False,
        include_cached: bool = True
    ) -> WebSearchResponse:
        """
        Perform hybrid web search with caching.
        
        1. Check Pinecone for cached web results
        2. If no good cached results or force_refresh, search web
        3. Vectorize and store new results
        4. Return combined results
        """
        all_results = []
        cached_count = 0
        fresh_count = 0
        
        # Step 1: Search cached content (unless force refresh)
        if include_cached and not force_refresh:
            cached_results = self.search_cached(query, top_k=top_k)
            
            # Filter out stale content
            fresh_cached = [r for r in cached_results if not self._is_content_stale(r.search_date)]
            all_results.extend(fresh_cached)
            cached_count = len(fresh_cached)
        
        # Step 2: Search web if needed
        need_fresh_search = (
            force_refresh or 
            len(all_results) < top_k or 
            not self.tavily_client
        )
        
        if need_fresh_search and self.tavily_client:
            web_results = self.search_web(query, max_results=top_k)
            
            # Filter out duplicates (by URL)
            existing_urls = {r.url for r in all_results}
            new_results = [r for r in web_results if r.url not in existing_urls]
            
            # Step 3: Vectorize and store new results
            if new_results:
                stored_count = self.vectorize_and_store(new_results, query)
                fresh_count = stored_count
                all_results.extend(new_results)
        
        # Sort by score and limit
        all_results.sort(key=lambda x: x.score, reverse=True)
        all_results = all_results[:top_k]
        
        return WebSearchResponse(
            query=query,
            results=all_results,
            total_results=len(all_results),
            cached_count=cached_count,
            fresh_count=fresh_count
        )
    
    def is_available(self) -> bool:
        """Check if web search service is available."""
        return self.tavily_client is not None or self.index is not None
