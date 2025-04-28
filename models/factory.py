"""
Model factory for DeepCoder CLI.
"""
from typing import Dict, Any

from deepcoder.models.base import BaseModel
from deepcoder.models.together import TogetherAIModel
from deepcoder.models.lightning import LightningAIModel


def create_model(config: Dict[str, Any]) -> BaseModel:
    """
    Create an appropriate model instance based on the configuration.
    
    Args:
        config: Configuration dictionary containing model settings
        
    Returns:
        BaseModel: An instance of the appropriate model
        
    Raises:
        ValueError: If the specified platform is not supported
    """
    platform = config.get("platform", "").lower()
    
    if platform == "togetherai":
        return TogetherAIModel(config)
    elif platform == "lightningai":
        return LightningAIModel(config)
    else:
        raise ValueError(f"Unsupported model platform: {platform}")