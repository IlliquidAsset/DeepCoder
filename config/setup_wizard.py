"""
Setup wizard for DeepCoder CLI.
"""
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


def run_setup_wizard() -> Dict[str, Any]:
    """
    Run the setup wizard to configure DeepCoder.
    
    Returns:
        Dict: The configuration dictionary
    """
    console.print("\n[bold blue]DeepCoder Setup Wizard[/bold blue]")
    console.print("This wizard will help you configure DeepCoder for first use.\n")
    
    # Initialize config with default values
    config = {
        "model": {
            "platform": "togetherai",
            "parameters": {
                "temperature": 0.2,
                "max_tokens": 2000,
                "top_p": 0.95,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            }
        },
        "logging": {
            "level": "INFO",
        },
        "git": {
            "auto_stage": False,
            "auto_commit": False,
        }
    }
    
    # Get platform selection
    platform = Prompt.ask(
        "Select model platform",
        choices=["togetherai", "lightningai"],
        default="togetherai"
    )
    config["model"]["platform"] = platform
    
    # Get API keys and endpoints based on platform
    if platform == "togetherai":
        api_key = Prompt.ask(
            "Enter your Together.ai API key",
            password=True
        )
        config["model"]["together_api_key"] = api_key
    else:  # lightningai
        endpoint_url = Prompt.ask(
            "Enter your Lightning AI endpoint URL",
            default="https://api.lightning.ai/v1"
        )
        api_key = Prompt.ask(
            "Enter your Lightning AI API key",
            password=True
        )
        config["model"]["lightning_endpoint_url"] = endpoint_url
        config["model"]["lightning_api_key"] = api_key
    
    # Get model parameters
    if Confirm.ask("Would you like to configure advanced model parameters?", default=False):
        temperature = float(Prompt.ask(
            "Temperature (0.0-1.0)",
            default="0.2"
        ))
        max_tokens = int(Prompt.ask(
            "Maximum tokens to generate",
            default="2000"
        ))
        
        config["model"]["parameters"]["temperature"] = temperature
        config["model"]["parameters"]["max_tokens"] = max_tokens
    
    # Get Git preferences
    if Confirm.ask("Would you like to configure Git integration?", default=True):
        auto_stage = Confirm.ask(
            "Automatically stage changes in Git?",
            default=False
        )
        auto_commit = False
        if auto_stage:
            auto_commit = Confirm.ask(
                "Automatically commit changes?",
                default=False
            )
        
        config["git"]["auto_stage"] = auto_stage
        config["git"]["auto_commit"] = auto_commit
    
    # Save configuration
    save_location = Prompt.ask(
        "Where would you like to save the configuration?",
        choices=["user", "project", "environment"],
        default="user"
    )
    
    if save_location == "user":
        save_config_to_user(config)
    elif save_location == "project":
        save_config_to_project(config)
    elif save_location == "environment":
        save_config_to_environment(config)
    
    return config


def save_config_to_user(config: Dict[str, Any]) -> None:
    """
    Save the configuration to the user's home directory.
    
    Args:
        config: The configuration dictionary
    """
    # Create config directory if it doesn't exist
    config_dir = Path.home() / ".config" / "deepcoder"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Save config file
    config_path = config_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    console.print(f"\n[green]Configuration saved to {config_path}[/green]")


def save_config_to_project(config: Dict[str, Any]) -> None:
    """
    Save the configuration to the current project directory.
    
    Args:
        config: The configuration dictionary
    """
    # Save to .deepcoder.yaml in current directory
    config_path = Path.cwd() / ".deepcoder.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    console.print(f"\n[green]Configuration saved to {config_path}[/green]")
    
    # Add to .gitignore if it exists and doesn't already ignore .deepcoder.yaml
    gitignore_path = Path.cwd() / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
        
        if ".deepcoder.yaml" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# DeepCoder configuration\n.deepcoder.yaml\n")
            console.print("[green]Added .deepcoder.yaml to .gitignore[/green]")


def save_config_to_environment(config: Dict[str, Any]) -> None:
    """
    Save the configuration as environment variables.
    
    Args:
        config: The configuration dictionary
    """
    env_vars = []
    
    # Platform
    env_vars.append(f"export MODEL_HOST_PLATFORM={config['model']['platform']}")
    
    # API keys and endpoints
    if config['model']['platform'] == "togetherai":
        env_vars.append(f"export TOGETHER_API_KEY={config['model']['together_api_key']}")
    else:  # lightningai
        env_vars.append(f"export LIGHTNING_ENDPOINT_URL={config['model']['lightning_endpoint_url']}")
        env_vars.append(f"export LIGHTNING_API_KEY={config['model']['lightning_api_key']}")
    
    # Model parameters
    env_vars.append(f"export DEEPCODER_MODEL_TEMPERATURE={config['model']['parameters']['temperature']}")
    env_vars.append(f"export DEEPCODER_MODEL_MAX_TOKENS={config['model']['parameters']['max_tokens']}")
    
    # Git settings
    env_vars.append(f"export DEEPCODER_GIT_AUTO_STAGE={'true' if config['git']['auto_stage'] else 'false'}")
    env_vars.append(f"export DEEPCODER_GIT_AUTO_COMMIT={'true' if config['git']['auto_commit'] else 'false'}")
    
    # Print environment variables to console
    console.print("\n[bold]Add these environment variables to your shell configuration:[/bold]")
    for var in env_vars:
        console.print(var)
    
    # Offer to create .env file
    if Confirm.ask("Would you like to create a .env file in the current directory?", default=True):
        env_path = Path.cwd() / ".env"
        with open(env_path, "w") as f:
            for var in env_vars:
                f.write(f"{var.replace('export ', '')}\n")
        
        console.print(f"\n[green]Environment variables saved to {env_path}[/green]")
        
        # Add to .gitignore if it exists and doesn't already ignore .env
        gitignore_path = Path.cwd() / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                content = f.read()
            
            if ".env" not in content:
                with open(gitignore_path, "a") as f:
                    f.write("\n# Environment variables\n.env\n")
                console.print("[green]Added .env to .gitignore[/green]")


def check_first_run() -> bool:
    """
    Check if this is the first run of DeepCoder.
    
    Returns:
        bool: True if this is the first run, False otherwise
    """
    # Check for user config
    user_config = Path.home() / ".config" / "deepcoder" / "config.yaml"
    if user_config.exists():
        return False
    
    # Check for project config
    project_config = Path.cwd() / ".deepcoder.yaml"
    if project_config.exists():
        return False
    
    # Check for complete set of environment variables
    # We need either Together.ai or Lightning AI variables completely set
    togetherai_complete = bool(os.environ.get("TOGETHER_API_KEY"))
    lightningai_complete = bool(os.environ.get("LIGHTNING_ENDPOINT_URL") and 
                               os.environ.get("LIGHTNING_API_KEY"))
    
    if togetherai_complete or lightningai_complete:
        return False
    
    return True