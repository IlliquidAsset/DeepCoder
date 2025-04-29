# DeepCoder CLI

An agentic Command Line Interface (CLI) tool that enables code modification using the DeepSeek Coder v3 model. This tool operates directly within your local file system project context via the CLI, providing a faithful clone of Claude Code functionality but powered by DeepSeek models.

## Features

- **Familiar Interface**: Identical command structure and user experience to Claude Code 
- **DeepSeek Powered**: Connect to DeepSeek Coder v3 models via DeepSeek platform or Lightning AI
- **Interactive Mode**: Enter interactive shell mode simply by typing `deepcoder`
- **Natural Language Processing**: Parse instructions and identify intentions
- **Agentic Workflow**: Plan and execute coding tasks
- **File System Interaction**: Locate, read, modify files based on instructions
- **Change Management**: Preview changes, confirm, and optionally commit to Git
- **Extensive Error Handling**: Comprehensive error handling for all stages

## Installation

### Easy Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/IlliquidAsset/deepcoder.git
cd deepcoder

# Run the installation script 
python install.py

# Now you can run DeepCoder with the 'deepcoder' command
deepcoder

# Or with specific instructions
deepcoder "Your instruction here"
```

### Alternative Methods

If the easy installation doesn't work, you can try these alternatives:

```bash
# Using the runner scripts directly
python run_deepcoder.py "Your instruction here"

# Or if you face any issues with the above, try the simpler script:
python run_simple.py "Your instruction here"
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/IlliquidAsset/deepcoder.git
cd deepcoder

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# For development (includes testing dependencies)
pip install -e ".[dev]"
```

### Troubleshooting

If you encounter installation issues:

1. Make sure all dependencies are installed: `pip install -r requirements.txt`
2. Try using the standalone runner: `python run_deepcoder.py`
3. If the module imports are still failing, try installing the dependencies individually:
   ```bash
   pip install typer rich pyyaml python-dotenv openai requests gitpython aiohttp
   ```

## Configuration

When you run DeepCoder for the first time (or with no arguments), it will automatically launch a setup wizard that guides you through the configuration process.

```bash
# Run the setup wizard explicitly
deepcoder --setup

# If you encounter issues with the interactive setup wizard,
# you can use the non-interactive setup command
deepcoder-setup

# For completely automated setup with default values
deepcoder-setup --defaults
```

DeepCoder supports configuration via:

1. Configuration file: `~/.config/deepcoder/config.yaml` (user-level) or `.deepcoder.yaml` (project-level)
2. Environment variables
3. CLI flags

### Configuration File Example

```yaml
# ~/.config/deepcoder/config.yaml
model:
  platform: "deepseek"  # or "lightningai"
  model_type: "coder-v3"  # or "v3-base", "r1"
  deepseek_api_key: "your_deepseek_api_key"
  use_lightning: false
  lightning_endpoint_url: "your_lightning_endpoint_url"  # only if use_lightning is true
  lightning_api_key: "your_lightning_api_key"  # only if use_lightning is true
  parameters:
    temperature: 0.2
    max_tokens: 2000
    top_p: 0.95
    frequency_penalty: 0.0
    presence_penalty: 0.0
```

### Environment Variables

```bash
export MODEL_HOST_PLATFORM=deepseek
export DEEPSEEK_API_KEY=your_deepseek_api_key
export DEEPSEEK_MODEL_TYPE=coder-v3
export DEEPSEEK_USE_LIGHTNING=false

# For Lightning AI hosting
export LIGHTNING_ENDPOINT_URL=your_lightning_endpoint_url
export LIGHTNING_API_KEY=your_lightning_api_key
```

## Usage

```bash
# Interactive mode (default)
deepcoder

# Run setup wizard explicitly
deepcoder --setup

# Basic usage with a single command
deepcoder "Refactor the login function in auth.py to use async await"

# Specify model platform
deepcoder --platform deepseek "Add error handling to the database connection in db.py"

# Specify model type
deepcoder --model-type coder-v3 "Create unit tests for the authentication module"

# Adjust model parameters
deepcoder --temperature 0.5 "Document the user authentication module"

# Git integration
deepcoder --stage "Fix the bug in the login function"
deepcoder --commit "Add validation to the user input"

# Interactive mode with specific options
deepcoder -i --temperature 0.7
```

### Interactive Mode Commands

When in interactive mode, you can:

- Type natural language instructions to perform coding tasks
- Use `exit` or `quit` to exit the interactive session
- Press Ctrl+C to cancel the current operation

## Development

### Running Tests

```bash
# Run all tests with coverage
python run_tests.py

# Or using pytest directly
pytest -xvs deepcoder/tests/ --cov=deepcoder

# Run specific tests
pytest -xvs deepcoder/tests/unit/models/
```

### Code Style

The codebase follows PEP 8 style guidelines. You can format the code using:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black deepcoder/
isort deepcoder/

# Check style
flake8 deepcoder/
```

## Security Considerations

- Always review proposed code modifications before confirming
- DeepCoder will never execute code fetched from the LLM
- Consider the risks of automated code modification

## License

MIT