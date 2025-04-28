#!/usr/bin/env python
"""
A standalone script to run the DeepCoder setup wizard.
"""
import sys
import os
import yaml
from pathlib import Path


def run_setup(use_defaults=False):
    """
    Run the DeepCoder setup wizard in a simple non-interactive way.
    
    Args:
        use_defaults: Whether to use default values for all prompts
    """
    print("DeepCoder Setup Wizard")
    print("======================")
    print("")
    
    if use_defaults:
        platform = "togetherai"
        api_key = "YOUR_API_KEY_HERE"
        endpoint_url = "https://api.lightning.ai/v1"
        save_location = "2"  # Project config
    else:
        try:
            # Get platform
            platform = input("Select model platform (togetherai/lightningai) [togetherai]: ").strip().lower()
            if not platform:
                platform = "togetherai"
            
            if platform not in ["togetherai", "lightningai"]:
                print(f"Invalid platform: {platform}")
                print("Using default: togetherai")
                platform = "togetherai"
            
            # Get API keys based on platform
            if platform == "togetherai":
                api_key = input("Enter your Together.ai API key: ").strip()
                if not api_key:
                    api_key = "YOUR_API_KEY_HERE"
                    print("Using placeholder API key. You will need to update this later.")
            else:  # lightningai
                endpoint_url = input("Enter your Lightning AI endpoint URL [https://api.lightning.ai/v1]: ").strip()
                if not endpoint_url:
                    endpoint_url = "https://api.lightning.ai/v1"
                
                api_key = input("Enter your Lightning AI API key: ").strip()
                if not api_key:
                    api_key = "YOUR_API_KEY_HERE"
                    print("Using placeholder API key. You will need to update this later.")
            
            # Ask about saving location
            print("\nWhere would you like to save the configuration?")
            print("1. User config (~/.config/deepcoder/config.yaml)")
            print("2. Project config (.deepcoder.yaml in current directory)")
            print("3. Environment variables (.env file in current directory)")
            
            save_location = input("Enter your choice (1-3) [2]: ").strip()
            if not save_location:
                save_location = "2"
        
        except (EOFError, KeyboardInterrupt):
            print("\nDetected input issues. Using default values.")
            platform = "togetherai"
            api_key = "YOUR_API_KEY_HERE"
            endpoint_url = "https://api.lightning.ai/v1"
            save_location = "2"  # Project config
    
    # Initialize config
    config = {
        "model": {
            "platform": platform,
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
    
    # Add API keys based on platform
    if platform == "togetherai":
        config["model"]["together_api_key"] = api_key
    else:  # lightningai
        config["model"]["lightning_endpoint_url"] = endpoint_url
        config["model"]["lightning_api_key"] = api_key
    
    # Save configuration based on location choice
    if save_location == "1":
        # User config
        config_dir = Path.home() / ".config" / "deepcoder"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.yaml"
        
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"\nConfiguration saved to {config_path}")
    
    elif save_location == "2":
        # Project config
        config_path = Path.cwd() / ".deepcoder.yaml"
        
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"\nConfiguration saved to {config_path}")
        
        # Add to .gitignore if it exists and doesn't already ignore .deepcoder.yaml
        gitignore_path = Path.cwd() / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                content = f.read()
            
            if ".deepcoder.yaml" not in content:
                with open(gitignore_path, "a") as f:
                    f.write("\n# DeepCoder configuration\n.deepcoder.yaml\n")
                print("Added .deepcoder.yaml to .gitignore")
    
    elif save_location == "3":
        # Environment variables
        env_path = Path.cwd() / ".env"
        
        with open(env_path, "w") as f:
            f.write(f"MODEL_HOST_PLATFORM={config['model']['platform']}\n")
            
            if platform == "togetherai":
                f.write(f"TOGETHER_API_KEY={config['model']['together_api_key']}\n")
            else:  # lightningai
                f.write(f"LIGHTNING_ENDPOINT_URL={config['model']['lightning_endpoint_url']}\n")
                f.write(f"LIGHTNING_API_KEY={config['model']['lightning_api_key']}\n")
            
            f.write(f"DEEPCODER_MODEL_TEMPERATURE={config['model']['parameters']['temperature']}\n")
            f.write(f"DEEPCODER_MODEL_MAX_TOKENS={config['model']['parameters']['max_tokens']}\n")
        
        print(f"\nEnvironment variables saved to {env_path}")
        
        # Add to .gitignore if it exists and doesn't already ignore .env
        gitignore_path = Path.cwd() / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                content = f.read()
            
            if ".env" not in content:
                with open(gitignore_path, "a") as f:
                    f.write("\n# Environment variables\n.env\n")
                print("Added .env to .gitignore")
    
    else:
        print(f"\nInvalid choice: {save_location}. Using project config.")
        # Project config
        config_path = Path.cwd() / ".deepcoder.yaml"
        
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"\nConfiguration saved to {config_path}")
    
    print("\nSetup complete! You can now use DeepCoder with your configuration.")
    print("\nIMPORTANT: If you used placeholder API keys, update your configuration with real API keys before using DeepCoder.")


if __name__ == "__main__":
    # Check if --defaults flag is passed
    use_defaults = "--defaults" in sys.argv
    
    try:
        run_setup(use_defaults=use_defaults)
    except Exception as e:
        print(f"\nError during setup: {str(e)}")
        print("Attempting to create a default configuration file...")
        try:
            run_setup(use_defaults=True)
        except Exception as e:
            print(f"\nFailed to create default configuration: {str(e)}")
            sys.exit(1)