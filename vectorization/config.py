"""
NetSuite Documentation Vectorization - Configuration Module

This module handles configuration management for the vectorization pipeline.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    embedding_dimension: int = 1536  # text-embedding-3-small dimension


@dataclass
class PineconeConfig:
    """Pinecone vector database configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("PINECONE_API_KEY", ""))
    environment: str = field(default_factory=lambda: os.getenv("PINECONE_ENVIRONMENT", "us-east-1"))
    index_name: str = field(default_factory=lambda: os.getenv("PINECONE_INDEX_NAME", "netsuite-docs"))
    metric: str = "cosine"
    dimension: int = 1536


@dataclass
class ProcessingConfig:
    """Text processing configuration."""
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200")))
    batch_size: int = field(default_factory=lambda: int(os.getenv("BATCH_SIZE", "100")))


@dataclass
class Config:
    """Main configuration class."""
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    pinecone: PineconeConfig = field(default_factory=PineconeConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    pdf_source_dir: Path = field(default_factory=lambda: Path(os.getenv("PDF_SOURCE_DIR", "../../")).resolve())
    
    def __post_init__(self):
        """Resolve paths after initialization."""
        if not self.pdf_source_dir.is_absolute():
            self.pdf_source_dir = (Path(__file__).parent / self.pdf_source_dir).resolve()
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.openai.api_key:
            errors.append("OPENAI_API_KEY is not set")
        
        if not self.pinecone.api_key:
            errors.append("PINECONE_API_KEY is not set")
        
        if not self.pdf_source_dir.exists():
            errors.append(f"PDF source directory does not exist: {self.pdf_source_dir}")
        
        return errors


# Document categories for metadata
DOC_CATEGORIES = {
    "SOAP": ["SOAP Web Services", "SuiteTalk"],
    "REST": ["REST Web Services", "REST API"],
    "GOVERNANCE": ["Governance", "Concurrency", "Limits", "Rate"],
    "PERMISSION": ["Permission", "Role", "Access"],
    "RECORD": ["Record", "Entity", "Transaction", "Item"],
    "SEARCH": ["Search", "Query", "SuiteQL"],
    "CUSTOM": ["Custom Record", "Custom Field", "Customization"],
}

# Object type keywords for metadata extraction
OBJECT_KEYWORDS = [
    "Customer", "Vendor", "Employee", "Contact", "Partner",
    "Invoice", "SalesOrder", "PurchaseOrder", "CreditMemo",
    "Item", "InventoryItem", "AssemblyItem", "ServiceItem",
    "Account", "Department", "Location", "Subsidiary",
    "Transaction", "JournalEntry", "Payment", "Deposit",
]


def get_config() -> Config:
    """Get configuration instance."""
    return Config()


def categorize_document(filename: str, content: str = "") -> dict:
    """
    Categorize a document based on filename and content.
    
    Args:
        filename: Name of the PDF file
        content: Optional text content for better categorization
        
    Returns:
        Dictionary with category and object_type metadata
    """
    filename_lower = filename.lower()
    content_lower = content.lower() if content else ""
    
    # Determine category
    category = "GENERAL"
    for cat, keywords in DOC_CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in filename_lower or keyword.lower() in content_lower[:500]:
                category = cat
                break
        if category != "GENERAL":
            break
    
    # Determine object type
    object_type = "General"
    for obj in OBJECT_KEYWORDS:
        if obj.lower() in filename_lower:
            object_type = obj
            break
    
    # Check for REST suffix
    if "_rest" in filename_lower or "rest." in filename_lower:
        category = "REST" if category == "GENERAL" else category
    
    return {
        "doc_category": category,
        "object_type": object_type
    }
