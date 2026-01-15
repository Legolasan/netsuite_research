"""
NetSuite Research Documents Extraction Module

This module handles extracting text from JSON and Markdown research documents
for vectorization, enabling RAG queries about analyzed connector capabilities.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Generator, Optional, Any
from dataclasses import dataclass

from tqdm import tqdm
from rich.console import Console

console = Console()


@dataclass
class ResearchDocument:
    """Represents an extracted research document."""
    filename: str
    filepath: Path
    text: str
    doc_type: str  # 'json' or 'markdown'
    metadata: Dict[str, str]
    
    def __repr__(self):
        return f"ResearchDocument(filename='{self.filename}', type={self.doc_type}, chars={len(self.text)})"


# Mapping of directory names to categories
RESEARCH_CATEGORIES = {
    "01_objects": {"category": "OBJECTS", "description": "NetSuite object catalog and implementation status"},
    "02_relations": {"category": "RELATIONS", "description": "Object relationships and ERD"},
    "03_permissions": {"category": "PERMISSIONS", "description": "Permission matrix and role requirements"},
    "04_replication": {"category": "REPLICATION", "description": "Replication methods and incremental sync"},
    "05_api_limits": {"category": "GOVERNANCE", "description": "API governance and rate limits"},
    "06_operations": {"category": "OPERATIONS", "description": "Supported API operations"},
    "07_summary": {"category": "SUMMARY", "description": "Gap analysis and improvement roadmap"},
    "08_technical": {"category": "TECHNICAL", "description": "Technical implementation details"},
}


def get_research_category(filepath: Path) -> Dict[str, str]:
    """
    Determine category based on file path.
    
    Args:
        filepath: Path to the research document
        
    Returns:
        Category metadata
    """
    path_str = str(filepath)
    
    for dir_name, cat_info in RESEARCH_CATEGORIES.items():
        if dir_name in path_str:
            return {
                "doc_category": cat_info["category"],
                "category_description": cat_info["description"],
            }
    
    return {
        "doc_category": "RESEARCH",
        "category_description": "Research documentation",
    }


def json_to_text(data: Any, prefix: str = "", depth: int = 0) -> str:
    """
    Convert JSON data to readable text format.
    
    Args:
        data: JSON data (dict, list, or primitive)
        prefix: Current key path prefix
        depth: Current nesting depth
        
    Returns:
        Text representation
    """
    lines = []
    indent = "  " * depth
    
    if isinstance(data, dict):
        for key, value in data.items():
            key_label = key.replace("_", " ").title()
            
            if isinstance(value, dict):
                lines.append(f"{indent}{key_label}:")
                lines.append(json_to_text(value, f"{prefix}.{key}", depth + 1))
            elif isinstance(value, list):
                if len(value) == 0:
                    lines.append(f"{indent}{key_label}: (empty)")
                elif all(isinstance(item, str) for item in value):
                    # Simple string list
                    items_str = ", ".join(str(v) for v in value[:20])
                    if len(value) > 20:
                        items_str += f" ... (+{len(value) - 20} more)"
                    lines.append(f"{indent}{key_label}: {items_str}")
                elif all(isinstance(item, dict) for item in value):
                    # List of objects
                    lines.append(f"{indent}{key_label} ({len(value)} items):")
                    for i, item in enumerate(value[:10]):  # Show first 10
                        lines.append(json_to_text(item, f"{prefix}.{key}[{i}]", depth + 1))
                    if len(value) > 10:
                        lines.append(f"{indent}  ... and {len(value) - 10} more items")
                else:
                    lines.append(f"{indent}{key_label}: {value}")
            else:
                lines.append(f"{indent}{key_label}: {value}")
    
    elif isinstance(data, list):
        for i, item in enumerate(data[:10]):
            lines.append(json_to_text(item, f"{prefix}[{i}]", depth))
        if len(data) > 10:
            lines.append(f"{indent}... and {len(data) - 10} more items")
    
    else:
        lines.append(f"{indent}{data}")
    
    return "\n".join(lines)


def extract_json_document(filepath: Path) -> Optional[ResearchDocument]:
    """
    Extract text from a JSON research document.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        ResearchDocument or None if extraction fails
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get category metadata
        category_meta = get_research_category(filepath)
        
        # Create metadata
        metadata = {
            "source_type": "research",
            "doc_type": "json",
            "source_file": filepath.name,
            "file_path": str(filepath),
            **category_meta,
        }
        
        # Extract key sections for metadata
        if isinstance(data, dict):
            if "metadata" in data:
                doc_meta = data.get("metadata", {})
                metadata["doc_version"] = str(doc_meta.get("version", ""))
                metadata["generated"] = str(doc_meta.get("generated", ""))
            
            if "summary" in data:
                summary = data.get("summary", {})
                if isinstance(summary, dict):
                    metadata["total_objects"] = str(summary.get("total_objects", ""))
        
        # Create text summary header
        header_lines = [
            f"# NetSuite Research Document: {filepath.stem}",
            f"Category: {category_meta['doc_category']}",
            f"Description: {category_meta['category_description']}",
            f"File: {filepath.name}",
            "",
            "## Content",
            "",
        ]
        header = "\n".join(header_lines)
        
        # Convert JSON to readable text
        content_text = json_to_text(data)
        
        full_text = header + content_text
        
        return ResearchDocument(
            filename=filepath.name,
            filepath=filepath,
            text=full_text,
            doc_type="json",
            metadata=metadata
        )
    
    except Exception as e:
        console.print(f"[red]Error extracting JSON {filepath.name}: {e}[/red]")
        return None


