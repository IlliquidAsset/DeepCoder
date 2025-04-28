#!/usr/bin/env python3
import os
import sys
import importlib.util

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for required packages
required_packages = {
    "typer": "typer", 
    "rich": "rich", 
    "pyyaml": "yaml", 
    "python-dotenv": "dotenv", 
    "openai": "openai", 
    "requests": "requests", 
    "gitpython": "git", 
    "aiohttp": "aiohttp",
    "lightning": "lightning"
}
missing_packages = []

for package_name, import_name in required_packages.items():
    if importlib.util.find_spec(import_name) is None:
        missing_packages.append(package_name)

if missing_packages:
    print(f"Missing required packages: {', '.join(missing_packages)}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Import and run the application
from cli.main import app
app()
