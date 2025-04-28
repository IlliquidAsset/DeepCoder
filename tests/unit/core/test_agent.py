"""
Unit tests for the agent module.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from deepcoder.core.agent import Agent, TaskType
from deepcoder.models.base import ModelResponse


class TestAgent:
    """Tests for the Agent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.model = MagicMock()
        self.config = {
            "model": {
                "platform": "togetherai",
                "parameters": {
                    "temperature": 0.5
                }
            },
            "git": {
                "auto_stage": False,
                "auto_commit": False
            }
        }
        self.project_root = "/tmp/test_project"
        
        # Mock the file manager and git manager
        with patch('deepcoder.core.agent.FileManager'), \
             patch('deepcoder.core.agent.GitManager'):
            self.agent = Agent(self.model, self.config, self.project_root)
    
    def test_initialization(self):
        """Test agent initialization."""
        assert self.agent.model == self.model
        assert self.agent.config == self.config
        assert self.agent.project_root == Path(self.project_root)
    
    def test_parse_instruction_refactor(self):
        """Test parsing refactor instruction."""
        instruction = "Refactor the login function in auth.py"
        task_type, entities = self.agent._parse_instruction(instruction)
        
        assert task_type == TaskType.REFACTOR
        assert "auth.py" in entities.get("files", [])
        assert "login" in entities.get("functions", [])
    
    def test_parse_instruction_add_feature(self):
        """Test parsing add feature instruction."""
        instruction = "Add a new validation method to user.py"
        task_type, entities = self.agent._parse_instruction(instruction)
        
        assert task_type == TaskType.ADD_FEATURE
        assert "user.py" in entities.get("files", [])
        assert "validation" in entities.get("functions", [])
    
    def test_parse_instruction_fix_bug(self):
        """Test parsing fix bug instruction."""
        instruction = "Fix the bug in the authentication.py file"
        task_type, entities = self.agent._parse_instruction(instruction)
        
        assert task_type == TaskType.FIX_BUG
        assert "authentication.py" in entities.get("files", [])
    
    def test_parse_instruction_explain(self):
        """Test parsing explain instruction."""
        instruction = "Explain how the login system works in auth.py"
        task_type, entities = self.agent._parse_instruction(instruction)
        
        assert task_type == TaskType.EXPLAIN
        assert "auth.py" in entities.get("files", [])
    
    def test_parse_instruction_document(self):
        """Test parsing document instruction."""
        instruction = "Add documentation to the database.py module"
        task_type, entities = self.agent._parse_instruction(instruction)
        
        assert task_type == TaskType.DOCUMENT
        assert "database.py" in entities.get("files", [])
    
    def test_parse_instruction_unknown(self):
        """Test parsing unknown instruction."""
        instruction = "What is the meaning of life?"
        task_type, entities = self.agent._parse_instruction(instruction)
        
        assert task_type == TaskType.UNKNOWN
    
    def test_create_plan_with_files(self):
        """Test creating a plan with specified files."""
        task_type = TaskType.REFACTOR
        entities = {"files": ["auth.py"]}
        instruction = "Refactor auth.py"
        
        plan = self.agent._create_plan(task_type, entities, instruction)
        
        # Check that the plan includes reading the file
        assert any(step["action"] == "read_file" and step["file_path"] == "auth.py" for step in plan)
        
        # Check that it includes generating changes
        assert any(step["action"] == "generate_changes" for step in plan)
    
    def test_create_plan_without_files(self):
        """Test creating a plan without specified files."""
        task_type = TaskType.REFACTOR
        entities = {"functions": ["login"]}
        instruction = "Refactor the login function"
        
        plan = self.agent._create_plan(task_type, entities, instruction)
        
        # Check that the plan includes searching for files
        assert any(step["action"] == "search_files" for step in plan)
    
    def test_create_plan_explain(self):
        """Test creating a plan for explanation task."""
        task_type = TaskType.EXPLAIN
        entities = {"files": ["auth.py"]}
        instruction = "Explain auth.py"
        
        plan = self.agent._create_plan(task_type, entities, instruction)
        
        # Check that the plan includes explanation actions
        assert any(step["action"] == "generate_explanation" for step in plan)
        assert any(step["action"] == "present_explanation" for step in plan)
        
        # Check that it doesn't include code change actions
        assert not any(step["action"] == "generate_changes" for step in plan)
    
    def test_create_plan_with_git_options(self):
        """Test creating a plan with Git options enabled."""
        # Enable Git options
        self.agent.config["git"]["auto_stage"] = True
        self.agent.config["git"]["auto_commit"] = True
        
        task_type = TaskType.REFACTOR
        entities = {"files": ["auth.py"]}
        instruction = "Refactor auth.py"
        
        plan = self.agent._create_plan(task_type, entities, instruction)
        
        # Check that the plan includes Git actions
        assert any(step["action"] == "git_stage_changes" for step in plan)
        assert any(step["action"] == "git_commit_changes" for step in plan)
    
    @pytest.mark.asyncio
    async def test_execute_plan_read_file(self):
        """Test executing a plan with read_file action."""
        plan = [
            {
                "action": "read_file",
                "file_path": "auth.py"
            }
        ]
        
        # Mock file_manager.read_file
        self.agent.file_manager.read_file = AsyncMock(return_value="def login(): pass")
        
        result = await self.agent._execute_plan(plan, "Read auth.py")
        
        # Check that the file was read
        self.agent.file_manager.read_file.assert_called_once_with("auth.py")
        assert result["files"]["auth.py"] == "def login(): pass"
    
    @pytest.mark.asyncio
    async def test_execute_plan_search_files(self):
        """Test executing a plan with search_files action."""
        plan = [
            {
                "action": "search_files",
                "criteria": {
                    "task_type": "refactor",
                    "entities": {"functions": ["login"]}
                }
            }
        ]
        
        # Mock file_manager methods
        self.agent.file_manager.search_files = AsyncMock(return_value=["auth.py"])
        self.agent.file_manager.read_file = AsyncMock(return_value="def login(): pass")
        
        result = await self.agent._execute_plan(plan, "Refactor login")
        
        # Check that files were searched and read
        self.agent.file_manager.search_files.assert_called_once()
        self.agent.file_manager.read_file.assert_called_once_with("auth.py")
        assert result["files"]["auth.py"] == "def login(): pass"
    
    @pytest.mark.asyncio
    async def test_execute_plan_generate_changes(self):
        """Test executing a plan with generate_changes action."""
        plan = [
            {
                "action": "generate_changes",
                "task_type": "refactor",
                "instruction": "Refactor login"
            }
        ]
        
        # Set up context with files
        context = {
            "instruction": "Refactor login",
            "files": {"auth.py": "def login(): pass"},
            "changes": [],
            "explanation": None,
            "error": None
        }
        
        # Mock _generate_code_changes
        self.agent._generate_code_changes = AsyncMock(return_value=[
            {
                "file_path": "auth.py",
                "original_content": "def login(): pass",
                "new_content": "def login():\n    # Refactored\n    pass",
                "diff": "@@ -1 +1,3 @@\n-def login(): pass\n+def login():\n+    # Refactored\n+    pass"
            }
        ])
        
        result = await self.agent._execute_plan(plan, "Refactor login", context=context)
        
        # Check that changes were generated
        self.agent._generate_code_changes.assert_called_once_with("refactor", context)
        assert len(result["changes"]) == 1
        assert result["changes"][0]["file_path"] == "auth.py"
    
    @pytest.mark.asyncio
    async def test_execute_plan_generate_explanation(self):
        """Test executing a plan with generate_explanation action."""
        plan = [
            {
                "action": "generate_explanation",
                "instruction": "Explain login"
            }
        ]
        
        # Set up context with files
        context = {
            "instruction": "Explain login",
            "files": {"auth.py": "def login(): pass"},
            "changes": [],
            "explanation": None,
            "error": None
        }
        
        # Mock _generate_explanation
        self.agent._generate_explanation = AsyncMock(return_value="This is a simple login function.")
        
        result = await self.agent._execute_plan(plan, "Explain login", context=context)
        
        # Check that explanation was generated
        self.agent._generate_explanation.assert_called_once_with(context)
        assert result["explanation"] == "This is a simple login function."
    
    @pytest.mark.asyncio
    async def test_generate_code_changes(self):
        """Test generating code changes."""
        # Mock model response
        model_response = ModelResponse(content="""
FILE: auth.py
```
def login():
    # Refactored
    pass
```

I've added a comment to show the function has been refactored.
""")
        self.model.generate = AsyncMock(return_value=model_response)
        
        # Set up context
        context = {
            "instruction": "Refactor login",
            "files": {"auth.py": "def login(): pass"}
        }
        
        changes = await self.agent._generate_code_changes("refactor", context)
        
        # Check that the model was called
        self.model.generate.assert_called_once()
        
        # Check the changes
        assert len(changes) == 1
        assert changes[0]["file_path"] == "auth.py"
        assert changes[0]["original_content"] == "def login(): pass"
        assert "# Refactored" in changes[0]["new_content"]
    
    @pytest.mark.asyncio
    async def test_generate_explanation(self):
        """Test generating explanation."""
        # Mock model response
        model_response = ModelResponse(content="This is a simple login function.")
        self.model.generate = AsyncMock(return_value=model_response)
        
        # Set up context
        context = {
            "instruction": "Explain login",
            "files": {"auth.py": "def login(): pass"}
        }
        
        explanation = await self.agent._generate_explanation(context)
        
        # Check that the model was called
        self.model.generate.assert_called_once()
        
        # Check the explanation
        assert explanation == "This is a simple login function."
    
    def test_parse_code_changes(self):
        """Test parsing code changes from model response."""
        model_response = """
FILE: auth.py
```
def login():
    # Refactored
    pass
```

I've added a comment to show the function has been refactored.

FILE: new_file.py
```
def new_function():
    return True
```

This is a new file with a new function.
"""
        original_files = {"auth.py": "def login(): pass"}
        
        changes = self.agent._parse_code_changes(model_response, original_files)
        
        # Check the changes
        assert len(changes) == 2
        
        # Check the modified file
        assert changes[0]["file_path"] == "auth.py"
        assert changes[0]["original_content"] == "def login(): pass"
        assert "# Refactored" in changes[0]["new_content"]
        assert "diff" in changes[0]
        
        # Check the new file
        assert changes[1]["file_path"] == "new_file.py"
        assert changes[1]["original_content"] == ""
        assert "new_function" in changes[1]["new_content"]
        assert changes[1]["is_new_file"] is True