"""
Base model interface for DeepCoder CLI.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ModelResponse:
    """Container for model responses."""
    
    def __init__(
        self,
        content: str,
        raw_response: Dict[str, Any] = None,
        error: Optional[str] = None
    ):
        self.content = content
        self.raw_response = raw_response or {}
        self.error = error

    @property
    def has_error(self) -> bool:
        """Check if the response has an error."""
        return self.error is not None


class BaseModel(ABC):
    """Base class for model implementations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the model with configuration.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        self.config = config
        self.model_params = config.get("parameters", {})
    
    @abstractmethod
    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            ModelResponse: The model's response
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dict: Information about the model
        """
        pass