"""
Main CLI interface for DeepCoder.
"""
import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.logging import RichHandler

from config.settings import get_config, update_config_with_cli_args
from config.setup_wizard import check_first_run, run_setup_wizard
from models.factory import create_model
from core.agent import Agent
from utils.diff import colorize_diff
from core.git_utils import GitManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)

logger = logging.getLogger("deepcoder")
console = Console()
app = typer.Typer(help="DeepCoder - An agentic CLI for code modification")


@app.command()
def main(
    instruction: Optional[str] = typer.Argument(None, help="Natural language instruction for the coding task"),
    platform: Optional[str] = typer.Option(
        None, "--platform", "-p", help="Model platform: 'deepseek' or 'lightningai'"
    ),
    model_type: Optional[str] = typer.Option(
        None, "--model-type", help="DeepSeek model type: 'coder-v3', 'v3-base', or 'r1'"
    ),
    temperature: Optional[float] = typer.Option(
        None, "--temperature", "-t", help="Temperature for model generation (0.0-1.0)"
    ),
    max_tokens: Optional[int] = typer.Option(
        None, "--max-tokens", "-m", help="Maximum tokens to generate"
    ),
    log_level: str = typer.Option(
        "INFO", "--log-level", "-l", 
        help="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    ),
    project_root: Optional[Path] = typer.Option(
        None, "--root", "-r", help="Project root directory (defaults to current directory)"
    ),
    no_confirm: bool = typer.Option(
        False, "--no-confirm", help="Skip confirmation before applying changes"
    ),
    stage: bool = typer.Option(
        False, "--stage", help="Stage changes in Git after applying"
    ),
    commit: bool = typer.Option(
        False, "--commit", help="Commit changes after applying (implies --stage)"
    ),
    setup: bool = typer.Option(
        False, "--setup", help="Run the setup wizard"
    ),
):
    """
    DeepCoder - An agentic command line interface for code modification using DeepSeek models.
    
    Provide a natural language instruction for what you want to do, and DeepCoder will handle the rest.
    
    DeepCoder supports two deployment options:
    1. Direct usage via DeepSeek platform (deepseek.com)
    2. Self-hosted models on Lightning.ai
    """
    # Run setup wizard if explicitly requested or if this is the first run
    if setup or (instruction is None and check_first_run()):
        try:
            config = run_setup_wizard()
            if instruction is None:
                console.print("\n[green]Setup complete! You can now use DeepCoder with your configuration.[/green]")
                return
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Setup wizard cancelled. Using default configuration if available.[/yellow]")
            if instruction is None:
                return
        except Exception as e:
            console.print(f"\n[red]Error during setup: {str(e)}[/red]")
            console.print("[yellow]Using default configuration if available.[/yellow]")
            if instruction is None:
                return
    
    # If no instruction provided, show help
    if instruction is None:
        console.print("\n[yellow]Please provide an instruction for DeepCoder.[/yellow]")
        console.print("Example: deepcoder \"Refactor the login function in auth.py\"")
        console.print("\nFor more options, run: deepcoder --help")
        return
    
    # Set up project root
    if project_root is None:
        project_root = Path.cwd()
    
    # Set log level
    logger.setLevel(log_level)
    
    # Collect CLI args
    cli_args = {
        "platform": platform,
        "model_type": model_type,
        "model_params": {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    }
    
    try:
        # Run the async main function
        asyncio.run(
            async_main(
                instruction=instruction,
                cli_args=cli_args,
                project_root=project_root,
                no_confirm=no_confirm,
                stage=stage,
                commit=commit
            )
        )
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        logger.exception("Unhandled exception")
        sys.exit(1)


async def async_main(
    instruction: str,
    cli_args: Dict[str, Any],
    project_root: Path,
    no_confirm: bool,
    stage: bool,
    commit: bool
) -> None:
    """
    Async main function that handles the CLI workflow.
    
    Args:
        instruction: The natural language instruction
        cli_args: CLI arguments
        project_root: Project root directory
        no_confirm: Whether to skip confirmation
        stage: Whether to stage changes in Git
        commit: Whether to commit changes
    """
    # Show startup banner
    console.print(
        Panel.fit(
            "[bold blue]DeepCoder[/bold blue] - Agentic CLI for code modification",
            border_style="blue"
        )
    )
    
    # Load and update configuration
    console.print("Loading configuration...")
    config = get_config()
    config = update_config_with_cli_args(config, cli_args)
    
    # Update git settings from CLI args
    if "git" not in config:
        config["git"] = {}
    
    config["git"]["auto_stage"] = stage or commit
    config["git"]["auto_commit"] = commit
    
    # Check if project is a Git repository
    git_manager = GitManager(project_root)
    if git_manager.is_git_repo():
        console.print(f"Project at [bold]{project_root}[/bold] is a Git repository")
    else:
        if stage or commit:
            console.print("[yellow]Warning: Project is not a Git repository, ignoring --stage and --commit flags[/yellow]")
            config["git"]["auto_stage"] = False
            config["git"]["auto_commit"] = False
    
    # Initialize model
    console.print(f"Initializing model (platform: [bold]{config['model']['platform']}[/bold])...")
    try:
        model = create_model(config["model"])
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("\n[yellow]Please run the setup wizard to configure DeepCoder:[/yellow]")
        console.print("  deepcoder --setup")
        return
    
    # Initialize agent
    agent = Agent(model, config, project_root)
    
    # Process instruction
    with console.status(f"Processing instruction: [bold]{instruction}[/bold]..."):
        result = await agent.process_instruction(instruction)
    
    # Check for errors
    if error := result.get("error"):
        console.print(f"[bold red]Error:[/bold red] {error}")
        return
    
    # Handle results based on whether we have changes or explanation
    if result.get("changes"):
        await handle_code_changes(
            result["changes"], 
            no_confirm, 
            agent, 
            git_manager,
            config["git"]["auto_stage"],
            config["git"]["auto_commit"]
        )
    elif result.get("explanation"):
        handle_explanation(result["explanation"])
    else:
        console.print("[yellow]No changes or explanation generated[/yellow]")


async def handle_code_changes(
    changes: List[Dict[str, Any]],
    no_confirm: bool,
    agent,
    git_manager,
    auto_stage: bool,
    auto_commit: bool
) -> None:
    """
    Handle code changes.
    
    Args:
        changes: List of code changes
        no_confirm: Whether to skip confirmation
        agent: The agent instance
        git_manager: The git manager instance
        auto_stage: Whether to automatically stage changes
        auto_commit: Whether to automatically commit changes
    """
    # Show changes
    console.print(f"\n[bold green]Generated {len(changes)} file change(s):[/bold green]")
    
    for i, change in enumerate(changes):
        file_path = change["file_path"]
        is_new = change.get("is_new_file", False)
        
        console.print(f"\n[bold]{i+1}. {'New file' if is_new else 'Modified'}: {file_path}[/bold]")
        
        if diff := change.get("diff"):
            console.print(Syntax(diff, "diff", theme="monokai"))
    
    # Confirm changes
    if not no_confirm:
        confirmed = Confirm.ask("\nApply these changes?")
        if not confirmed:
            console.print("[yellow]Changes not applied[/yellow]")
            return
    
    # Apply changes
    console.print("\nApplying changes...")
    modified_files = []
    
    for change in changes:
        file_path = change["file_path"]
        new_content = change["new_content"]
        
        # Convert to absolute path if not already
        if not os.path.isabs(file_path):
            abs_path = os.path.join(agent.project_root, file_path)
        else:
            abs_path = file_path
        
        # Write the file
        try:
            await agent.file_manager.write_file(file_path, new_content)
            console.print(f"[green]✓[/green] Updated {file_path}")
            modified_files.append(file_path)
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to update {file_path}: {str(e)}")
    
    # Handle Git operations
    if git_manager.is_git_repo() and modified_files and auto_stage:
        console.print("\nStaging changes in Git...")
        
        for file_path in modified_files:
            try:
                git_manager.stage_file(file_path)
                console.print(f"[green]✓[/green] Staged {file_path}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to stage {file_path}: {str(e)}")
        
        if auto_commit:
            console.print("\nCommitting changes...")
            try:
                commit_hash = git_manager.commit_changes(f"DeepCoder: {changes[0]['file_path']}")
                console.print(f"[green]✓[/green] Committed changes: {commit_hash[:7]}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to commit changes: {str(e)}")


def handle_explanation(explanation: str) -> None:
    """
    Handle explanation.
    
    Args:
        explanation: The explanation to display
    """
    console.print("\n[bold green]Explanation:[/bold green]")
    console.print(Panel(explanation, border_style="green"))


if __name__ == "__main__":
    app()