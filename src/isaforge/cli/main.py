"""Main CLI entry point for ISA-Forge."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from isaforge import __version__

app = typer.Typer(
    name="isaforge",
    help="ISA-Forge: Human-in-the-loop ISA-Tab generator using LLMs",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"ISA-Forge version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """ISA-Forge: Human-in-the-loop ISA-Tab generator using LLMs."""
    pass


@app.command()
def generate(
    bioproject: Optional[str] = typer.Option(
        None,
        "--bioproject",
        "-b",
        help="BioProject accession (e.g., PRJNA123456)",
    ),
    local_files: Optional[list[str]] = typer.Option(
        None,
        "--local",
        "-l",
        help="Local metadata files (CSV, JSON, TSV)",
    ),
    output: Path = typer.Option(
        Path("./isa_output"),
        "--output",
        "-o",
        help="Output directory for ISA-Tab files",
    ),
) -> None:
    """Generate ISA-Tab files from BioProject or local metadata."""
    from isaforge.cli.commands.generate import run_generate

    asyncio.run(run_generate(bioproject, local_files, output))


@app.command()
def resume(
    session_id: str = typer.Argument(..., help="Session ID to resume"),
) -> None:
    """Resume a previous generation session."""
    from isaforge.cli.commands.resume import run_resume

    asyncio.run(run_resume(session_id))


@app.command()
def validate(
    isa_dir: Path = typer.Argument(..., help="Directory containing ISA-Tab files"),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Use strict validation (fail on warnings)",
    ),
) -> None:
    """Validate ISA-Tab files."""
    from isaforge.cli.commands.validate import run_validate

    run_validate(isa_dir, strict)


@app.command("list-sessions")
def list_sessions(
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum sessions to show"),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (active, completed, failed)",
    ),
) -> None:
    """List previous generation sessions."""
    from isaforge.cli.commands.sessions import run_list_sessions

    asyncio.run(run_list_sessions(limit, status))


if __name__ == "__main__":
    app()
