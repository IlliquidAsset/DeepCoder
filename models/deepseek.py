"""
DeepSeek model integration for DeepCoder CLI.
"""
import os
import json
import aiohttp
from typing import Dict, Any, Optional, List

from models.base import BaseModel, ModelResponse


class DeepSeekModel(BaseModel):
    """DeepSeek model implementation."""
    
    # Default API endpoint (platform.deepseek.com)
    API_BASE = "https://api.deepseek.com/v1"
    
    # Available DeepSeek models
    MODELS = {
        "coder-v3": "deepseek-ai/deepseek-coder-v3",
        "v3-base": "deepseek-ai/deepseek-v3-base",
        "r1": "deepseek-ai/deepseek-r1"
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DeepSeek model.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        super().__init__(config)
        self.api_key = config.get("deepseek_api_key")
        
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        
        # Set up endpoint - either direct or through Lightning.ai
        self.use_lightning = config.get("use_lightning", False)
        
        if self.use_lightning:
            self.endpoint_url = config.get("lightning_endpoint_url")
            self.lightning_api_key = config.get("lightning_api_key")
            
            if not self.endpoint_url:
                raise ValueError("Lightning AI endpoint URL is required when use_lightning=True")
            
            if not self.lightning_api_key:
                raise ValueError("Lightning AI API key is required when use_lightning=True")
        else:
            # Direct DeepSeek platform usage
            self.api_base = config.get("api_base", self.API_BASE)
        
        # Set the model name
        model_type = config.get("model_type", "coder-v3")
        self.model_name = self.MODELS.get(model_type, self.MODELS["coder-v3"])
    
    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response from the DeepSeek model.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            ModelResponse: The model's response
        """
        if self.use_lightning:
            return await self._generate_via_lightning(prompt)
        else:
            return await self._generate_direct(prompt)
    
    async def _generate_direct(self, prompt: str) -> ModelResponse:
        """
        Generate response directly using the DeepSeek API.
        
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
    
    async def _generate_via_lightning(self, prompt: str) -> ModelResponse:
        """
        Generate response using the DeepSeek model via Lightning.ai.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            ModelResponse: The model's response
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.lightning_api_key}",
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
        Get information about the DeepSeek model.
        
        Returns:
            Dict: Information about the model
        """
        if self.use_lightning:
            return {
                "provider": "DeepSeek via Lightning AI",
                "model": self.model_name,
                "endpoint": self.endpoint_url,
                "parameters": self.model_params
            }
        else:
            return {
                "provider": "DeepSeek",
                "model": self.model_name,
                "api_base": self.api_base,
                "parameters": self.model_params
            }