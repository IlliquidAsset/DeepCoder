"""
Configuration handling for DeepCoder CLI.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Default configuration
DEFAULT_CONFIG = {
    "model": {
        "platform": "togetherai",  # or "lightningai"
        "together_api_key": None,
        "lightning_endpoint_url": None,
        "lightning_api_key": None,
        "parameters": {
            "temperature": 0.2,
            "max_tokens": 2000,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": None,
        },
    },
    "logging": {
        "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        "file": None,  # Path to log file (if None, logs to stderr)
    },
    "git": {
        "auto_stage": False,
        "auto_commit": False,
    },
}


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


def load_config_file() -> Dict[Any, Any]:
    """Load configuration from the config file if it exists."""
    config_paths = [
        Path.home() / ".config" / "deepcoder" / "config.yaml",
        Path.cwd() / ".deepcoder.yaml",
    ]

    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}

    return {}


def get_config(strict: bool = False) -> Dict[Any, Any]:
    """
    Load and validate the configuration from multiple sources:
    1. Default configuration
    2. Configuration file
    3. Environment variables
    
    Args:
        strict: Whether to strictly enforce validation rules
    
    Returns:
        Dict: The merged configuration
    """
    # Start with default config
    config = DEFAULT_CONFIG.copy()

    # Update with config file values
    file_config = load_config_file()
    _deep_update(config, file_config)

    # Update with environment variables
    env_config = _get_config_from_env()
    _deep_update(config, env_config)

    # Check if we should use strict validation
    # In interactive mode with no command, we can be more lenient
    use_strict = strict or not _is_interactive()
    
    # Validate with appropriate strictness
    _validate_config(config, strict=use_strict)

    return config


def _is_interactive() -> bool:
    """
    Check if we're running in an interactive terminal.
    
    Returns:
        bool: True if interactive, False otherwise
    """
    import sys
    return sys.stdin.isatty() and sys.stdout.isatty()


def _get_config_from_env() -> Dict[Any, Any]:
    """Extract configuration from environment variables."""
    env_config = {"model": {}}
    
    # Model host platform
    if model_platform := os.environ.get("MODEL_HOST_PLATFORM"):
        env_config["model"]["platform"] = model_platform.lower()
    
    # API keys and endpoints
    if together_api_key := os.environ.get("TOGETHER_API_KEY"):
        env_config["model"]["together_api_key"] = together_api_key
    
    if lightning_endpoint_url := os.environ.get("LIGHTNING_ENDPOINT_URL"):
        env_config["model"]["lightning_endpoint_url"] = lightning_endpoint_url
    
    if lightning_api_key := os.environ.get("LIGHTNING_API_KEY"):
        env_config["model"]["lightning_api_key"] = lightning_api_key
    
    # Logging
    if log_level := os.environ.get("DEEPCODER_LOG_LEVEL"):
        if "logging" not in env_config:
            env_config["logging"] = {}
        env_config["logging"]["level"] = log_level
    
    # Git settings
    if auto_stage := os.environ.get("DEEPCODER_GIT_AUTO_STAGE"):
        if "git" not in env_config:
            env_config["git"] = {}
        env_config["git"]["auto_stage"] = auto_stage.lower() in ("true", "1", "yes")
    
    if auto_commit := os.environ.get("DEEPCODER_GIT_AUTO_COMMIT"):
        if "git" not in env_config:
            env_config["git"] = {}
        env_config["git"]["auto_commit"] = auto_commit.lower() in ("true", "1", "yes")
    
    return env_config


def _deep_update(target, source):
    """Recursively update nested dictionaries."""
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


def _validate_config(config: Dict[Any, Any], strict: bool = True) -> None:
    """
    Validate configuration values.
    
    Args:
        config: The configuration dictionary
        strict: Whether to strictly enforce validation rules
    """
    platform = config["model"]["platform"].lower()
    
    if platform not in ["togetherai", "lightningai"]:
        raise ConfigurationError(
            f"Invalid model platform: {platform}. Must be 'togetherai' or 'lightningai'."
        )
    
    # Validate Together.ai configuration
    if platform == "togetherai" and not config["model"]["together_api_key"]:
        if strict:
            raise ConfigurationError(
                "Missing Together.ai API key. Please provide it via config file or TOGETHER_API_KEY environment variable."
            )
    
    # Validate Lightning AI configuration
    if platform == "lightningai":
        if not config["model"]["lightning_endpoint_url"]:
            if strict:
                raise ConfigurationError(
                    "Missing Lightning AI endpoint URL. Please provide it via config file or LIGHTNING_ENDPOINT_URL environment variable."
                )
        if not config["model"]["lightning_api_key"]:
            if strict:
                raise ConfigurationError(
                    "Missing Lightning AI API key. Please provide it via config file or LIGHTNING_API_KEY environment variable."
                )


def update_config_with_cli_args(config: Dict[Any, Any], cli_args: Dict[str, Any]) -> Dict[Any, Any]:
    """Update configuration with CLI arguments."""
    updated_config = config.copy()
    
    # Update model platform if provided
    if platform := cli_args.get("platform"):
        updated_config["model"]["platform"] = platform
    
    # Update model parameters if provided
    if "model_params" in cli_args:
        for param, value in cli_args["model_params"].items():
            if value is not None and param in updated_config["model"]["parameters"]:
                updated_config["model"]["parameters"][param] = value
    
    # Revalidate configuration after CLI updates
    _validate_config(updated_config)
    
    return updated_config