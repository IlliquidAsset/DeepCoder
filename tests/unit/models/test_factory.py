"""
Unit tests for model factory module.
"""
import pytest
from unittest.mock import patch

from deepcoder.models.factory import create_model
from deepcoder.models.together import TogetherAIModel
from deepcoder.models.lightning import LightningAIModel


class TestModelFactory:
    """Tests for model factory."""
    
    def test_create_togetherai_model(self):
        """Test creating a Together.ai model."""
        config = {
            "platform": "togetherai",
            "together_api_key": "test_key",
            "parameters": {
                "temperature": 0.5
            }
        }
        
        with patch('deepcoder.models.together.TogetherAIModel.__init__', return_value=None):
            model = create_model(config)
            assert isinstance(model, TogetherAIModel)
    
    def test_create_lightningai_model(self):
        """Test creating a Lightning AI model."""
        config = {
            "platform": "lightningai",
            "lightning_endpoint_url": "https://api.lightning.ai/model",
            "lightning_api_key": "test_key",
            "parameters": {
                "temperature": 0.5
            }
        }
        
        with patch('deepcoder.models.lightning.LightningAIModel.__init__', return_value=None):
            model = create_model(config)
            assert isinstance(model, LightningAIModel)
    
    def test_unsupported_platform(self):
        """Test error is raised for unsupported platform."""
        config = {
            "platform": "unsupported",
            "parameters": {}
        }
        
        with pytest.raises(ValueError, match="Unsupported model platform"):
            create_model(config)