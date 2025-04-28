"""
Model factory for DeepCoder CLI.
"""
from typing import Dict, Any

from models.base import BaseModel
from models.lightning import LightningAIModel
from models.deepseek import DeepSeekModel


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
    
    if platform == "lightningai":
        return LightningAIModel(config)
    elif platform == "deepseek":
        return DeepSeekModel(config)
    else:
        raise ValueError(f"Unsupported model platform: {platform}. Supported platforms: lightningai, deepseek")