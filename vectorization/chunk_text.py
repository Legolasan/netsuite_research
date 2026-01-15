"""
NetSuite Documentation Vectorization - Text Chunking Module

This module handles splitting extracted PDF text into chunks suitable for embeddings.
"""

import re
import hashlib
from typing import List, Generator, Optional
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

from config import get_config, ProcessingConfig
from extract_pdfs import PDFDocument, PDFPage


@dataclass
class TextChunk:
    """Represents a chunk of text ready for embedding."""
    chunk_id: str
    text: str
    token_count: int
    metadata: dict = field(default_factory=dict)
    
    def __repr__(self):
        return f"TextChunk(id='{self.chunk_id[:8]}...', tokens={self.token_count})"
    
    def to_pinecone_format(self) -> dict:
        """Convert to Pinecone upsert format."""
        return {
            "id": self.chunk_id,
            "metadata": {
                **self.metadata,
                "text": self.text[:1000],  # Store truncated text in metadata
                "token_count": self.token_count
            }
        }


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text: Text to count tokens for
        model: Tokenizer model name
        
    Returns:
        Token count
    """
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate
        return len(text) // 4


def generate_chunk_id(source_file: str, chunk_index: int, text: str) -> str:
    """
    Generate a unique, deterministic ID for a text chunk.
    
    Args:
        source_file: Source filename
        chunk_index: Index of chunk within document
        text: Chunk text content
        
    Returns:
        Unique chunk ID
    """
    content = f"{source_file}:{chunk_index}:{text[:100]}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def create_text_splitter(config: Optional[ProcessingConfig] = None) -> RecursiveCharacterTextSplitter:
    """
    Create a text splitter with configured chunk size and overlap.
    
    Args:
        config: Optional processing config (uses defaults if not provided)
        
    Returns:
        Configured text splitter
    """
    if config is None:
        config = get_config().processing
    
    return RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        length_function=count_tokens,
        separators=[
            "\n\n\n",  # Multiple newlines (section breaks)
            "\n\n",    # Paragraph breaks
            "\n",      # Line breaks
            ". ",      # Sentence endings
            ", ",      # Clause breaks
            " ",       # Word breaks
            ""         # Character breaks (last resort)
        ]
    )


def chunk_document(
    document: PDFDocument,
    config: Optional[ProcessingConfig] = None
) -> Generator[TextChunk, None, None]:
    """
    Split a PDF document into chunks.
    
    Args:
        document: PDFDocument to chunk
        config: Optional processing configuration
        
    Yields:
        TextChunk objects
    """
    splitter = create_text_splitter(config)
    
    # Split the document text
    chunks = splitter.split_text(document.text)
    
    for i, chunk_text in enumerate(chunks):
        chunk_id = generate_chunk_id(document.filename, i, chunk_text)
        token_count = count_tokens(chunk_text)
        
        yield TextChunk(
            chunk_id=chunk_id,
            text=chunk_text,
            token_count=token_count,
            metadata={
                **document.metadata,
                "source_file": document.filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "page_count": document.page_count
            }
        )


def chunk_page(
    page: PDFPage,
    config: Optional[ProcessingConfig] = None
) -> Generator[TextChunk, None, None]:
    """
    Split a single PDF page into chunks.
    
    Args:
        page: PDFPage to chunk
        config: Optional processing configuration
        
    Yields:
        TextChunk objects
    """
    splitter = create_text_splitter(config)
    
    # For single pages, we might not need to split if under chunk size
    token_count = count_tokens(page.text)
    
    if token_count <= (config or get_config().processing).chunk_size:
        # Page fits in one chunk
        chunk_id = generate_chunk_id(page.filename, page.page_number, page.text)
        yield TextChunk(
            chunk_id=chunk_id,
            text=page.text,
            token_count=token_count,
            metadata={
                **page.metadata,
                "source_file": page.filename,
                "page_number": page.page_number,
                "chunk_index": 0,
                "total_chunks": 1
            }
        )
    else:
        # Split the page
        chunks = splitter.split_text(page.text)
        for i, chunk_text in enumerate(chunks):
            chunk_id = generate_chunk_id(f"{page.filename}:p{page.page_number}", i, chunk_text)
            yield TextChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                token_count=count_tokens(chunk_text),
                metadata={
                    **page.metadata,
                    "source_file": page.filename,
                    "page_number": page.page_number,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )


def chunk_documents(
    documents: List[PDFDocument],
    config: Optional[ProcessingConfig] = None
) -> Generator[TextChunk, None, None]:
    """
    Chunk multiple documents.
    
    Args:
        documents: List of PDFDocuments
        config: Optional processing configuration
        
    Yields:
        TextChunk objects from all documents
    """
    for doc in documents:
        yield from chunk_document(doc, config)


def estimate_total_chunks(documents: List[PDFDocument], config: Optional[ProcessingConfig] = None) -> dict:
    """
    Estimate the total number of chunks and tokens for a list of documents.
    
    Args:
        documents: List of PDFDocuments
        config: Optional processing configuration
        
    Returns:
        Dictionary with estimation stats
    """
    if config is None:
        config = get_config().processing
    
    total_chars = sum(len(doc.text) for doc in documents)
    total_tokens = sum(count_tokens(doc.text) for doc in documents)
    
    # Rough estimate: chunks = tokens / chunk_size * overlap_factor
    overlap_factor = 1.2  # Account for overlap
    estimated_chunks = int((total_tokens / config.chunk_size) * overlap_factor)
    
    return {
        "total_documents": len(documents),
        "total_characters": total_chars,
        "total_tokens": total_tokens,
        "estimated_chunks": estimated_chunks,
        "chunk_size": config.chunk_size,
        "chunk_overlap": config.chunk_overlap,
        "estimated_embedding_cost_usd": (total_tokens / 1_000_000) * 0.02  # text-embedding-3-small pricing
    }


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from extract_pdfs import extract_all_pdfs
    
    console = Console()
    
    # Extract and estimate
    console.print("[blue]Extracting PDFs for chunk estimation...[/blue]")
    documents = list(extract_all_pdfs())
    
    stats = estimate_total_chunks(documents)
    
    table = Table(title="Chunking Estimation")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Documents", str(stats["total_documents"]))
    table.add_row("Total Characters", f"{stats['total_characters']:,}")
    table.add_row("Total Tokens", f"{stats['total_tokens']:,}")
    table.add_row("Estimated Chunks", f"{stats['estimated_chunks']:,}")
    table.add_row("Chunk Size", str(stats["chunk_size"]))
    table.add_row("Chunk Overlap", str(stats["chunk_overlap"]))
    table.add_row("Est. Embedding Cost", f"${stats['estimated_embedding_cost_usd']:.4f}")
    
    console.print(table)
