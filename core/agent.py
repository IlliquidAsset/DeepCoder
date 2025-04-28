"""
Core agent functionality for DeepCoder CLI.
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from deepcoder.models.base import BaseModel, ModelResponse
from deepcoder.core.file_manager import FileManager
from deepcoder.core.git_utils import GitManager
from deepcoder.utils.diff import create_diff

logger = logging.getLogger("deepcoder.agent")


class TaskType(Enum):
    """Types of coding tasks."""
    REFACTOR = "refactor"
    ADD_FEATURE = "add_feature"
    FIX_BUG = "fix_bug"
    EXPLAIN = "explain"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class Agent:
    """Core agent that orchestrates the DeepCoder workflow."""
    
    def __init__(
        self, 
        model: BaseModel,
        config: Dict[str, Any],
        project_root: Optional[str] = None
    ):
        """
        Initialize the agent.
        
        Args:
            model: The model to use for generating code
            config: Configuration dictionary
            project_root: The root directory of the project (defaults to current directory)
        """
        self.model = model
        self.config = config
        self.project_root = Path(project_root or os.getcwd())
        self.file_manager = FileManager(self.project_root)
        self.git_manager = GitManager(self.project_root)
    
    async def process_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Process a natural language instruction.
        
        Args:
            instruction: The instruction to process
            
        Returns:
            Dict: Result of processing the instruction
        """
        logger.info(f"Processing instruction: {instruction}")
        
        # 1. Parse instruction
        task_type, entities = self._parse_instruction(instruction)
        logger.debug(f"Parsed instruction - Task: {task_type}, Entities: {entities}")
        
        # 2. Plan steps based on task type
        plan = self._create_plan(task_type, entities, instruction)
        logger.debug(f"Created plan: {plan}")
        
        # 3. Execute plan
        return await self._execute_plan(plan, instruction)
    
    def _parse_instruction(self, instruction: str) -> Tuple[TaskType, Dict[str, Any]]:
        """
        Parse the instruction to identify task type and entities.
        
        Args:
            instruction: The instruction to parse
            
        Returns:
            Tuple[TaskType, Dict]: The identified task type and relevant entities
        """
        instruction_lower = instruction.lower()
        entities = {}
        
        # Extract file names from the instruction (simple heuristic)
        file_candidates = [
            word for word in instruction.split() 
            if (word.endswith(".py") or word.endswith(".js") or word.endswith(".ts") or
                word.endswith(".java") or word.endswith(".c") or word.endswith(".cpp") or
                word.endswith(".h") or word.endswith(".html") or word.endswith(".css") or
                word.endswith(".md") or word.endswith(".json") or word.endswith(".yml") or
                word.endswith(".yaml"))
        ]
        
        if file_candidates:
            entities["files"] = file_candidates
        
        # Extract function names (simple heuristic)
        # Look for words followed by "function" or "method"
        words = instruction.split()
        for i, word in enumerate(words):
            if i > 0 and word.lower() in ["function", "method"]:
                entities.setdefault("functions", []).append(words[i-1])
        
        # Determine task type based on keywords
        if any(kw in instruction_lower for kw in ["refactor", "restructure", "rewrite", "improve"]):
            return TaskType.REFACTOR, entities
        elif any(kw in instruction_lower for kw in ["add", "create", "implement", "new"]):
            return TaskType.ADD_FEATURE, entities
        elif any(kw in instruction_lower for kw in ["fix", "resolve", "debug", "issue", "bug"]):
            return TaskType.FIX_BUG, entities
        elif any(kw in instruction_lower for kw in ["explain", "understand", "interpret"]):
            return TaskType.EXPLAIN, entities
        elif any(kw in instruction_lower for kw in ["document", "documentation", "comment"]):
            return TaskType.DOCUMENT, entities
        else:
            return TaskType.UNKNOWN, entities
    
    def _create_plan(
        self, 
        task_type: TaskType, 
        entities: Dict[str, Any],
        instruction: str
    ) -> List[Dict[str, Any]]:
        """
        Create a plan for executing the instruction.
        
        Args:
            task_type: The type of task to execute
            entities: The entities identified in the instruction
            instruction: The original instruction
            
        Returns:
            List[Dict]: A plan of steps to execute
        """
        plan = []
        
        # Common initial steps
        if "files" in entities:
            for file_name in entities["files"]:
                plan.append({
                    "action": "read_file",
                    "file_path": file_name
                })
        else:
            # If no files explicitly mentioned, we'll need to search for relevant files
            plan.append({
                "action": "search_files",
                "criteria": {
                    "task_type": task_type.value,
                    "entities": entities
                }
            })
        
        # Task-specific steps
        if task_type in [TaskType.REFACTOR, TaskType.ADD_FEATURE, TaskType.FIX_BUG, TaskType.DOCUMENT]:
            plan.append({
                "action": "generate_changes",
                "task_type": task_type.value,
                "instruction": instruction
            })
            plan.append({
                "action": "present_changes"
            })
            plan.append({
                "action": "confirm_changes"
            })
            plan.append({
                "action": "apply_changes"
            })
            
            # Optional git steps based on config
            if self.config.get("git", {}).get("auto_stage", False):
                plan.append({
                    "action": "git_stage_changes"
                })
                
            if self.config.get("git", {}).get("auto_commit", False):
                plan.append({
                    "action": "git_commit_changes",
                    "message": f"{task_type.value.replace('_', ' ')}: {instruction}"
                })
        
        elif task_type == TaskType.EXPLAIN:
            plan.append({
                "action": "generate_explanation",
                "instruction": instruction
            })
            plan.append({
                "action": "present_explanation"
            })
        
        return plan
    
    async def _execute_plan(self, plan: List[Dict[str, Any]], instruction: str) -> Dict[str, Any]:
        """
        Execute the plan.
        
        Args:
            plan: The plan to execute
            instruction: The original instruction
            
        Returns:
            Dict: The result of executing the plan
        """
        context = {
            "instruction": instruction,
            "files": {},
            "changes": [],
            "explanation": None,
            "error": None
        }
        
        for step in plan:
            action = step.get("action")
            logger.debug(f"Executing step: {action}")
            
            try:
                if action == "read_file":
                    file_path = step.get("file_path")
                    content = await self.file_manager.read_file(file_path)
                    context["files"][file_path] = content
                
                elif action == "search_files":
                    criteria = step.get("criteria", {})
                    files = await self.file_manager.search_files(criteria)
                    
                    for file_path in files:
                        if file_path not in context["files"]:
                            content = await self.file_manager.read_file(file_path)
                            context["files"][file_path] = content
                
                elif action == "generate_changes":
                    task_type = step.get("task_type")
                    changes = await self._generate_code_changes(task_type, context)
                    context["changes"] = changes
                
                elif action == "present_changes":
                    # This is handled by the CLI interface after agent returns
                    pass
                
                elif action == "confirm_changes":
                    # This is handled by the CLI interface after agent returns
                    pass
                
                elif action == "apply_changes":
                    # This is handled by the CLI interface after confirmation
                    pass
                
                elif action == "generate_explanation":
                    explanation = await self._generate_explanation(context)
                    context["explanation"] = explanation
                
                elif action == "present_explanation":
                    # This is handled by the CLI interface after agent returns
                    pass
                
                elif action == "git_stage_changes":
                    # This is handled by the CLI interface after changes are applied
                    pass
                
                elif action == "git_commit_changes":
                    # This is handled by the CLI interface after changes are applied
                    pass
                
                else:
                    logger.warning(f"Unknown action: {action}")
            
            except Exception as e:
                logger.error(f"Error executing step {action}: {str(e)}")
                context["error"] = f"Error in {action}: {str(e)}"
                break
        
        return context
    
    async def _generate_code_changes(self, task_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate code changes using the model.
        
        Args:
            task_type: The type of task to execute
            context: The current execution context
            
        Returns:
            List[Dict]: A list of changes to apply
        """
        instruction = context.get("instruction", "")
        files = context.get("files", {})
        
        # Prepare the prompt
        prompt = self._create_code_generation_prompt(task_type, instruction, files)
        
        # Call the model
        response = await self.model.generate(prompt)
        
        if response.has_error:
            raise Exception(f"Model error: {response.error}")
        
        # Parse the response to extract code changes
        changes = self._parse_code_changes(response.content, files)
        
        return changes
    
    def _create_code_generation_prompt(
        self, 
        task_type: str, 
        instruction: str, 
        files: Dict[str, str]
    ) -> str:
        """
        Create a prompt for code generation.
        
        Args:
            task_type: The type of task to execute
            instruction: The original instruction
            files: The files to modify
            
        Returns:
            str: The prompt for code generation
        """
        prompt = f"""You are DeepCoder, an expert AI coding assistant that helps modify code based on user instructions.

TASK TYPE: {task_type}

INSTRUCTION: {instruction}

RELEVANT FILES:
"""
        
        for file_path, content in files.items():
            prompt += f"\n--- {file_path} ---\n{content}\n"
        
        prompt += """
Based on the instruction and the code provided, generate the necessary changes.
Your response should be structured as follows:

For each file that needs modifications:

FILE: <file_path>
```
<entire new file content>
```

Explain your changes briefly after each file.

Remember:
1. Only include files that need modifications
2. Always provide the ENTIRE new file content, not just the changes
3. Include sensible code comments where appropriate
4. Ensure the code is correct, idiomatic, and follows best practices
"""
        
        return prompt
    
    def _parse_code_changes(
        self, 
        model_response: str, 
        original_files: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Parse the model response to extract code changes.
        
        Args:
            model_response: The model's response
            original_files: The original file contents
            
        Returns:
            List[Dict]: A list of changes to apply
        """
        changes = []
        
        # Split the response by file sections
        file_sections = model_response.split("FILE: ")
        
        for section in file_sections[1:]:  # Skip the first empty section
            # Extract the file path
            file_path_end = section.find("\n")
            file_path = section[:file_path_end].strip()
            
            # Extract the new content
            content_start = section.find("```") + 3
            content_end = section.find("```", content_start)
            
            if content_start == 2 or content_end == -1:  # Invalid format
                continue
            
            new_content = section[content_start:content_end].strip()
            
            # Check if we have the original file content
            if file_path in original_files:
                original_content = original_files[file_path]
                
                # Create a diff
                diff = create_diff(original_content, new_content, file_path)
                
                # Add the change
                changes.append({
                    "file_path": file_path,
                    "original_content": original_content,
                    "new_content": new_content,
                    "diff": diff
                })
            else:
                # This is a new file
                changes.append({
                    "file_path": file_path,
                    "original_content": "",
                    "new_content": new_content,
                    "is_new_file": True,
                    "diff": create_diff("", new_content, file_path)
                })
        
        return changes
    
    async def _generate_explanation(self, context: Dict[str, Any]) -> str:
        """
        Generate an explanation using the model.
        
        Args:
            context: The current execution context
            
        Returns:
            str: The generated explanation
        """
        instruction = context.get("instruction", "")
        files = context.get("files", {})
        
        # Prepare the prompt
        prompt = f"""You are DeepCoder, an expert AI coding assistant that helps explain code.

INSTRUCTION: {instruction}

RELEVANT FILES:
"""
        
        for file_path, content in files.items():
            prompt += f"\n--- {file_path} ---\n{content}\n"
        
        prompt += """
Based on the instruction and the code provided, provide a detailed explanation.
Focus on clarity, accuracy, and providing insights that would be helpful to the user.
"""
        
        # Call the model
        response = await self.model.generate(prompt)
        
        if response.has_error:
            raise Exception(f"Model error: {response.error}")
        
        return response.content