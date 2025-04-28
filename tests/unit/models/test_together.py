"""
Unit tests for Together.ai model implementation.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from deepcoder.models.together import TogetherAIModel


class TestTogetherAIModel:
    """Tests for Together.ai model implementation."""
    
    def test_initialization(self):
        """Test model initialization."""
        config = {
            "together_api_key": "test_key",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
        
        model = TogetherAIModel(config)
        
        assert model.api_key == "test_key"
        assert model.api_base == TogetherAIModel.API_BASE
        assert model.model_name == TogetherAIModel.MODEL_NAME
        assert model.model_params["temperature"] == 0.5
        assert model.model_params["max_tokens"] == 1000
    
    def test_initialization_with_custom_base_url(self):
        """Test model initialization with custom base URL."""
        config = {
            "together_api_key": "test_key",
            "api_base": "https://custom.together.xyz/v1",
            "model_name": "custom-model",
            "parameters": {}
        }
        
        model = TogetherAIModel(config)
        
        assert model.api_key == "test_key"
        assert model.api_base == "https://custom.together.xyz/v1"
        assert model.model_name == "custom-model"
    
    def test_initialization_without_api_key(self):
        """Test model initialization without API key."""
        config = {
            "parameters": {}
        }
        
        with pytest.raises(ValueError, match="Together.ai API key is required"):
            TogetherAIModel(config)
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation."""
        config = {
            "together_api_key": "test_key",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
        
        model = TogetherAIModel(config)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        })
        
        # Mock ClientSession
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            response = await model.generate("Test prompt")
            
            assert not response.has_error
            assert response.content == "Test response"
    
    @pytest.mark.asyncio
    async def test_generate_api_error(self):
        """Test API error handling."""
        config = {
            "together_api_key": "test_key",
            "parameters": {}
        }
        
        model = TogetherAIModel(config)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={
            "error": {
                "message": "Bad request"
            }
        })
        
        # Mock ClientSession
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            response = await model.generate("Test prompt")
            
            assert response.has_error
            assert "API Error (400): Bad request" in response.error
    
    @pytest.mark.asyncio
    async def test_generate_connection_error(self):
        """Test connection error handling."""
        config = {
            "together_api_key": "test_key",
            "parameters": {}
        }
        
        model = TogetherAIModel(config)
        
        # Mock ClientSession to raise an exception
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("Connection error"))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            response = await model.generate("Test prompt")
            
            assert response.has_error
            assert "Unexpected error: Connection error" in response.error
    
    def test_get_model_info(self):
        """Test getting model info."""
        config = {
            "together_api_key": "test_key",
            "parameters": {
                "temperature": 0.5
            }
        }
        
        model = TogetherAIModel(config)
        info = model.get_model_info()
        
        assert info["provider"] == "Together.ai"
        assert info["model"] == model.model_name
        assert info["api_base"] == model.api_base
        assert info["parameters"]["temperature"] == 0.5