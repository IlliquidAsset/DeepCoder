#!/usr/bin/env python3
"""
Simplified runner for DeepCoder.
This script directly calls the CLI script without complex imports.
"""
import os
import sys
import subprocess

# Get the absolute path to the cli/main.py script
current_dir = os.path.dirname(os.path.abspath(__file__))
main_script = os.path.join(current_dir, "cli", "main.py")

# Check if the main script exists
if not os.path.exists(main_script):
    print(f"Error: Could not find {main_script}")
    sys.exit(1)

# Get the command line arguments
args = sys.argv[1:]
args_str = " ".join(f'"{arg}"' for arg in args)

# Run the main script with the provided arguments
try:
    cmd = f"{sys.executable} {main_script} {args_str}"
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error running DeepCoder: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)