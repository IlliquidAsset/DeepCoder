"""
Unit tests for Lightning AI model implementation.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from deepcoder.models.lightning import LightningAIModel


class TestLightningAIModel:
    """Tests for Lightning AI model implementation."""
    
    def test_initialization(self):
        """Test model initialization."""
        config = {
            "lightning_endpoint_url": "https://api.lightning.ai/model",
            "lightning_api_key": "test_key",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
        
        model = LightningAIModel(config)
        
        assert model.endpoint_url == "https://api.lightning.ai/model"
        assert model.api_key == "test_key"
        assert model.model_params["temperature"] == 0.5
        assert model.model_params["max_tokens"] == 1000
    
    def test_initialization_without_endpoint_url(self):
        """Test model initialization without endpoint URL."""
        config = {
            "lightning_api_key": "test_key",
            "parameters": {}
        }
        
        with pytest.raises(ValueError, match="Lightning AI endpoint URL is required"):
            LightningAIModel(config)
    
    def test_initialization_without_api_key(self):
        """Test model initialization without API key."""
        config = {
            "lightning_endpoint_url": "https://api.lightning.ai/model",
            "parameters": {}
        }
        
        with pytest.raises(ValueError, match="Lightning AI API key is required"):
            LightningAIModel(config)
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation."""
        config = {
            "lightning_endpoint_url": "https://api.lightning.ai/model",
            "lightning_api_key": "test_key",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
        
        model = LightningAIModel(config)
        
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
            "lightning_endpoint_url": "https://api.lightning.ai/model",
            "lightning_api_key": "test_key",
            "parameters": {}
        }
        
        model = LightningAIModel(config)
        
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
            "lightning_endpoint_url": "https://api.lightning.ai/model",
            "lightning_api_key": "test_key",
            "parameters": {}
        }
        
        model = LightningAIModel(config)
        
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
            "lightning_endpoint_url": "https://api.lightning.ai/model",
            "lightning_api_key": "test_key",
            "parameters": {
                "temperature": 0.5
            }
        }
        
        model = LightningAIModel(config)
        info = model.get_model_info()
        
        assert info["provider"] == "Lightning AI"
        assert info["endpoint"] == model.endpoint_url
        assert info["parameters"]["temperature"] == 0.5