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

def install_cli_command():
    """Install DeepCoder as a CLI command."""
    print("\nInstalling DeepCoder CLI command...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        print("DeepCoder CLI command installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install CLI command: {str(e)}")
        print("You'll need to use 'python run_deepcoder.py' instead.")

def create_command_script():
    """Create standalone command script for direct execution."""
    print("\nCreating standalone command script...")
    
    bin_dir = Path.cwd() / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    script_content = """#!/bin/bash
# Script to run DeepCoder from anywhere

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Make sure we're using the project's python environment
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
elif [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/venv/bin/python"
else
    PYTHON="python"
fi

# Run DeepCoder
"$PYTHON" "$PROJECT_DIR/run_deepcoder.py" "$@"
"""
    
    script_path = bin_dir / "deepcoder"
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"Command script created at {script_path}")
    
    # Create installation script
    install_script_content = """#!/bin/bash
# Quick installer for DeepCoder command

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BIN_DIR="$SCRIPT_DIR/bin"

if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$BIN_DIR/deepcoder" "/usr/local/bin/deepcoder"
    echo "DeepCoder command installed to /usr/local/bin"
elif [ -d "$HOME/.local/bin" ]; then
    mkdir -p "$HOME/.local/bin"
    ln -sf "$BIN_DIR/deepcoder" "$HOME/.local/bin/deepcoder"
    echo "DeepCoder command installed to $HOME/.local/bin"
else
    echo "Could not install to system directory. Use $BIN_DIR/deepcoder directly."
fi
"""
    
    install_script_path = Path.cwd() / "install_command.sh"
    
    with open(install_script_path, "w") as f:
        f.write(install_script_content)
    
    # Make executable
    os.chmod(install_script_path, 0o755)
    
    print(f"Command installer created at {install_script_path}")
    return str(script_path)

def main():
    """Main installation function."""
    print("=== DeepCoder Installation ===\n")
    
    check_and_install_dependencies()
    create_basic_config()
    create_run_script()
    create_requirements_file()
    install_cli_command()
    command_script = create_command_script()
    
    print("\n=== Installation Complete ===")
    print("\nTo run DeepCoder:")
    print("1. Edit .deepcoder.yaml to add your API keys")
    print("2. Run using one of these methods:")
    print("\n   a) As a Python module (recommended):")
    print("      deepcoder")
    print("\n   b) Using the standalone script:")
    print(f"      {command_script}")
    print("\n   c) Install the command system-wide:")
    print("      ./install_command.sh")
    print("\nThis will start DeepCoder in interactive mode. To exit, type 'exit' or 'quit'.")
    print("\nYou can also run a single instruction:")
    print("   deepcoder \"Your instruction here\"")
    print("\nIf the CLI command doesn't work, use these alternatives:")
    print("   python run_deepcoder.py")
    print("   python run_simple.py")

if __name__ == "__main__":
    main()