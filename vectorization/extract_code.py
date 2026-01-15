"""
NetSuite Connector Code Extraction Module

This module handles extracting text from Java source code files
for vectorization, enabling RAG queries about the connector implementation.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Generator, Optional
from dataclasses import dataclass

from tqdm import tqdm
from rich.console import Console

console = Console()


@dataclass
class CodeDocument:
    """Represents an extracted code file."""
    filename: str
    filepath: Path
    text: str
    language: str
    metadata: Dict[str, str]
    
    def __repr__(self):
        return f"CodeDocument(filename='{self.filename}', lang={self.language}, chars={len(self.text)})"


def extract_java_metadata(content: str, filename: str) -> Dict[str, str]:
    """
    Extract metadata from Java source code.
    
    Args:
        content: Java source code content
        filename: Name of the file
        
    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        "language": "java",
        "source_type": "code",
        "doc_category": "CODE",
    }
    
    # Extract package name
    package_match = re.search(r'package\s+([\w.]+);', content)
    if package_match:
        metadata["package"] = package_match.group(1)
    
    # Extract class/interface/enum name
    class_match = re.search(r'(?:public\s+)?(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)', content)
    if class_match:
        metadata["class_name"] = class_match.group(1)
    
    # Determine code type
    if 'enum ' in content:
        metadata["code_type"] = "enum"
    elif 'interface ' in content:
        metadata["code_type"] = "interface"
    elif 'abstract class ' in content:
        metadata["code_type"] = "abstract_class"
    else:
        metadata["code_type"] = "class"
    
    # Categorize by connector component
    filename_lower = filename.lower()
    filepath_lower = str(filename).lower()
    
    if 'search' in filename_lower:
        metadata["connector_component"] = "search"
        metadata["object_type"] = extract_object_from_search(filename)
    elif 'record' in filename_lower or 'type' in filename_lower:
        metadata["connector_component"] = "record_type"
        metadata["object_type"] = extract_object_from_type(filename)
    elif 'objecttype' in filename_lower:
        metadata["connector_component"] = "object_definition"
    elif 'auth' in filename_lower or 'credential' in filename_lower:
        metadata["connector_component"] = "authentication"
    elif 'config' in filename_lower:
        metadata["connector_component"] = "configuration"
    elif 'util' in filename_lower or 'helper' in filename_lower:
        metadata["connector_component"] = "utility"
    else:
        metadata["connector_component"] = "core"
    
    # Extract implemented interfaces
    implements_match = re.search(r'implements\s+([\w,\s<>]+)(?:\s*\{|$)', content)
    if implements_match:
        interfaces = implements_match.group(1).strip()
        metadata["implements"] = interfaces
    
    # Extract extended class
    extends_match = re.search(r'extends\s+(\w+)', content)
    if extends_match:
        metadata["extends"] = extends_match.group(1)
    
    # Count methods
    method_count = len(re.findall(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>,\s]+\s+\w+\s*\(', content))
    metadata["method_count"] = str(method_count)
    
    # Extract enum values if it's an enum
    if metadata["code_type"] == "enum":
        enum_values = extract_enum_values(content)
        if enum_values:
            metadata["enum_values"] = ", ".join(enum_values[:20])  # First 20 values
            metadata["enum_count"] = str(len(enum_values))
    
    return metadata


def extract_object_from_search(filename: str) -> str:
    """Extract object type from search class filename."""
    # e.g., CustomerInternalSearch.java -> Customer
    match = re.match(r'(\w+?)(?:Internal)?Search\.java', filename)
    if match:
        return match.group(1)
    return "General"


def extract_object_from_type(filename: str) -> str:
    """Extract object type from record type filename."""
    # e.g., NetsuiteTransactionRecordType.java -> Transaction
    match = re.search(r'Netsuite(\w+?)RecordType\.java', filename)
    if match:
        return match.group(1)
    return "General"


def extract_enum_values(content: str) -> List[str]:
    """Extract enum constant names from Java enum."""
    # Find the enum body
    enum_body_match = re.search(r'enum\s+\w+[^{]*\{([^}]+)', content, re.DOTALL)
    if not enum_body_match:
        return []
    
    enum_body = enum_body_match.group(1)
    
    # Extract enum constants (before any method definitions)
    # Enum constants are uppercase identifiers, possibly with parameters
    constants = re.findall(r'^\s*([A-Z][A-Z0-9_]*)\s*(?:\([^)]*\))?\s*[,;]', enum_body, re.MULTILINE)
    
    return constants


def clean_java_code(content: str) -> str:
    """
    Clean Java code for better text extraction.
    
    Args:
        content: Raw Java source code
        
    Returns:
        Cleaned text suitable for embedding
    """
    # Remove license headers (usually at the top)
    content = re.sub(r'^/\*[\s\S]*?\*/\s*', '', content)
    
    # Keep Javadoc comments as they contain valuable documentation
    # But clean up the formatting
    content = re.sub(r'/\*\*', '\n/**', content)
    
    # Remove single-line comments that are just dividers
    content = re.sub(r'//[-=]+\s*\n', '\n', content)
    
    # Normalize whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    
    return content.strip()


def create_code_summary(content: str, metadata: Dict[str, str]) -> str:
    """
    Create a summary prefix for the code to improve search relevance.
    
    Args:
        content: Java source code
        metadata: Extracted metadata
        
    Returns:
        Summary text to prepend to the code
    """
    parts = []
    
    # Add class/component description
    class_name = metadata.get("class_name", "Unknown")
    code_type = metadata.get("code_type", "class")
    component = metadata.get("connector_component", "core")
    
    parts.append(f"NetSuite Connector {code_type}: {class_name}")
    parts.append(f"Component: {component}")
    
    if metadata.get("object_type") and metadata["object_type"] != "General":
        parts.append(f"Object Type: {metadata['object_type']}")
    
    if metadata.get("enum_count"):
        parts.append(f"Defines {metadata['enum_count']} values: {metadata.get('enum_values', '')}")
    
    if metadata.get("implements"):
        parts.append(f"Implements: {metadata['implements']}")
    
    if metadata.get("extends"):
        parts.append(f"Extends: {metadata['extends']}")
    
    # Extract class-level Javadoc if present
    javadoc_match = re.search(r'/\*\*\s*([\s\S]*?)\*/\s*(?:public|abstract)', content)
    if javadoc_match:
        javadoc = javadoc_match.group(1)
        # Clean up Javadoc
        javadoc = re.sub(r'\n\s*\*\s*', ' ', javadoc)
        javadoc = re.sub(r'@\w+.*', '', javadoc)  # Remove @tags
        javadoc = javadoc.strip()
        if javadoc and len(javadoc) > 20:
            parts.append(f"Description: {javadoc[:300]}")
    
    return "\n".join(parts) + "\n\n"


def find_java_files(directory: Path, recursive: bool = True) -> List[Path]:
    """
    Find all Java files in a directory.
    
    Args:
        directory: Directory to search
        recursive: Whether to search recursively
        
    Returns:
        List of Java file paths
    """
    pattern = "**/*.java" if recursive else "*.java"
    java_files = list(directory.glob(pattern))
    java_files.sort(key=lambda p: p.name.lower())
    return java_files


def extract_java_file(filepath: Path) -> Optional[CodeDocument]:
    """
    Extract text and metadata from a single Java file.
    
    Args:
        filepath: Path to Java file
        
    Returns:
        CodeDocument or None if extraction fails
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if len(content) < 50:  # Skip nearly empty files
            return None
        
        metadata = extract_java_metadata(content, filepath.name)
        metadata["source_file"] = filepath.name
        metadata["file_path"] = str(filepath)
        
        # Create summary and clean code
        summary = create_code_summary(content, metadata)
        cleaned_code = clean_java_code(content)
        
        # Combine summary with code
        full_text = summary + cleaned_code
        
        return CodeDocument(
            filename=filepath.name,
            filepath=filepath,
            text=full_text,
            language="java",
            metadata=metadata
        )
    
    except Exception as e:
        console.print(f"[red]Error extracting {filepath.name}: {e}[/red]")
        return None


def extract_all_code(
    directory: Path,
    progress: bool = True
) -> Generator[CodeDocument, None, None]:
    """
    Extract text from all Java files in a directory.
    
    Args:
        directory: Directory containing Java files
        progress: Whether to show progress bar
        
    Yields:
        CodeDocument objects
    """
    java_files = find_java_files(directory)
    
    console.print(f"[blue]Found {len(java_files)} Java files in {directory}[/blue]")
    
    iterator = tqdm(java_files, desc="Extracting Java files") if progress else java_files
    
    for filepath in iterator:
        doc = extract_java_file(filepath)
        if doc:
            yield doc


def get_code_extraction_stats(directory: Path) -> Dict:
    """
    Get statistics about code extraction without full extraction.
    
    Args:
        directory: Directory to analyze
        
    Returns:
        Dictionary with statistics
    """
    java_files = find_java_files(directory)
    
    stats = {
        "total_files": len(java_files),
        "total_size_kb": sum(f.stat().st_size for f in java_files) / 1024,
        "components": {},
        "sample_files": [f.name for f in java_files[:10]]
    }
    
    # Categorize files by component type
    for filepath in java_files:
        filename_lower = filepath.name.lower()
        
        if 'search' in filename_lower:
            component = "search"
        elif 'record' in filename_lower or 'type' in filename_lower:
            component = "record_type"
        elif 'objecttype' in filename_lower:
            component = "object_definition"
        else:
            component = "other"
        
        stats["components"][component] = stats["components"].get(component, 0) + 1
    
    return stats


if __name__ == "__main__":
    # Test extraction
    import sys
    
    if len(sys.argv) > 1:
        test_dir = Path(sys.argv[1])
    else:
        test_dir = Path(__file__).parent.parent.parent / "Connector_Code"
    
    if test_dir.exists():
        stats = get_code_extraction_stats(test_dir)
        console.print(f"\n[bold]Code Extraction Stats for {test_dir}[/bold]")
        console.print(f"Total Java files: {stats['total_files']}")
        console.print(f"Total size: {stats['total_size_kb']:.2f} KB")
        console.print(f"Components: {stats['components']}")
        console.print(f"Sample files: {stats['sample_files'][:5]}")
    else:
        console.print(f"[red]Directory not found: {test_dir}[/red]")
