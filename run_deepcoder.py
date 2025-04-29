#!/usr/bin/env python3
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
