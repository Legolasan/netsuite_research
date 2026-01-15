"""
Chat Service - RAG-powered chat over NetSuite documentation

Adapted from vectorization/rag_helper.py for web application use.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from openai import OpenAI
from dotenv import load_dotenv

from .search import SearchService, SearchResponse

# Load environment variables
load_dotenv()


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


class ChatService:
    """RAG chat service for NetSuite documentation Q&A."""
    
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
    
    def retrieve_context(
        self,
        question: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Retrieve relevant context for a question."""
        return self.search_service.search(question, top_k=top_k, filter=filter)
    
    def generate_answer(
        self,
        question: str,
        context: str,
        sources: List[str]
    ) -> RAGResponse:
        """Generate an answer using GPT with the retrieved context."""
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
        
        Args:
            question: Natural language question
            top_k: Number of context chunks to retrieve
            filter: Optional metadata filter for context
            
        Returns:
            RAGResponse with answer and sources
        """
        # Retrieve context
        search_results = self.retrieve_context(question, top_k, filter)
        
        if not search_results.results:
            return RAGResponse(
                question=question,
                answer="I couldn't find relevant documentation to answer this question. Please try rephrasing or ensure the documentation has been indexed.",
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
