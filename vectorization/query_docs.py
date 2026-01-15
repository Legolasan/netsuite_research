"""
NetSuite Documentation Vectorization - Query Interface Module

This module provides semantic search capabilities over the vectorized documentation.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from openai import OpenAI
from pinecone import Pinecone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from config import get_config, Config

console = Console()


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
    
    def __repr__(self):
        return f"SearchResult(source='{self.source_file}', score={self.score:.3f})"


@dataclass
class SearchResponse:
    """Represents a complete search response."""
    query: str
    results: List[SearchResult]
    total_results: int
    
    def to_context_string(self, max_results: int = 5) -> str:
        """Convert top results to a context string for RAG."""
        context_parts = []
        for i, result in enumerate(self.results[:max_results]):
            context_parts.append(
                f"[Source: {result.source_file}]\n{result.text}"
            )
        return "\n\n---\n\n".join(context_parts)


class NetSuiteDocSearch:
    """Semantic search interface for NetSuite documentation."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the search interface.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
        """
        self.config = config or get_config()
        
        # Initialize clients
        self.openai_client = OpenAI(api_key=self.config.openai.api_key)
        self.pinecone_client = Pinecone(api_key=self.config.pinecone.api_key)
        self.index = self.pinecone_client.Index(self.config.pinecone.index_name)
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query string
            
        Returns:
            Query embedding vector
        """
        response = self.openai_client.embeddings.create(
            model=self.config.openai.embedding_model,
            input=query
        )
        return response.data[0].embedding
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> SearchResponse:
        """
        Perform semantic search over the documentation.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            filter: Optional metadata filter (e.g., {"doc_category": "SOAP"})
            include_metadata: Whether to include metadata in results
            
        Returns:
            SearchResponse with ranked results
        """
        # Generate query embedding
        query_vector = self.generate_query_embedding(query)
        
        # Query Pinecone
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata
        )
        
        # Parse results
        search_results = []
        for match in results.matches:
            metadata = match.metadata or {}
            search_results.append(SearchResult(
                chunk_id=match.id,
                score=match.score,
                text=metadata.get("text", ""),
                source_file=metadata.get("source_file", "Unknown"),
                doc_category=metadata.get("doc_category", "GENERAL"),
                object_type=metadata.get("object_type", "General"),
                metadata=metadata
            ))
        
        return SearchResponse(
            query=query,
            results=search_results,
            total_results=len(search_results)
        )
    
    def search_by_category(
        self,
        query: str,
        category: str,
        top_k: int = 10
    ) -> SearchResponse:
        """
        Search within a specific document category.
        
        Args:
            query: Search query
            category: Document category (SOAP, REST, GOVERNANCE, PERMISSION, RECORD, etc.)
            top_k: Number of results
            
        Returns:
            SearchResponse filtered by category
        """
        return self.search(
            query=query,
            top_k=top_k,
            filter={"doc_category": {"$eq": category}}
        )
    
    def search_by_object(
        self,
        query: str,
        object_type: str,
        top_k: int = 10
    ) -> SearchResponse:
        """
        Search within documentation for a specific object type.
        
        Args:
            query: Search query
            object_type: Object type (Customer, Invoice, Transaction, etc.)
            top_k: Number of results
            
        Returns:
            SearchResponse filtered by object type
        """
        return self.search(
            query=query,
            top_k=top_k,
            filter={"object_type": {"$eq": object_type}}
        )
    
    def find_similar(
        self,
        chunk_id: str,
        top_k: int = 5
    ) -> SearchResponse:
        """
        Find documents similar to a specific chunk.
        
        Args:
            chunk_id: ID of the reference chunk
            top_k: Number of similar results
            
        Returns:
            SearchResponse with similar documents
        """
        # Fetch the original vector
        fetch_response = self.index.fetch(ids=[chunk_id])
        
        if chunk_id not in fetch_response.vectors:
            return SearchResponse(query=f"Similar to {chunk_id}", results=[], total_results=0)
        
        original_vector = fetch_response.vectors[chunk_id].values
        
        # Search for similar
        results = self.index.query(
            vector=original_vector,
            top_k=top_k + 1,  # +1 to exclude the original
            include_metadata=True
        )
        
        # Parse and filter out original
        search_results = []
        for match in results.matches:
            if match.id == chunk_id:
                continue
            metadata = match.metadata or {}
            search_results.append(SearchResult(
                chunk_id=match.id,
                score=match.score,
                text=metadata.get("text", ""),
                source_file=metadata.get("source_file", "Unknown"),
                doc_category=metadata.get("doc_category", "GENERAL"),
                object_type=metadata.get("object_type", "General"),
                metadata=metadata
            ))
        
        return SearchResponse(
            query=f"Similar to {chunk_id}",
            results=search_results[:top_k],
            total_results=len(search_results)
        )


def search_netsuite_docs(
    query: str,
    top_k: int = 5,
    filter: Optional[Dict[str, Any]] = None,
    config: Optional[Config] = None
) -> SearchResponse:
    """
    Convenience function for searching NetSuite documentation.
    
    Args:
        query: Natural language search query
        top_k: Number of results to return
        filter: Optional metadata filter
        config: Optional configuration
        
    Returns:
        SearchResponse with results
    
    Example:
        >>> results = search_netsuite_docs(
        ...     "What are the API rate limits?",
        ...     filter={"doc_category": "GOVERNANCE"}
        ... )
    """
    searcher = NetSuiteDocSearch(config)
    return searcher.search(query, top_k, filter)


def print_search_results(response: SearchResponse):
    """Pretty print search results to console."""
    console.print(f"\n[bold blue]Search Results for:[/bold blue] {response.query}\n")
    console.print(f"[dim]Found {response.total_results} results[/dim]\n")
    
    for i, result in enumerate(response.results, 1):
        console.print(Panel(
            f"[dim]{result.text[:500]}{'...' if len(result.text) > 500 else ''}[/dim]",
            title=f"[bold]{i}. {result.source_file}[/bold]",
            subtitle=f"Score: {result.score:.3f} | Category: {result.doc_category} | Object: {result.object_type}"
        ))


def interactive_search():
    """Run an interactive search session."""
    console.print("\n[bold blue]NetSuite Documentation Search[/bold blue]")
    console.print("[dim]Type 'quit' to exit[/dim]\n")
    
    searcher = NetSuiteDocSearch()
    
    while True:
        query = console.input("[green]Search:[/green] ").strip()
        
        if query.lower() in ("quit", "exit", "q"):
            break
        
        if not query:
            continue
        
        try:
            results = searcher.search(query, top_k=5)
            print_search_results(results)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Search NetSuite documentation")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--object", help="Filter by object type")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    args = parser.parse_args()
    
    if args.interactive:
        interactive_search()
    elif args.query:
        filter_dict = {}
        if args.category:
            filter_dict["doc_category"] = {"$eq": args.category}
        if args.object:
            filter_dict["object_type"] = {"$eq": args.object}
        
        results = search_netsuite_docs(
            args.query,
            top_k=args.top_k,
            filter=filter_dict if filter_dict else None
        )
        print_search_results(results)
    else:
        parser.print_help()
