#!/usr/bin/env python3
"""
Standalone runner for DeepCoder.
This script adds the necessary directories to the Python path and runs the DeepCoder CLI.
"""
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
    print("Please run: python install.py")
    sys.exit(1)

try:
    # Import and run the application
    from cli.main import app
    app()
except ModuleNotFoundError as e:
    print(f"Error: {e}")
    print("\nThe deepcoder package couldn't be imported. Make sure you're running this script from the project root directory.")
    print("If the issue persists, try running: python install.py")
    sys.exit(1)
except ImportError as e:
    print(f"Import error: {e}")
    print("\nThere was a problem importing the necessary modules.")
    print("Please make sure all dependencies are installed by running: python install.py")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)