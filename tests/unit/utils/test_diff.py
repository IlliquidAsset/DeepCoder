"""
Unit tests for the diff utilities module.
"""
import pytest
from deepcoder.utils.diff import create_diff, colorize_diff, parse_diff


class TestDiffUtils:
    """Tests for the diff utilities."""
    
    def test_create_diff(self):
        """Test creating a unified diff."""
        old_content = "def login():\n    pass"
        new_content = "def login():\n    # Authenticate user\n    pass"
        file_path = "auth.py"
        
        diff = create_diff(old_content, new_content, file_path)
        
        # Check that diff contains expected elements
        assert "--- a/auth.py" in diff
        assert "+++ b/auth.py" in diff
        assert "+    # Authenticate user" in diff
    
    def test_create_diff_no_changes(self):
        """Test creating a diff with no changes."""
        content = "def login():\n    pass"
        file_path = "auth.py"
        
        diff = create_diff(content, content, file_path)
        
        # Diff should be empty for identical content
        assert diff == ""
    
    def test_colorize_diff(self):
        """Test colorizing a diff."""
        diff = """--- a/auth.py
+++ b/auth.py
@@ -1,2 +1,3 @@
 def login():
+    # Authenticate user
     pass"""
        
        colorized = colorize_diff(diff)
        
        # Check that ANSI color codes were added
        assert "\033[31m" in colorized  # Red for deletions
        assert "\033[32m" in colorized  # Green for additions
        assert "\033[36m" in colorized  # Cyan for chunk headers
    
    def test_parse_diff(self):
        """Test parsing a diff."""
        diff = """--- a/auth.py
+++ b/auth.py
@@ -1,2 +1,3 @@
 def login():
+    # Authenticate user
     pass"""
        
        changes = parse_diff(diff)
        
        # Check that changes were parsed correctly
        assert len(changes) == 1
        assert changes[0][0] == "add"  # Action
        assert changes[0][1] == "auth.py"  # File
        assert changes[0][2] == 1  # Start line
        assert changes[0][3] == 1  # Line count
        assert "# Authenticate user" in changes[0][4]  # Content
    
    def test_parse_diff_multiple_changes(self):
        """Test parsing a diff with multiple changes."""
        diff = """--- a/auth.py
+++ b/auth.py
@@ -1,3 +1,4 @@
 def login():
+    # Authenticate user
     pass
-# End of file
+# End of auth.py"""
        
        changes = parse_diff(diff)
        
        # Check that all changes were parsed
        assert len(changes) == 2
        
        # Check first change (addition)
        assert changes[0][0] == "add"
        assert "# Authenticate user" in changes[0][4]
        
        # Check second change (deletion)
        assert changes[1][0] == "delete"
        assert "# End of file" in changes[1][4]