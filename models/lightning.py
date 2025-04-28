"""
Lightning AI model integration for DeepCoder CLI.
"""
import os
import json
import aiohttp
from typing import Dict, Any, Optional, List

from models.base import BaseModel, ModelResponse


class LightningAIModel(BaseModel):
    """Lightning AI model implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Lightning AI model.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        super().__init__(config)
        self.endpoint_url = config.get("lightning_endpoint_url")
        self.api_key = config.get("lightning_api_key")
        
        if not self.endpoint_url:
            raise ValueError("Lightning AI endpoint URL is required")
        
        if not self.api_key:
            raise ValueError("Lightning AI API key is required")
    
    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response from the Lightning AI model.
        
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
                    self.endpoint_url, 
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
                    
                    # Lightning AI endpoints might have different response formats
                    # This implementation assumes an OpenAI-compatible format
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
        Get information about the Lightning AI model.
        
        Returns:
            Dict: Information about the model
        """
        return {
            "provider": "Lightning AI",
            "endpoint": self.endpoint_url,
            "parameters": self.model_params
        }