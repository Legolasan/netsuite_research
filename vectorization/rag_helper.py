"""
NetSuite Documentation Vectorization - RAG Helper Module

This module provides Retrieval Augmented Generation (RAG) capabilities
for answering questions about NetSuite documentation.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import get_config, Config
from query_docs import NetSuiteDocSearch, SearchResponse

console = Console()


# System prompt for NetSuite documentation Q&A
SYSTEM_PROMPT = """You are a NetSuite documentation expert assistant. Your role is to answer questions about NetSuite APIs, objects, integrations, and best practices based on the provided documentation context.

Guidelines:
1. Only answer based on the provided context. If the context doesn't contain relevant information, say so.
2. Be specific and cite the source documents when possible.
3. For technical questions, provide code examples when relevant.
4. Highlight any important warnings, limitations, or governance considerations.
5. If asked about API limits or permissions, be precise about the requirements.

Format your responses in a clear, structured manner using:
- Headers for different sections
- Bullet points for lists
- Code blocks for API examples
- Tables for comparing options when appropriate"""


@dataclass
class RAGResponse:
    """Represents a RAG-generated response."""
    question: str
    answer: str
    sources: List[str]
    context_used: str
    model: str
    tokens_used: int


class NetSuiteRAG:
    """RAG interface for NetSuite documentation Q&A."""
    
    def __init__(
        self,
        config: Optional[Config] = None,
        model: str = "gpt-4o",
        temperature: float = 0.1
    ):
        """
        Initialize the RAG helper.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
            model: OpenAI model for generation
            temperature: Generation temperature (lower = more focused)
        """
        self.config = config or get_config()
        self.model = model
        self.temperature = temperature
        
        self.openai_client = OpenAI(api_key=self.config.openai.api_key)
        self.searcher = NetSuiteDocSearch(self.config)
    
    def retrieve_context(
        self,
        question: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """
        Retrieve relevant context for a question.
        
        Args:
            question: User question
            top_k: Number of context chunks to retrieve
            filter: Optional metadata filter
            
        Returns:
            SearchResponse with relevant chunks
        """
        return self.searcher.search(question, top_k=top_k, filter=filter)
    
    def generate_answer(
        self,
        question: str,
        context: str,
        sources: List[str]
    ) -> RAGResponse:
        """
        Generate an answer using GPT with the retrieved context.
        
        Args:
            question: User question
            context: Retrieved documentation context
            sources: List of source document names
            
        Returns:
            RAGResponse with generated answer
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Based on the following NetSuite documentation context, please answer the question.

DOCUMENTATION CONTEXT:
{context}

QUESTION: {question}

Please provide a comprehensive answer based on the documentation above."""}
        ]
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        return RAGResponse(
            question=question,
            answer=answer,
            sources=sources,
            context_used=context[:500] + "..." if len(context) > 500 else context,
            model=self.model,
            tokens_used=tokens_used
        )
    
    def ask(
        self,
        question: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        Ask a question about NetSuite documentation.
        
        This method retrieves relevant context and generates an answer.
        
        Args:
            question: Natural language question
            top_k: Number of context chunks to retrieve
            filter: Optional metadata filter for context
            
        Returns:
            RAGResponse with answer and sources
            
        Example:
            >>> rag = NetSuiteRAG()
            >>> response = rag.ask("What are the SOAP API rate limits?")
            >>> print(response.answer)
        """
        # Retrieve context
        search_results = self.retrieve_context(question, top_k, filter)
        
        if not search_results.results:
            return RAGResponse(
                question=question,
                answer="I couldn't find relevant documentation to answer this question. Please try rephrasing or check if the documentation has been vectorized.",
                sources=[],
                context_used="",
                model=self.model,
                tokens_used=0
            )
        
        # Build context string
        context = search_results.to_context_string(max_results=top_k)
        sources = list(set(r.source_file for r in search_results.results))
        
        # Generate answer
        return self.generate_answer(question, context, sources)
    
    def ask_about_object(
        self,
        question: str,
        object_type: str,
        top_k: int = 5
    ) -> RAGResponse:
        """
        Ask a question about a specific NetSuite object type.
        
        Args:
            question: Question about the object
            object_type: NetSuite object type (Customer, Invoice, etc.)
            top_k: Number of context chunks
            
        Returns:
            RAGResponse focused on the object type
        """
        return self.ask(
            question,
            top_k=top_k,
            filter={"object_type": {"$eq": object_type}}
        )
    
    def ask_about_api(
        self,
        question: str,
        api_type: str = "SOAP",
        top_k: int = 5
    ) -> RAGResponse:
        """
        Ask a question about a specific API type.
        
        Args:
            question: Question about the API
            api_type: API type (SOAP or REST)
            top_k: Number of context chunks
            
        Returns:
            RAGResponse focused on the API type
        """
        return self.ask(
            question,
            top_k=top_k,
            filter={"doc_category": {"$eq": api_type}}
        )


def ask_netsuite(
    question: str,
    top_k: int = 5,
    filter: Optional[Dict[str, Any]] = None,
    config: Optional[Config] = None
) -> RAGResponse:
    """
    Convenience function for asking questions about NetSuite.
    
    Args:
        question: Natural language question
        top_k: Number of context chunks to retrieve
        filter: Optional metadata filter
        config: Optional configuration
        
    Returns:
        RAGResponse with answer
        
    Example:
        >>> answer = ask_netsuite("How do I implement incremental sync for Customers?")
        >>> print(answer.answer)
    """
    rag = NetSuiteRAG(config)
    return rag.ask(question, top_k, filter)


def print_rag_response(response: RAGResponse):
    """Pretty print a RAG response."""
    console.print(f"\n[bold blue]Question:[/bold blue] {response.question}\n")
    
    console.print(Panel(
        Markdown(response.answer),
        title="[bold green]Answer[/bold green]",
        border_style="green"
    ))
    
    if response.sources:
        console.print("\n[bold]Sources:[/bold]")
        for source in response.sources:
            console.print(f"  • {source}")
    
    console.print(f"\n[dim]Model: {response.model} | Tokens: {response.tokens_used}[/dim]")


def interactive_rag():
    """Run an interactive RAG Q&A session."""
    console.print("\n[bold blue]NetSuite Documentation Q&A[/bold blue]")
    console.print("[dim]Ask questions about NetSuite APIs, objects, and integrations.[/dim]")
    console.print("[dim]Type 'quit' to exit[/dim]\n")
    
    rag = NetSuiteRAG()
    
    while True:
        question = console.input("[green]Question:[/green] ").strip()
        
        if question.lower() in ("quit", "exit", "q"):
            break
        
        if not question:
            continue
        
        try:
            console.print("[dim]Searching and generating answer...[/dim]")
            response = rag.ask(question)
            print_rag_response(response)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NetSuite Documentation Q&A")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--top-k", type=int, default=5, help="Number of context chunks")
    parser.add_argument("--category", help="Filter by category (SOAP, REST, etc.)")
    parser.add_argument("--object", help="Filter by object type")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use")
    args = parser.parse_args()
    
    if args.interactive:
        interactive_rag()
    elif args.question:
        filter_dict = {}
        if args.category:
            filter_dict["doc_category"] = {"$eq": args.category}
        if args.object:
            filter_dict["object_type"] = {"$eq": args.object}
        
        rag = NetSuiteRAG(model=args.model)
        response = rag.ask(
            args.question,
            top_k=args.top_k,
            filter=filter_dict if filter_dict else None
        )
        print_rag_response(response)
    else:
        parser.print_help()
