"""
Unit tests for configuration handling.
"""
import os
import pytest
from unittest.mock import patch
from pathlib import Path

from deepcoder.config.settings import (
    get_config, 
    update_config_with_cli_args, 
    ConfigurationError,
    _get_config_from_env
)


class TestConfig:
    """Tests for configuration handling."""
    
    def test_default_config(self):
        """Test that default configuration is loaded."""
        with patch('deepcoder.config.settings.load_config_file', return_value={}):
            with patch('deepcoder.config.settings._get_config_from_env', return_value={}):
                config = get_config()
                
                assert config["model"]["platform"] == "togetherai"
                assert config["model"]["parameters"]["temperature"] == 0.2
                assert config["model"]["parameters"]["max_tokens"] == 2000
    
    def test_update_config_with_cli_args(self):
        """Test updating configuration with CLI arguments."""
        base_config = {
            "model": {
                "platform": "togetherai",
                "parameters": {
                    "temperature": 0.2,
                    "max_tokens": 2000
                }
            }
        }
        
        cli_args = {
            "platform": "lightningai",
            "model_params": {
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
        
        updated_config = update_config_with_cli_args(base_config, cli_args)
        
        assert updated_config["model"]["platform"] == "lightningai"
        assert updated_config["model"]["parameters"]["temperature"] == 0.5
        assert updated_config["model"]["parameters"]["max_tokens"] == 1000
    
    def test_get_config_from_env(self):
        """Test extracting configuration from environment variables."""
        with patch.dict(os.environ, {
            "MODEL_HOST_PLATFORM": "lightningai",
            "LIGHTNING_ENDPOINT_URL": "https://api.lightning.ai/model",
            "LIGHTNING_API_KEY": "test_key",
            "DEEPCODER_LOG_LEVEL": "DEBUG"
        }):
            env_config = _get_config_from_env()
            
            assert env_config["model"]["platform"] == "lightningai"
            assert env_config["model"]["lightning_endpoint_url"] == "https://api.lightning.ai/model"
            assert env_config["model"]["lightning_api_key"] == "test_key"
            assert env_config["logging"]["level"] == "DEBUG"
    
    def test_config_validation_togetherai(self):
        """Test validation of Together.ai configuration."""
        config = {
            "model": {
                "platform": "togetherai",
                "together_api_key": None
            }
        }
        
        with pytest.raises(ConfigurationError, match="Missing Together.ai API key"):
            get_config = lambda: config  # Mock get_config to return our test config
            with patch('deepcoder.config.settings.get_config', get_config):
                from deepcoder.config.settings import _validate_config
                _validate_config(config)
    
    def test_config_validation_lightningai(self):
        """Test validation of Lightning AI configuration."""
        config = {
            "model": {
                "platform": "lightningai",
                "lightning_endpoint_url": None,
                "lightning_api_key": "test_key"
            }
        }
        
        with pytest.raises(ConfigurationError, match="Missing Lightning AI endpoint URL"):
            get_config = lambda: config  # Mock get_config to return our test config
            with patch('deepcoder.config.settings.get_config', get_config):
                from deepcoder.config.settings import _validate_config
                _validate_config(config)
        
        config["model"]["lightning_endpoint_url"] = "https://api.lightning.ai/model"
        config["model"]["lightning_api_key"] = None
        
        with pytest.raises(ConfigurationError, match="Missing Lightning AI API key"):
            get_config = lambda: config  # Mock get_config to return our test config
            with patch('deepcoder.config.settings.get_config', get_config):
                from deepcoder.config.settings import _validate_config
                _validate_config(config)