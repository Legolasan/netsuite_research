"""
NetSuite Documentation Vectorization - Main Vectorization Module

This module handles the complete pipeline from multiple sources to Pinecone vectors.
Supports: PDFs, Java code files, and research documents (JSON/MD).
"""

import os
import time
from typing import List, Optional, Generator, Union
from dataclasses import dataclass
from enum import Enum

from openai import OpenAI
from pinecone import Pinecone
from pinecone import ServerlessSpec
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from config import get_config, Config
from extract_pdfs import extract_all_pdfs, PDFDocument
from extract_code import extract_all_code, CodeDocument
from extract_research import extract_all_research, ResearchDocument
from chunk_text import chunk_document, chunk_code_document, chunk_research_document, TextChunk, estimate_total_chunks


class SourceType(Enum):
    """Types of document sources."""
    PDF = "pdf"
    CODE = "code"
    RESEARCH = "research"
    ALL = "all"

console = Console()


@dataclass
class VectorizationStats:
    """Statistics from vectorization run."""
    documents_processed: int = 0
    chunks_created: int = 0
    vectors_upserted: int = 0
    errors: int = 0
    total_tokens: int = 0
    duration_seconds: float = 0.0


class NetSuiteVectorizer:
    """Main class for vectorizing NetSuite documentation."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the vectorizer with configuration.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
        """
        self.config = config or get_config()
        self._validate_config()
        
        # Initialize clients
        self.openai_client = OpenAI(api_key=self.config.openai.api_key)
        self.pinecone_client = Pinecone(api_key=self.config.pinecone.api_key)
        
        # Index reference (initialized lazily)
        self._index = None
    
    def _validate_config(self):
        """Validate configuration before proceeding."""
        errors = self.config.validate()
        if errors:
            for error in errors:
                console.print(f"[red]Configuration Error: {error}[/red]")
            raise ValueError("Configuration validation failed")
    
    @property
    def index(self):
        """Get or create Pinecone index."""
        if self._index is None:
            self._ensure_index_exists()
            self._index = self.pinecone_client.Index(self.config.pinecone.index_name)
        return self._index
    
    def _ensure_index_exists(self):
        """Create Pinecone index if it doesn't exist."""
        try:
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
        except Exception:
            # Fallback for different API versions
            index_names = []
        
        if self.config.pinecone.index_name not in index_names:
            console.print(f"[yellow]Creating Pinecone index: {self.config.pinecone.index_name}[/yellow]")
            
            try:
                self.pinecone_client.create_index(
                    name=self.config.pinecone.index_name,
                    dimension=self.config.pinecone.dimension,
                    metric=self.config.pinecone.metric,
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.config.pinecone.environment
                    )
                )
            except Exception as e:
                # Index might already exist or different error
                console.print(f"[yellow]Note: {e}[/yellow]")
            
            # Wait for index to be ready
            console.print("[yellow]Waiting for index to be ready...[/yellow]")
            time.sleep(10)
            
            console.print(f"[green]Index '{self.config.pinecone.index_name}' created successfully[/green]")
        else:
            console.print(f"[blue]Using existing index: {self.config.pinecone.index_name}[/blue]")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.openai_client.embeddings.create(
            model=self.config.openai.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        response = self.openai_client.embeddings.create(
            model=self.config.openai.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def upsert_chunks(self, chunks: List[TextChunk]) -> int:
        """
        Upsert chunks with embeddings to Pinecone.
        
        Args:
            chunks: List of TextChunks to upsert
            
        Returns:
            Number of vectors upserted
        """
        if not chunks:
            return 0
        
        # Generate embeddings in batch
        texts = [chunk.text for chunk in chunks]
        embeddings = self.generate_embeddings_batch(texts)
        
        # Prepare vectors for upsert
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vectors.append({
                "id": chunk.chunk_id,
                "values": embedding,
                "metadata": {
                    **chunk.metadata,
                    "text": chunk.text[:1000]  # Store truncated text
                }
            })
        
        # Upsert to Pinecone
        self.index.upsert(vectors=vectors)
        
        return len(vectors)
    
    def vectorize_document(self, document: Union[PDFDocument, CodeDocument, ResearchDocument]) -> int:
        """
        Vectorize a single document (PDF, Code, or Research).
        
        Args:
            document: Document to vectorize (PDFDocument, CodeDocument, or ResearchDocument)
            
        Returns:
            Number of vectors created
        """
        # Choose appropriate chunking function based on document type
        if isinstance(document, CodeDocument):
            chunks = list(chunk_code_document(document, self.config.processing))
        elif isinstance(document, ResearchDocument):
            chunks = list(chunk_research_document(document, self.config.processing))
        else:
            chunks = list(chunk_document(document, self.config.processing))
        
        if not chunks:
            return 0
        
        # Process in batches
        batch_size = self.config.processing.batch_size
        total_upserted = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            total_upserted += self.upsert_chunks(batch)
            
            # Small delay to respect rate limits
            time.sleep(0.1)
        
        return total_upserted
    
    def vectorize_all(
        self,
        documents: Optional[List[Union[PDFDocument, CodeDocument, ResearchDocument]]] = None,
        max_documents: Optional[int] = None,
        source_type: SourceType = SourceType.PDF
    ) -> VectorizationStats:
        """
        Vectorize all documents from the specified source type.
        
        Args:
            documents: Optional pre-extracted documents (extracts if not provided)
            max_documents: Optional limit on number of documents to process
            source_type: Type of documents to process (PDF, CODE, RESEARCH, ALL)
            
        Returns:
            VectorizationStats with processing results
        """
        start_time = time.time()
        stats = VectorizationStats()
        
        # Extract documents if not provided
        if documents is None:
            documents = []
            
            if source_type in [SourceType.PDF, SourceType.ALL]:
                console.print("[blue]Extracting PDF documents...[/blue]")
                try:
                    documents.extend(list(extract_all_pdfs()))
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not extract PDFs: {e}[/yellow]")
            
            if source_type in [SourceType.CODE, SourceType.ALL]:
                console.print("[blue]Extracting Java code files...[/blue]")
                code_errors = self.config.validate_code_source()
                if not code_errors:
                    documents.extend(list(extract_all_code(self.config.code_source_dir)))
                else:
                    console.print(f"[yellow]Warning: {code_errors[0]}[/yellow]")
            
            if source_type in [SourceType.RESEARCH, SourceType.ALL]:
                console.print("[blue]Extracting research documents...[/blue]")
                research_errors = self.config.validate_research_source()
                if not research_errors:
                    documents.extend(list(extract_all_research(self.config.research_source_dir)))
                else:
                    console.print(f"[yellow]Warning: {research_errors[0]}[/yellow]")
        
        if max_documents:
            documents = documents[:max_documents]
        
        if not documents:
            console.print("[yellow]No documents found to process.[/yellow]")
            return stats
        
        console.print(f"[blue]Processing {len(documents)} documents...[/blue]")
        
        # Show estimation
        estimation = estimate_total_chunks(documents, self.config.processing)
        console.print(f"[dim]Estimated chunks: {estimation['estimated_chunks']:,}[/dim]")
        console.print(f"[dim]Estimated cost: ${estimation['estimated_embedding_cost_usd']:.4f}[/dim]")
        
        # Process documents with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Vectorizing...", total=len(documents))
            
            for doc in documents:
                try:
                    vectors_created = self.vectorize_document(doc)
                    stats.documents_processed += 1
                    stats.vectors_upserted += vectors_created
                    
                except Exception as e:
                    console.print(f"[red]Error processing {doc.filename}: {e}[/red]")
                    stats.errors += 1
                
                progress.update(task, advance=1)
        
        stats.duration_seconds = time.time() - start_time
        
        return stats
    
    def get_index_stats(self) -> dict:
        """Get statistics about the Pinecone index."""
        return self.index.describe_index_stats()
    
    def delete_all_vectors(self):
        """Delete all vectors from the index (use with caution)."""
        console.print("[yellow]Deleting all vectors from index...[/yellow]")
        self.index.delete(delete_all=True)
        console.print("[green]All vectors deleted[/green]")


def print_stats(stats: VectorizationStats):
    """Print vectorization statistics."""
    table = Table(title="Vectorization Complete")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Documents Processed", str(stats.documents_processed))
    table.add_row("Vectors Upserted", f"{stats.vectors_upserted:,}")
    table.add_row("Errors", str(stats.errors))
    table.add_row("Duration", f"{stats.duration_seconds:.1f} seconds")
    table.add_row("Rate", f"{stats.vectors_upserted / max(stats.duration_seconds, 1):.1f} vectors/sec")
    
    console.print(table)


def main():
    """Main entry point for vectorization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vectorize NetSuite documentation")
    parser.add_argument("--max-docs", type=int, help="Maximum number of documents to process")
    parser.add_argument("--dry-run", action="store_true", help="Show estimation without processing")
    parser.add_argument("--delete-all", action="store_true", help="Delete all vectors before processing")
    parser.add_argument(
        "--source", 
        type=str, 
        choices=["pdf", "code", "research", "all"],
        default="all",
        help="Source type to vectorize (default: all)"
    )
    args = parser.parse_args()
    
    # Map string to enum
    source_map = {
        "pdf": SourceType.PDF,
        "code": SourceType.CODE,
        "research": SourceType.RESEARCH,
        "all": SourceType.ALL,
    }
    source_type = source_map[args.source]
    
    try:
        vectorizer = NetSuiteVectorizer()
        
        if args.dry_run:
            # Collect documents for estimation
            documents = []
            config = get_config()
            
            if source_type in [SourceType.PDF, SourceType.ALL]:
                console.print("[blue]Checking PDFs...[/blue]")
                try:
                    documents.extend(list(extract_all_pdfs()))
                except Exception as e:
                    console.print(f"[yellow]PDF extraction skipped: {e}[/yellow]")
            
            if source_type in [SourceType.CODE, SourceType.ALL]:
                console.print("[blue]Checking code files...[/blue]")
                if config.code_source_dir.exists():
                    documents.extend(list(extract_all_code(config.code_source_dir)))
            
            if source_type in [SourceType.RESEARCH, SourceType.ALL]:
                console.print("[blue]Checking research docs...[/blue]")
                if config.research_source_dir.exists():
                    documents.extend(list(extract_all_research(config.research_source_dir)))
            
            estimation = estimate_total_chunks(documents)
            
            table = Table(title=f"Dry Run Estimation (source: {args.source})")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Documents", str(len(documents)))
            for key, value in estimation.items():
                if isinstance(value, float):
                    table.add_row(key, f"{value:.4f}")
                else:
                    table.add_row(key, f"{value:,}" if isinstance(value, int) else str(value))
            
            console.print(table)
            
            # Show breakdown by type
            pdf_count = sum(1 for d in documents if isinstance(d, PDFDocument))
            code_count = sum(1 for d in documents if isinstance(d, CodeDocument))
            research_count = sum(1 for d in documents if isinstance(d, ResearchDocument))
            
            console.print(f"\n[dim]Breakdown: {pdf_count} PDFs, {code_count} code files, {research_count} research docs[/dim]")
            return
        
        if args.delete_all:
            vectorizer.delete_all_vectors()
        
        console.print(f"\n[bold blue]Starting vectorization (source: {args.source})[/bold blue]\n")
        stats = vectorizer.vectorize_all(max_documents=args.max_docs, source_type=source_type)
        print_stats(stats)
        
        # Show index stats
        index_stats = vectorizer.get_index_stats()
        console.print(f"\n[blue]Index Stats:[/blue] {index_stats}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
