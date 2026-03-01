"""Progress indicators for CLI."""

from contextlib import contextmanager

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@contextmanager
def create_spinner(message: str):
    """Create a spinner context manager.

    Args:
        message: Message to display with spinner.

    Yields:
        Progress task ID.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(message, total=None)
        yield task


def create_progress_bar(total: int, description: str = "Processing"):
    """Create a progress bar.

    Args:
        total: Total number of items.
        description: Description text.

    Returns:
        Progress context manager.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )
