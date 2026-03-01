"""Sessions list command implementation."""

from rich.console import Console
from rich.table import Table

from isaforge.cli.ui.console import print_info
from isaforge.core.constants import SessionStatus
from isaforge.observability.logger import setup_logging
from isaforge.session.database import init_database
from isaforge.session.manager import session_manager

console = Console()


async def run_list_sessions(limit: int, status: str | None) -> None:
    """Run the list-sessions command.

    Args:
        limit: Maximum number of sessions to show.
        status: Optional status filter.
    """
    setup_logging()
    await init_database()

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = SessionStatus(status.lower())
        except ValueError:
            print_info(f"Invalid status: {status}. Valid options: active, completed, failed, abandoned")
            return

    # Fetch sessions
    sessions = await session_manager.list_sessions(status=status_filter, limit=limit)

    if not sessions:
        print_info("No sessions found.")
        return

    # Create table
    table = Table(title="ISA-Forge Sessions")
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("BioProject", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Turns", justify="right")
    table.add_column("Fields", justify="right")
    table.add_column("Created", style="dim")

    for session in sessions:
        bioproject = session.bioproject_id or "-"
        fields = f"{len(session.fields_resolved)}/{len(session.fields_resolved) + len(session.fields_pending)}"
        created = session.created_at.strftime("%Y-%m-%d %H:%M")

        # Color status
        status_style = {
            SessionStatus.ACTIVE: "yellow",
            SessionStatus.COMPLETED: "green",
            SessionStatus.FAILED: "red",
            SessionStatus.ABANDONED: "dim",
        }.get(session.status, "white")

        table.add_row(
            session.id[:8] + "...",
            bioproject,
            f"[{status_style}]{session.status.value}[/{status_style}]",
            str(session.turn_count),
            fields,
            created,
        )

    console.print(table)
    console.print(f"\nShowing {len(sessions)} session(s). Use 'isaforge resume <session_id>' to continue.")