def extract_markdown_document(filepath: Path) -> Optional[ResearchDocument]:
    """
    Extract text from a Markdown research document.
    
    Args:
        filepath: Path to Markdown file
        
    Returns:
        ResearchDocument or None if extraction fails
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) < 50:  # Skip nearly empty files
            return None
        
        # Get category metadata
        category_meta = get_research_category(filepath)
        
        # Create metadata
        metadata = {
            "source_type": "research",
            "doc_type": "markdown",
            "source_file": filepath.name,
            "file_path": str(filepath),
            **category_meta,
        }
        
        # Extract title from first heading
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        # Count sections
        section_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
        metadata["section_count"] = str(section_count)
        
        # Add document header for context
        header_lines = [
            f"NetSuite Research Document: {filepath.stem}",
            f"Category: {category_meta['doc_category']}",
            f"Type: Markdown Documentation",
            "",
        ]
        header = "\n".join(header_lines)
        
        # Clean up markdown slightly
        cleaned_content = content.strip()
        
        full_text = header + cleaned_content
        
        return ResearchDocument(
            filename=filepath.name,
            filepath=filepath,
            text=full_text,
            doc_type="markdown",
            metadata=metadata
        )
    
    except Exception as e:
        console.print(f"[red]Error extracting Markdown {filepath.name}: {e}[/red]")
        return None


def find_research_files(directory: Path, recursive: bool = True) -> List[Path]:
    """
    Find all JSON and Markdown files in the research directory.
    
    Args:
        directory: Directory to search
        recursive: Whether to search recursively
        
    Returns:
        List of file paths
    """
    files = []
    
    pattern = "**/*" if recursive else "*"
    
    for filepath in directory.glob(pattern):
        if filepath.is_file():
            # Include JSON and Markdown files
            if filepath.suffix.lower() in ['.json', '.md']:
                # Exclude certain files
                if filepath.name.lower() not in ['package.json', 'package-lock.json', 'readme.md']:
                    # Exclude files in certain directories
                    path_str = str(filepath).lower()
                    if 'node_modules' not in path_str and 'venv' not in path_str and '.git' not in path_str:
                        files.append(filepath)
    
    files.sort(key=lambda p: (p.parent.name, p.name.lower()))
    return files


def extract_all_research(
    directory: Path,
    progress: bool = True
) -> Generator[ResearchDocument, None, None]:
    """
    Extract text from all research documents in a directory.
    
    Args:
        directory: Directory containing research documents
        progress: Whether to show progress bar
        
    Yields:
        ResearchDocument objects
    """
    research_files = find_research_files(directory)
    
    console.print(f"[blue]Found {len(research_files)} research documents in {directory}[/blue]")
    
    iterator = tqdm(research_files, desc="Extracting research docs") if progress else research_files
    
    for filepath in iterator:
        if filepath.suffix.lower() == '.json':
            doc = extract_json_document(filepath)
        elif filepath.suffix.lower() == '.md':
            doc = extract_markdown_document(filepath)
        else:
            continue
        
        if doc:
            yield doc


def get_research_extraction_stats(directory: Path) -> Dict:
    """
    Get statistics about research document extraction.
    
    Args:
        directory: Directory to analyze
        
    Returns:
        Dictionary with statistics
    """
    research_files = find_research_files(directory)
    
    stats = {
        "total_files": len(research_files),
        "json_files": sum(1 for f in research_files if f.suffix.lower() == '.json'),
        "markdown_files": sum(1 for f in research_files if f.suffix.lower() == '.md'),
        "categories": {},
        "sample_files": [f.name for f in research_files[:10]]
    }
    
    # Categorize files
    for filepath in research_files:
        cat_info = get_research_category(filepath)
        cat = cat_info["doc_category"]
        stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
    
    return stats


if __name__ == "__main__":
    # Test extraction
    import sys
    
    if len(sys.argv) > 1:
        test_dir = Path(sys.argv[1])
    else:
        test_dir = Path(__file__).parent.parent
    
    if test_dir.exists():
        stats = get_research_extraction_stats(test_dir)
        console.print(f"\n[bold]Research Document Stats for {test_dir}[/bold]")
        console.print(f"Total files: {stats['total_files']}")
        console.print(f"JSON files: {stats['json_files']}")
        console.print(f"Markdown files: {stats['markdown_files']}")
        console.print(f"Categories: {stats['categories']}")
        console.print(f"Sample files: {stats['sample_files'][:5]}")
    else:
        console.print(f"[red]Directory not found: {test_dir}[/red]")
