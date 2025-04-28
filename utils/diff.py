"""
Diffing utilities for DeepCoder CLI.
"""
import difflib
from typing import List, Tuple


def create_diff(old_content: str, new_content: str, file_path: str) -> str:
    """
    Create a unified diff between old and new content.
    
    Args:
        old_content: The original content
        new_content: The new content
        file_path: The path of the file
        
    Returns:
        str: The unified diff
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=3
    )
    
    return "".join(diff)


def colorize_diff(diff: str) -> str:
    """
    Colorize a diff with ANSI color codes.
    
    Args:
        diff: The diff to colorize
        
    Returns:
        str: The colorized diff
    """
    colorized = []
    
    for line in diff.splitlines(True):
        if line.startswith("+"):
            colorized.append(f"\033[32m{line}\033[0m")  # Green for additions
        elif line.startswith("-"):
            colorized.append(f"\033[31m{line}\033[0m")  # Red for deletions
        elif line.startswith("@"):
            colorized.append(f"\033[36m{line}\033[0m")  # Cyan for chunk headers
        else:
            colorized.append(line)
    
    return "".join(colorized)


def parse_diff(diff: str) -> List[Tuple[str, str, int, int, str]]:
    """
    Parse a unified diff into a list of changes.
    
    Args:
        diff: The unified diff to parse
        
    Returns:
        List[Tuple]: List of (action, file, start_line, line_count, content)
    """
    changes = []
    current_file = None
    current_chunk = None
    
    for line in diff.splitlines(True):
        if line.startswith("--- "):
            # Old file
            pass
        elif line.startswith("+++ "):
            # New file
            current_file = line[6:].strip()
        elif line.startswith("@@ "):
            # Chunk header
            # Format: @@ -start,count +start,count @@
            parts = line.split()
            old_range = parts[1]
            new_range = parts[2]
            
            # Extract start line and count for the new file
            if "," in new_range:
                start, count = new_range[1:].split(",")
            else:
                start = new_range[1:]
                count = 1
            
            current_chunk = (int(start), int(count))
        elif current_file and current_chunk:
            # Content line
            if line.startswith("+"):
                # Addition
                changes.append(("add", current_file, current_chunk[0], 1, line[1:]))
            elif line.startswith("-"):
                # Deletion
                changes.append(("delete", current_file, current_chunk[0], 1, line[1:]))
    
    return changes