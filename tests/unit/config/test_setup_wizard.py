"""
Unit tests for setup wizard module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from deepcoder.config.setup_wizard import check_first_run, run_setup_wizard


class TestSetupWizard:
    """Tests for the setup wizard module."""
    
    def test_check_first_run_with_user_config(self):
        """Test check_first_run with existing user config."""
        with patch('pathlib.Path.exists', return_value=True):
            assert not check_first_run()
    
    def test_check_first_run_without_configs(self):
        """Test check_first_run without any existing configs."""
        with patch('pathlib.Path.exists', return_value=False), \
             patch.dict(os.environ, {}, clear=True):
            assert check_first_run()
    
    def test_check_first_run_with_env_vars(self):
        """Test check_first_run with environment variables."""
        with patch('pathlib.Path.exists', return_value=False), \
             patch.dict(os.environ, {"TOGETHER_API_KEY": "test_key"}):
            assert not check_first_run()
    
    @pytest.mark.parametrize("platform,expected_keys", [
        ("togetherai", ["together_api_key"]),
        ("lightningai", ["lightning_endpoint_url", "lightning_api_key"])
    ])
    def test_run_setup_wizard(self, platform, expected_keys):
        """Test run_setup_wizard with different platforms."""
        # Mock all the Prompt.ask and Confirm.ask calls
        with patch('rich.prompt.Prompt.ask', side_effect=[
                platform,                        # platform selection
                "test_key" if platform == "togetherai" else "https://api.lightning.ai/v1",  # API key or endpoint URL
                "test_key" if platform == "lightningai" else None,  # API key for lightningai
                "n",                             # advanced params
                "n",                             # git integration
                "user"                           # save location
            ]), \
             patch('rich.prompt.Confirm.ask', return_value=False), \
             patch('deepcoder.config.setup_wizard.save_config_to_user') as mock_save:
            
            config = run_setup_wizard()
            
            # Check that the config contains the expected values
            assert config["model"]["platform"] == platform
            for key in expected_keys:
                assert key in config["model"]
                assert config["model"][key] is not None
            
            # Check that save_config_to_user was called
            mock_save.assert_called_once_with(config)
    
    def test_save_config_to_user(self):
        """Test saving config to user directory."""
        mock_config = {"test": "config"}
        
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', MagicMock()), \
             patch('yaml.dump') as mock_dump, \
             patch('rich.console.Console.print') as mock_print:
            
            from deepcoder.config.setup_wizard import save_config_to_user
            save_config_to_user(mock_config)
            
            # Check that directory was created
            mock_mkdir.assert_called_once()
            
            # Check that yaml.dump was called with the config
            mock_dump.assert_called_once()
            assert mock_dump.call_args[0][0] == mock_config
            
            # Check that a success message was printed
            mock_print.assert_called_once()
    
    def test_save_config_to_project(self):
        """Test saving config to project directory."""
        mock_config = {"test": "config"}
        
        with patch('builtins.open', MagicMock()), \
             patch('yaml.dump') as mock_dump, \
             patch('pathlib.Path.exists', return_value=True), \
             patch('rich.console.Console.print') as mock_print:
            
            from deepcoder.config.setup_wizard import save_config_to_project
            save_config_to_project(mock_config)
            
            # Check that yaml.dump was called with the config
            mock_dump.assert_called_once()
            assert mock_dump.call_args[0][0] == mock_config
            
            # Check that a success message was printed
            assert mock_print.call_count > 0
    
    def test_save_config_to_environment(self):
        """Test saving config to environment variables."""
        mock_config = {
            "model": {
                "platform": "togetherai",
                "together_api_key": "test_key",
                "parameters": {
                    "temperature": 0.5,
                    "max_tokens": 1000
                }
            },
            "git": {
                "auto_stage": True,
                "auto_commit": False
            }
        }
        
        with patch('rich.console.Console.print') as mock_print, \
             patch('rich.prompt.Confirm.ask', return_value=False):
            
            from deepcoder.config.setup_wizard import save_config_to_environment
            save_config_to_environment(mock_config)
            
            # Check that environment variables were printed
            assert mock_print.call_count > 0
            
            # Check for expected environment variables in output
            env_vars = [
                "MODEL_HOST_PLATFORM=togetherai",
                "TOGETHER_API_KEY=test_key",
                "DEEPCODER_MODEL_TEMPERATURE=0.5",
                "DEEPCODER_MODEL_MAX_TOKENS=1000",
                "DEEPCODER_GIT_AUTO_STAGE=true",
                "DEEPCODER_GIT_AUTO_COMMIT=false"
            ]
            
            for var in env_vars:
                var_printed = False
                for call in mock_print.call_args_list:
                    if var in str(call):
                        var_printed = True
                        break
                assert var_printed, f"Environment variable {var} not printed"