#!/usr/bin/env python3
"""
Installation script for DeepCoder.
This script will:
1. Install required dependencies
2. Create a basic configuration
3. Provide instructions for running DeepCoder
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_and_install_dependencies():
    """Check and install required dependencies."""
    print("Checking and installing dependencies...")
    
    required_packages = [
        "typer",
        "rich",
        "pyyaml",
        "python-dotenv",
        "openai",
        "requests",
        "gitpython",
        "aiohttp"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("All dependencies installed successfully!")

def create_basic_config():
    """Create a basic configuration file in the project directory."""
    print("\nCreating basic configuration...")
    
    config = {
        "model": {
            "platform": "togetherai",
            "together_api_key": "YOUR_API_KEY_HERE",
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
    
    try:
        import yaml
        config_path = Path.cwd() / ".deepcoder.yaml"
        
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"Basic configuration created at {config_path}")
        print("Edit this file to add your API keys before using DeepCoder")
    except Exception as e:
        print(f"Failed to create configuration: {str(e)}")

def create_run_script():
    """Create a run script to make it easier to execute DeepCoder."""
    print("\nCreating run script...")
    
    script_content = """#!/usr/bin/env python3
import os
import sys
import importlib.util

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for required packages
required_packages = ["typer", "rich", "pyyaml", "python-dotenv", "openai", "requests", "gitpython", "aiohttp"]
missing_packages = []

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        missing_packages.append(package)

if missing_packages:
    print(f"Missing required packages: {', '.join(missing_packages)}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Import and run the application
from cli.main import app
app()
"""
    
    run_script_path = Path.cwd() / "run_deepcoder.py"
    
    with open(run_script_path, "w") as f:
        f.write(script_content)
    
    os.chmod(run_script_path, 0o755)  # Make executable
    
    print(f"Run script created at {run_script_path}")

def create_requirements_file():
    """Create a requirements.txt file."""
    print("\nCreating requirements.txt file...")
    
    requirements = """typer>=0.9.0
rich>=13.3.5
pyyaml>=6.0
python-dotenv>=1.0.0
openai>=1.3.0
requests>=2.28.2
gitpython>=3.1.31
aiohttp>=3.8.0
"""
    
    req_path = Path.cwd() / "requirements.txt"
    
    with open(req_path, "w") as f:
        f.write(requirements)
    
    print(f"Requirements file created at {req_path}")

def main():
    """Main installation function."""
    print("=== DeepCoder Installation ===\n")
    
    check_and_install_dependencies()
    create_basic_config()
    create_run_script()
    create_requirements_file()
    
    print("\n=== Installation Complete ===")
    print("\nTo run DeepCoder:")
    print("1. Edit .deepcoder.yaml to add your API keys")
    print("2. Run one of these commands:")
    print("   python run_deepcoder.py \"Your instruction here\"")
    print("   python run_simple.py \"Your instruction here\" (recommended if you have import issues)")
    print("\nOr install the package:")
    print("   pip install -r requirements.txt")
    print("   pip install -e .")
    print("   deepcoder \"Your instruction here\"")

if __name__ == "__main__":
    main()