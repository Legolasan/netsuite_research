"""
Chat Service - RAG-powered chat over NetSuite documentation with web search

Combines vectorized documentation with live web search for comprehensive answers.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from openai import OpenAI
from dotenv import load_dotenv

from .search import SearchService, SearchResponse
from .web_search import WebSearchService, WebSearchResponse

# Load environment variables
load_dotenv()


# System prompt for NetSuite documentation Q&A with web search
SYSTEM_PROMPT = """You are a NetSuite documentation expert assistant. Your role is to answer questions about NetSuite APIs, objects, integrations, and best practices based on the provided context.

You may receive context from two sources:
1. **Documentation**: Official NetSuite documentation that has been indexed
2. **Web Search**: Recent web search results for up-to-date information

Guidelines:
1. Answer based on the provided context. Prioritize official documentation over web results when available.
2. Clearly cite your sources, distinguishing between documentation and web sources.
3. For technical questions, provide code examples when relevant.
4. Highlight any important warnings, limitations, or governance considerations.
5. If asked about API limits or permissions, be precise about the requirements.
6. If web sources provide newer information that contradicts older documentation, mention this discrepancy.

Format your responses in a clear, structured manner using:
- Headers for different sections
- Bullet points for lists
- Code blocks for API examples
- Tables for comparing options when appropriate

When citing sources:
- For documentation: Use the document name, e.g., "According to [NetSuite SOAP API Guide]..."
- For web sources: Include the URL, e.g., "According to [Oracle Help Center](https://...)..."
"""


@dataclass
class Source:
    """Represents a source reference."""
    name: str
    type: str  # "doc" or "web"
    url: Optional[str] = None


@dataclass
class RAGResponse:
    """Represents a RAG-generated response."""
    question: str
    answer: str
    sources: List[str]
    web_sources: List[Dict[str, str]] = field(default_factory=list)  # [{name, url}]
    doc_sources: List[str] = field(default_factory=list)
    context_used: str = ""
    model: str = ""
    tokens_used: int = 0
    include_web: bool = False


class ChatService:
    """RAG chat service for NetSuite documentation Q&A with web search."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.1):
        """
        Initialize the chat service.
        
        Args:
            model: OpenAI model for generation
            temperature: Generation temperature (lower = more focused)
        """
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.search_service = SearchService()
        
        # Web search is optional
        try:
            self.web_search_service = WebSearchService()
        except Exception:
            self.web_search_service = None
    
    def retrieve_doc_context(
        self,
        question: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Retrieve relevant context from documentation."""
        return self.search_service.search_docs_only(question, top_k=top_k, filter=filter)
    
    def retrieve_web_context(
        self,
        question: str,
        top_k: int = 3,
        force_refresh: bool = False
    ) -> Optional[WebSearchResponse]:
        """Retrieve relevant context from web search."""
        if not self.web_search_service or not self.web_search_service.is_available():
            return None
        
        return self.web_search_service.search(
            query=question,
            top_k=top_k,
            force_refresh=force_refresh
        )
    
    def _build_combined_context(
        self,
        doc_results: SearchResponse,
        web_results: Optional[WebSearchResponse],
        max_doc_results: int = 5,
        max_web_results: int = 3
    ) -> tuple[str, List[str], List[Dict[str, str]]]:
        """
        Build combined context from doc and web results.
        
        Returns:
            Tuple of (context_string, doc_sources, web_sources)
        """
        context_parts = []
        doc_sources = []
        web_sources = []
        
        # Add documentation context
        if doc_results.results:
            context_parts.append("## From Official Documentation:\n")
            for result in doc_results.results[:max_doc_results]:
                context_parts.append(f"[Source: {result.source_file}]\n{result.text}\n")
                if result.source_file not in doc_sources:
                    doc_sources.append(result.source_file)
        
        # Add web context
        if web_results and web_results.results:
            context_parts.append("\n## From Web Search:\n")
            for result in web_results.results[:max_web_results]:
                context_parts.append(
                    f"[Web Source: {result.title}]\nURL: {result.url}\n{result.content}\n"
                )
                web_sources.append({
                    "name": result.title,
                    "url": result.url,
                    "is_cached": result.is_cached
                })
        
        return "\n".join(context_parts), doc_sources, web_sources
    
    def generate_answer(
        self,
        question: str,
        context: str,
        doc_sources: List[str],
        web_sources: List[Dict[str, str]]
    ) -> RAGResponse:
        """Generate an answer using GPT with the retrieved context."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Based on the following context (from documentation and/or web search), please answer the question.

CONTEXT:
{context}

QUESTION: {question}

Please provide a comprehensive answer based on the context above. Cite your sources appropriately."""}
        ]
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        # Combine all sources for backward compatibility
        all_sources = doc_sources.copy()
        for ws in web_sources:
            all_sources.append(f"{ws['name']} ({ws['url']})")
        
        return RAGResponse(
            question=question,
            answer=answer,
            sources=all_sources,
            doc_sources=doc_sources,
            web_sources=web_sources,
            context_used=context[:500] + "..." if len(context) > 500 else context,
            model=self.model,
            tokens_used=tokens_used,
            include_web=len(web_sources) > 0
        )
    
    def ask(
        self,
        question: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_web: bool = True,
        force_web_refresh: bool = False
    ) -> RAGResponse:
        """
        Ask a question about NetSuite documentation.
        
        Args:
            question: Natural language question
            top_k: Number of context chunks to retrieve
            filter: Optional metadata filter for context
            include_web: Whether to include web search results
            force_web_refresh: Force fresh web search (ignore cache)
            
        Returns:
            RAGResponse with answer and sources
        """
        # Retrieve documentation context
        doc_results = self.retrieve_doc_context(question, top_k, filter)
        
        # Retrieve web context if enabled
        web_results = None
        if include_web:
            web_results = self.retrieve_web_context(
                question, 
                top_k=3, 
                force_refresh=force_web_refresh
            )
        
        # Check if we have any results
        has_doc_results = doc_results and doc_results.results
        has_web_results = web_results and web_results.results
        
        if not has_doc_results and not has_web_results:
            return RAGResponse(
                question=question,
                answer="I couldn't find relevant information to answer this question. Please try rephrasing or ensure the documentation has been indexed.",
                sources=[],
                doc_sources=[],
                web_sources=[],
                context_used="",
                model=self.model,
                tokens_used=0,
                include_web=include_web
            )
        
        # Build combined context
        context, doc_sources, web_sources = self._build_combined_context(
            doc_results,
            web_results,
            max_doc_results=top_k,
            max_web_results=3
        )
        
        # Generate answer
        return self.generate_answer(question, context, doc_sources, web_sources)
    
    def ask_docs_only(
        self,
        question: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """Ask a question using only documentation (no web search)."""
        return self.ask(question, top_k, filter, include_web=False)
    
    def is_web_search_available(self) -> bool:
        """Check if web search is available."""
        return (
            self.web_search_service is not None and 
            self.web_search_service.is_available()
        )
