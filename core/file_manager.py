"""
File management utilities for DeepCoder CLI.
"""
import os
import fnmatch
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("deepcoder.file_manager")


class FileError(Exception):
    """Exception raised for file-related errors."""
    pass


class FileManager:
    """Manages file operations for the DeepCoder agent."""
    
    # File types to consider when searching
    CODE_FILE_EXTENSIONS = {
        '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', 
        '.html', '.css', '.md', '.json', '.yml', '.yaml'
    }
    
    # Default patterns to ignore (similar to common .gitignore entries)
    DEFAULT_IGNORE_PATTERNS = [
        '**/node_modules/**',
        '**/.git/**',
        '**/venv/**',
        '**/.env',
        '**/__pycache__/**',
        '**/*.pyc',
        '**/dist/**',
        '**/build/**',
        '**/.DS_Store'
    ]
    
    def __init__(self, project_root: Path):
        """
        Initialize the file manager.
        
        Args:
            project_root: The root directory of the project
        """
        self.project_root = project_root
        self.gitignore_patterns = self._parse_gitignore()
    
    def _parse_gitignore(self) -> List[str]:
        """
        Parse .gitignore file in the project root.
        
        Returns:
            List[str]: Patterns from .gitignore
        """
        patterns = list(self.DEFAULT_IGNORE_PATTERNS)
        gitignore_path = self.project_root / '.gitignore'
        
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                logger.warning(f"Error parsing .gitignore: {str(e)}")
        
        return patterns
    
    def _is_ignored(self, path: Path) -> bool:
        """
        Check if a path should be ignored.
        
        Args:
            path: The path to check
            
        Returns:
            bool: True if the path should be ignored
        """
        rel_path = path.relative_to(self.project_root)
        path_str = str(rel_path)
        
        for pattern in self.gitignore_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
        
        return False
    
    async def read_file(self, file_path: str) -> str:
        """
        Read a file's content.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            str: The file content
            
        Raises:
            FileError: If the file cannot be read
        """
        # Convert to absolute path if not already
        if not os.path.isabs(file_path):
            path = self.project_root / file_path
        else:
            path = Path(file_path)
        
        try:
            if not path.exists():
                raise FileError(f"File not found: {path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {path}: {str(e)}")
            raise FileError(f"Failed to read file {path}: {str(e)}")
    
    async def write_file(self, file_path: str, content: str) -> None:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Raises:
            FileError: If the file cannot be written
        """
        # Convert to absolute path if not already
        if not os.path.isabs(file_path):
            path = self.project_root / file_path
        else:
            path = Path(file_path)
        
        try:
            # Create directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error writing file {path}: {str(e)}")
            raise FileError(f"Failed to write file {path}: {str(e)}")
    
    async def search_files(self, criteria: Dict[str, Any]) -> List[str]:
        """
        Search for files based on criteria.
        
        Args:
            criteria: Search criteria (task type, entities, etc.)
            
        Returns:
            List[str]: Paths to relevant files
        """
        task_type = criteria.get("task_type", "unknown")
        entities = criteria.get("entities", {})
        
        # If specific files are mentioned, look for them
        if "files" in entities:
            return [
                path for path in entities["files"] 
                if Path(self.project_root / path).exists()
            ]
        
        # Otherwise, search based on other criteria
        found_files = []
        
        # If functions are mentioned, search for files containing them
        if "functions" in entities:
            function_names = entities.get("functions", [])
            
            # TODO: Implement more sophisticated search
            # For now, we'll just return all code files in the project
            
            for path in self._list_code_files():
                for function_name in function_names:
                    try:
                        content = await self.read_file(str(path))
                        if function_name in content:
                            found_files.append(str(path.relative_to(self.project_root)))
                            break
                    except Exception:
                        pass
        
        # If no specific files or functions found, return a limited set of code files
        if not found_files:
            # Just return the first few code files as a fallback
            all_code_files = self._list_code_files()
            
            # Filter to the most relevant ones based on task type
            if task_type == "refactor" or task_type == "fix_bug":
                # For refactoring or bug fixes, prefer Python, JavaScript, and TypeScript files
                filtered_files = [p for p in all_code_files if p.suffix in ['.py', '.js', '.ts']]
            elif task_type == "document":
                # For documentation, prefer Python, Markdown, and markup files
                filtered_files = [p for p in all_code_files if p.suffix in ['.py', '.md', '.html']]
            else:
                filtered_files = all_code_files
            
            # Limit the number of files to avoid overwhelming the model
            found_files = [
                str(path.relative_to(self.project_root)) 
                for path in filtered_files[:5]
            ]
        
        return found_files
    
    def _list_code_files(self) -> List[Path]:
        """
        List all code files in the project.
        
        Returns:
            List[Path]: Paths to code files
        """
        code_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip directories that should be ignored
            dirs[:] = [d for d in dirs if not self._is_ignored(Path(root) / d)]
            
            for file in files:
                path = Path(root) / file
                
                if path.suffix in self.CODE_FILE_EXTENSIONS and not self._is_ignored(path):
                    code_files.append(path)
        
        # Sort by modification time (newest first)
        code_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        return code_files