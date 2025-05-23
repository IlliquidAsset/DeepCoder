"""
Unit tests for the git utilities module.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from deepcoder.core.git_utils import GitManager, GitError


class TestGitManager:
    """Tests for the GitManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path("/tmp/test_project")
        
        # Mock git.Repo for testing
        self.mock_repo = MagicMock()
        
        with patch('git.Repo', return_value=self.mock_repo):
            self.git_manager = GitManager(self.project_root)
    
    def test_initialization_success(self):
        """Test successful initialization."""
        with patch('git.Repo', return_value=self.mock_repo):
            git_manager = GitManager(self.project_root)
            
            assert git_manager._repo == self.mock_repo
            assert git_manager.is_git_repo()
    
    def test_initialization_not_git_repo(self):
        """Test initialization when not a Git repository."""
        with patch('git.Repo', side_effect=Exception("Not a git repository")):
            git_manager = GitManager(self.project_root)
            
            assert git_manager._repo is None
            assert not git_manager.is_git_repo()
    
    def test_get_status_with_repo(self):
        """Test getting Git status with a repository."""
        # Mock the index.diff methods
        self.mock_repo.index.diff.side_effect = lambda x: [
            MagicMock(a_path="modified.py") if x is None else MagicMock(a_path="staged.py")
        ]
        self.mock_repo.untracked_files = ["untracked.py"]
        
        status = self.git_manager.get_status()
        
        assert "untracked.py" in status["untracked"]
        assert "modified.py" in status["modified"]
        assert "staged.py" in status["staged"]
    
    def test_get_status_without_repo(self):
        """Test getting Git status without a repository."""
        self.git_manager._repo = None
        
        status = self.git_manager.get_status()
        
        assert status["untracked"] == []
        assert status["modified"] == []
        assert status["staged"] == []
    
    def test_get_status_error(self):
        """Test handling errors when getting Git status."""
        self.mock_repo.index.diff.side_effect = Exception("Git error")
        
        with pytest.raises(GitError, match="Failed to get Git status"):
            self.git_manager.get_status()
    
    def test_stage_file_success(self):
        """Test staging a file successfully."""
        # Mock the git.add method
        self.mock_repo.git.add = MagicMock()
        
        # Test with relative path
        self.git_manager.stage_file("src/test.py")
        self.mock_repo.git.add.assert_called_with("src/test.py")
        
        # Test with absolute path
        with patch('os.path.relpath', return_value="src/test.py"):
            self.git_manager.stage_file("/tmp/test_project/src/test.py")
            self.mock_repo.git.add.assert_called_with("src/test.py")
    
    def test_stage_file_without_repo(self):
        """Test staging a file without a repository."""
        self.git_manager._repo = None
        
        with pytest.raises(GitError, match="Not a Git repository"):
            self.git_manager.stage_file("src/test.py")
    
    def test_stage_file_error(self):
        """Test handling errors when staging a file."""
        self.mock_repo.git.add = MagicMock(side_effect=Exception("Git error"))
        
        with pytest.raises(GitError, match="Failed to stage file"):
            self.git_manager.stage_file("src/test.py")
    
    def test_commit_changes_success(self):
        """Test committing changes successfully."""
        # Mock the index.commit method
        commit_mock = MagicMock(hexsha="abcdef123456")
        self.mock_repo.index.commit = MagicMock(return_value=commit_mock)
        
        commit_hash = self.git_manager.commit_changes("Test commit")
        
        # Check that commit was called with the correct message
        self.mock_repo.index.commit.assert_called_once()
        assert "Test commit" in self.mock_repo.index.commit.call_args[0][0]
        assert "Generated by DeepCoder CLI" in self.mock_repo.index.commit.call_args[0][0]
        
        # Check the returned commit hash
        assert commit_hash == "abcdef123456"
    
    def test_commit_changes_without_repo(self):
        """Test committing changes without a repository."""
        self.git_manager._repo = None
        
        with pytest.raises(GitError, match="Not a Git repository"):
            self.git_manager.commit_changes("Test commit")
    
    def test_commit_changes_error(self):
        """Test handling errors when committing changes."""
        self.mock_repo.index.commit = MagicMock(side_effect=Exception("Git error"))
        
        with pytest.raises(GitError, match="Failed to commit changes"):
            self.git_manager.commit_changes("Test commit")
    
    def test_is_file_ignored_success(self):
        """Test checking if a file is ignored successfully."""
        # Mock the ignored method
        self.mock_repo.ignored = MagicMock(return_value=True)
        
        # Test with relative path
        assert self.git_manager.is_file_ignored("node_modules/package.json")
        
        # Test with absolute path
        with patch('os.path.relpath', return_value="node_modules/package.json"):
            assert self.git_manager.is_file_ignored("/tmp/test_project/node_modules/package.json")
    
    def test_is_file_ignored_without_repo(self):
        """Test checking if a file is ignored without a repository."""
        self.git_manager._repo = None
        
        assert not self.git_manager.is_file_ignored("node_modules/package.json")
    
    def test_is_file_ignored_error(self):
        """Test handling errors when checking if a file is ignored."""
        self.mock_repo.ignored = MagicMock(side_effect=Exception("Git error"))
        
        # Should return False on error
        assert not self.git_manager.is_file_ignored("src/test.py")