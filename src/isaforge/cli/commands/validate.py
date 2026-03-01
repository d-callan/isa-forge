"""Validate command implementation."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from isaforge.cli.ui.console import print_error, print_info, print_success, print_warning
from isaforge.isa_builder.validator import ISATabValidator

console = Console()


def run_validate(isa_dir: Path, strict: bool) -> None:
    """Run the validate command.

    Args:
        isa_dir: Directory containing ISA-Tab files.
        strict: Whether to use strict validation.
    """
    if not isa_dir.exists():
        print_error(f"Directory not found: {isa_dir}")
        return

    print_info(f"Validating ISA-Tab files in: {isa_dir}")

    validator = ISATabValidator(strict=strict)

    try:
        results = validator.validate(isa_dir)

        # Display results
        console.print()

        if results["valid"]:
            print_success("Validation passed!")
        else:
            print_error("Validation failed!")

        # Show info
        if results["info"]:
            console.print()
            console.print("[bold]Information:[/bold]")
            for info in results["info"]:
                console.print(f"  ℹ️  {info}")

        # Show warnings
        if results["warnings"]:
            console.print()
            console.print("[bold yellow]Warnings:[/bold yellow]")
            for warning in results["warnings"]:
                print_warning(f"  ⚠️  {warning}")

        # Show errors
        if results["errors"]:
            console.print()
            console.print("[bold red]Errors:[/bold red]")
            for error in results["errors"]:
                print_error(f"  ❌ {error}")

    except Exception as e:
        print_error(f"Validation error: {e}")
