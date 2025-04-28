"""
Unit tests for the file manager module.
"""
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from deepcoder.core.file_manager import FileManager, FileError


class TestFileManager:
    """Tests for the FileManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path("/tmp/test_project")
        
        # Mock _parse_gitignore
        with patch.object(FileManager, '_parse_gitignore', return_value=[]):
            self.file_manager = FileManager(self.project_root)
    
    def test_initialization(self):
        """Test file manager initialization."""
        assert self.file_manager.project_root == self.project_root
    
    def test_parse_gitignore(self):
        """Test parsing .gitignore file."""
        # Mock open to return a sample .gitignore file
        mock_gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class

# Node.js
node_modules/
"""
        with patch('builtins.open', mock_open(read_data=mock_gitignore_content)), \
             patch('pathlib.Path.exists', return_value=True):
            patterns = self.file_manager._parse_gitignore()
            
            # Check default patterns
            assert '**/node_modules/**' in patterns
            assert '**/.git/**' in patterns
            
            # Check patterns from .gitignore
            assert '__pycache__/' in patterns
            assert '*.py[cod]' in patterns
            assert 'node_modules/' in patterns
    
    def test_is_ignored(self):
        """Test checking if a path should be ignored."""
        # Set up test patterns
        self.file_manager.gitignore_patterns = [
            '**/node_modules/**',
            '**/__pycache__/**',
            '*.pyc'
        ]
        
        # Mock relative_to to return the path unchanged
        with patch.object(Path, 'relative_to', return_value=Path('node_modules/package.json')):
            assert self.file_manager._is_ignored(Path('/tmp/test_project/node_modules/package.json'))
        
        with patch.object(Path, 'relative_to', return_value=Path('src/main.py')):
            assert not self.file_manager._is_ignored(Path('/tmp/test_project/src/main.py'))
        
        with patch.object(Path, 'relative_to', return_value=Path('src/module.pyc')):
            assert self.file_manager._is_ignored(Path('/tmp/test_project/src/module.pyc'))
    
    @pytest.mark.asyncio
    async def test_read_file_success(self):
        """Test reading a file successfully."""
        file_content = "def test(): pass"
        
        with patch('builtins.open', mock_open(read_data=file_content)), \
             patch('pathlib.Path.exists', return_value=True):
            content = await self.file_manager.read_file("src/test.py")
            assert content == file_content
    
    @pytest.mark.asyncio
    async def test_read_file_not_found(self):
        """Test reading a file that doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileError, match="File not found"):
                await self.file_manager.read_file("src/nonexistent.py")
    
    @pytest.mark.asyncio
    async def test_read_file_error(self):
        """Test handling errors when reading a file."""
        with patch('builtins.open', side_effect=IOError("Permission denied")), \
             patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(FileError, match="Failed to read file"):
                await self.file_manager.read_file("src/test.py")
    
    @pytest.mark.asyncio
    async def test_write_file_success(self):
        """Test writing a file successfully."""
        mock_file = mock_open()
        
        with patch('builtins.open', mock_file), \
             patch('pathlib.Path.parent.mkdir') as mock_mkdir:
            await self.file_manager.write_file("src/test.py", "def test(): pass")
            
            # Check that directories were created
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Check that file was written
            mock_file.assert_called_once_with(self.project_root / "src/test.py", 'w', encoding='utf-8')
            mock_file().write.assert_called_once_with("def test(): pass")
    
    @pytest.mark.asyncio
    async def test_write_file_error(self):
        """Test handling errors when writing a file."""
        with patch('builtins.open', side_effect=IOError("Permission denied")), \
             patch('pathlib.Path.parent.mkdir'):
            with pytest.raises(FileError, match="Failed to write file"):
                await self.file_manager.write_file("src/test.py", "def test(): pass")
    
    @pytest.mark.asyncio
    async def test_search_files_by_name(self):
        """Test searching files by name."""
        entities = {
            "files": ["src/auth.py", "src/nonexistent.py"]
        }
        
        with patch('pathlib.Path.exists', side_effect=lambda p: "nonexistent" not in str(p)):
            files = await self.file_manager.search_files({"entities": entities})
            
            assert len(files) == 1
            assert files[0] == "src/auth.py"
    
    @pytest.mark.asyncio
    async def test_search_files_by_function(self):
        """Test searching files by function name."""
        entities = {
            "functions": ["login"]
        }
        
        # Mock _list_code_files to return some test files
        test_files = [
            self.project_root / "src/auth.py",
            self.project_root / "src/user.py"
        ]
        self.file_manager._list_code_files = MagicMock(return_value=test_files)
        
        # Mock read_file to return content with the function in one file
        async def mock_read_file(path):
            if "auth.py" in path:
                return "def login(): pass"
            else:
                return "def logout(): pass"
        
        self.file_manager.read_file = mock_read_file
        
        files = await self.file_manager.search_files({
            "task_type": "refactor",
            "entities": entities
        })
        
        assert len(files) == 1
        assert "auth.py" in files[0]
    
    @pytest.mark.asyncio
    async def test_search_files_fallback(self):
        """Test fallback when no specific files or functions are found."""
        # Mock _list_code_files to return some test files
        test_files = [
            self.project_root / "src/auth.py",
            self.project_root / "src/user.py",
            self.project_root / "src/database.js",
            self.project_root / "docs/readme.md"
        ]
        
        # Add stat attribute to each Path object
        for file_path in test_files:
            file_path.stat = MagicMock(return_value=MagicMock(st_mtime=1234567890))
        
        self.file_manager._list_code_files = MagicMock(return_value=test_files)
        
        # For refactor task, should prefer Python, JavaScript, and TypeScript files
        files = await self.file_manager.search_files({
            "task_type": "refactor",
            "entities": {}
        })
        
        assert len(files) <= 5  # Limited to 5 files
        
        # For document task, should prefer Python, Markdown, and markup files
        files = await self.file_manager.search_files({
            "task_type": "document",
            "entities": {}
        })
        
        assert len(files) <= 5  # Limited to 5 files
    
    def test_list_code_files(self):
        """Test listing code files in the project."""
        # Mock os.walk to return some test files
        test_dirs = [
            ("/tmp/test_project/src", ["utils"], ["auth.py", "user.py"]),
            ("/tmp/test_project/src/utils", [], ["helpers.py", "config.js", "README.md"]),
            ("/tmp/test_project/node_modules", ["package"], ["index.js"]),  # Should be ignored
        ]
        
        with patch('os.walk', return_value=test_dirs), \
             patch.object(FileManager, '_is_ignored', side_effect=lambda p: "node_modules" in str(p)), \
             patch('pathlib.Path.stat', return_value=MagicMock(st_mtime=1234567890)):
            files = self.file_manager._list_code_files()
            
            # Check that node_modules is ignored
            assert not any("node_modules" in str(f) for f in files)
            
            # Check that code files are included
            file_names = [f.name for f in files]
            assert "auth.py" in file_names
            assert "user.py" in file_names
            assert "helpers.py" in file_names
            assert "config.js" in file_names
            assert "README.md" in file_names