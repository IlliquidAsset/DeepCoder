"""
Together.ai model integration for DeepCoder CLI.
"""
import os
import json
import aiohttp
from typing import Dict, Any, Optional, List

from models.base import BaseModel, ModelResponse


class TogetherAIModel(BaseModel):
    """Together.ai model implementation."""
    
    API_BASE = "https://api.together.xyz/v1"
    MODEL_NAME = "deepseek-ai/deepseek-coder-v3"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Together.ai model.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        super().__init__(config)
        self.api_key = config.get("together_api_key")
        
        if not self.api_key:
            raise ValueError("Together.ai API key is required")
        
        # Override API base URL if specified in config
        self.api_base = config.get("api_base", self.API_BASE)
        
        # Set the model name
        self.model_name = config.get("model_name", self.MODEL_NAME)
    
    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response from the Together.ai model.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            ModelResponse: The model's response
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.model_params.get("temperature", 0.2),
                    "max_tokens": self.model_params.get("max_tokens", 2000),
                    "top_p": self.model_params.get("top_p", 0.95),
                    "frequency_penalty": self.model_params.get("frequency_penalty", 0.0),
                    "presence_penalty": self.model_params.get("presence_penalty", 0.0),
                }
                
                if stop_sequences := self.model_params.get("stop"):
                    payload["stop"] = stop_sequences
                
                async with session.post(
                    f"{self.api_base}/chat/completions", 
                    headers=headers, 
                    json=payload
                ) as response:
                    response_json = await response.json()
                    
                    if response.status != 200:
                        error_message = response_json.get("error", {}).get("message", str(response_json))
                        return ModelResponse(
                            content="",
                            raw_response=response_json,
                            error=f"API Error ({response.status}): {error_message}"
                        )
                    
                    content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return ModelResponse(content=content, raw_response=response_json)
        
        except aiohttp.ClientError as e:
            return ModelResponse(
                content="",
                error=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return ModelResponse(
                content="",
                error=f"Unexpected error: {str(e)}"
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Together.ai model.
        
        Returns:
            Dict: Information about the model
        """
        return {
            "provider": "Together.ai",
            "model": self.model_name,
            "api_base": self.api_base,
            "parameters": self.model_params
        }