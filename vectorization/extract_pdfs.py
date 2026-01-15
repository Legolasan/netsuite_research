"""
NetSuite Documentation Vectorization - PDF Text Extraction Module

This module handles extracting text from PDF files in the NetSuite documentation folder.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Generator, Optional
from dataclasses import dataclass

from pypdf import PdfReader
from tqdm import tqdm
from rich.console import Console
from rich.table import Table

from config import get_config, categorize_document

console = Console()


@dataclass
class PDFDocument:
    """Represents an extracted PDF document."""
    filename: str
    filepath: Path
    text: str
    page_count: int
    metadata: Dict[str, str]
    
    def __repr__(self):
        return f"PDFDocument(filename='{self.filename}', pages={self.page_count}, chars={len(self.text)})"


@dataclass
class PDFPage:
    """Represents a single page from a PDF."""
    filename: str
    filepath: Path
    page_number: int
    text: str
    metadata: Dict[str, str]


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing extra whitespace and artifacts.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Remove multiple newlines (keep max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove page headers/footers patterns common in NetSuite docs
    text = re.sub(r'NetSuite Applications Suite\s*-\s*', '', text)
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove non-printable characters except newlines and spaces
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    return text.strip()


def extract_pdf_text(filepath: Path) -> Optional[str]:
    """
    Extract text from a PDF file.
    
    Args:
        filepath: Path to PDF file
        
    Returns:
        Extracted text or None if extraction fails
    """
    try:
        reader = PdfReader(filepath)
        text_parts = []
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        full_text = "\n\n".join(text_parts)
        return clean_text(full_text)
    
    except Exception as e:
        console.print(f"[red]Error extracting {filepath.name}: {e}[/red]")
        return None


def extract_pdf_by_pages(filepath: Path) -> Generator[PDFPage, None, None]:
    """
    Extract text from a PDF file page by page.
    
    Args:
        filepath: Path to PDF file
        
    Yields:
        PDFPage objects for each page
    """
    try:
        reader = PdfReader(filepath)
        filename = filepath.name
        metadata = categorize_document(filename)
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                yield PDFPage(
                    filename=filename,
                    filepath=filepath,
                    page_number=i + 1,
                    text=clean_text(page_text),
                    metadata={
                        **metadata,
                        "page_number": str(i + 1),
                        "total_pages": str(len(reader.pages))
                    }
                )
    
    except Exception as e:
        console.print(f"[red]Error extracting pages from {filepath.name}: {e}[/red]")


def find_pdf_files(directory: Path, pattern: str = "*.pdf") -> List[Path]:
    """
    Find all PDF files in a directory (non-recursive by default).
    
    Args:
        directory: Directory to search
        pattern: Glob pattern for matching files
        
    Returns:
        List of PDF file paths
    """
    pdf_files = list(directory.glob(pattern))
    
    # Sort by name for consistent processing order
    pdf_files.sort(key=lambda p: p.name.lower())
    
    return pdf_files


def extract_all_pdfs(
    directory: Optional[Path] = None,
    progress: bool = True
) -> Generator[PDFDocument, None, None]:
    """
    Extract text from all PDF files in the NetSuite documentation directory.
    
    Args:
        directory: Optional custom directory (uses config default if not provided)
        progress: Whether to show progress bar
        
    Yields:
        PDFDocument objects
    """
    config = get_config()
    source_dir = directory or config.pdf_source_dir
    
    pdf_files = find_pdf_files(source_dir)
    
    console.print(f"[blue]Found {len(pdf_files)} PDF files in {source_dir}[/blue]")
    
    iterator = tqdm(pdf_files, desc="Extracting PDFs") if progress else pdf_files
    
    for filepath in iterator:
        text = extract_pdf_text(filepath)
        
        if text and len(text) > 100:  # Skip nearly empty documents
            try:
                reader = PdfReader(filepath)
                page_count = len(reader.pages)
            except:
                page_count = 0
            
            metadata = categorize_document(filepath.name, text[:1000])
            metadata["source_file"] = filepath.name
            
            yield PDFDocument(
                filename=filepath.name,
                filepath=filepath,
                text=text,
                page_count=page_count,
                metadata=metadata
            )


def get_extraction_stats(directory: Optional[Path] = None) -> Dict:
    """
    Get statistics about PDF extraction without full extraction.
    
    Args:
        directory: Optional custom directory
        
    Returns:
        Dictionary with statistics
    """
    config = get_config()
    source_dir = directory or config.pdf_source_dir
    
    pdf_files = find_pdf_files(source_dir)
    
    stats = {
        "total_files": len(pdf_files),
        "total_size_mb": sum(f.stat().st_size for f in pdf_files) / (1024 * 1024),
        "categories": {},
        "sample_files": [f.name for f in pdf_files[:10]]
    }
    
    # Categorize files by name patterns
    for filepath in pdf_files:
        cat_info = categorize_document(filepath.name)
        cat = cat_info["doc_category"]
        stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
    
    return stats


def print_extraction_summary(directory: Optional[Path] = None):
    """Print a summary of available PDFs for extraction."""
    stats = get_extraction_stats(directory)
    
    console.print("\n[bold blue]NetSuite PDF Documentation Summary[/bold blue]\n")
    
    table = Table(title="Document Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total PDF Files", str(stats["total_files"]))
    table.add_row("Total Size", f"{stats['total_size_mb']:.2f} MB")
    
    console.print(table)
    
    console.print("\n[bold]Documents by Category:[/bold]")
    cat_table = Table()
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Count", style="green")
    
    for cat, count in sorted(stats["categories"].items(), key=lambda x: -x[1]):
        cat_table.add_row(cat, str(count))
    
    console.print(cat_table)
    
    console.print("\n[bold]Sample Files:[/bold]")
    for f in stats["sample_files"]:
        console.print(f"  • {f}")


if __name__ == "__main__":
    # Run extraction summary when executed directly
    print_extraction_summary()
