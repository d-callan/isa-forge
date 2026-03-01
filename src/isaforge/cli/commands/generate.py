"""Generate command implementation."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from isaforge.agents.orchestrator import ISAForgeOrchestrator
from isaforge.cli.ui.console import print_error, print_info, print_success, print_warning
from isaforge.cli.ui.progress import create_spinner
from isaforge.observability.logger import setup_logging
from isaforge.session.database import init_database

console = Console()


async def run_generate(
    bioproject: str | None,
    local_files: list[str] | None,
    output: Path,
) -> None:
    """Run the generate command.

    Args:
        bioproject: Optional BioProject accession.
        local_files: Optional list of local metadata files.
        output: Output directory path.
    """
    setup_logging()
    await init_database()

    # Validate inputs
    if not bioproject and not local_files:
        print_error("Please provide either a BioProject ID (--bioproject) or local files (--local)")
        return

    # Show welcome message
    console.print(Panel.fit(
        "[bold blue]ISA-Forge[/bold blue] - ISA-Tab Generator\n"
        "Type 'quit' or 'exit' to end the session.",
        title="Welcome",
    ))

    # Initialize orchestrator
    orchestrator = ISAForgeOrchestrator()

    # Start session
    with create_spinner("Starting session..."):
        session_id = await orchestrator.start_session(
            bioproject_id=bioproject,
            local_metadata_paths=local_files,
            output_path=str(output),
        )

    print_success(f"Session started: {session_id}")

    if bioproject:
        print_info(f"BioProject: {bioproject}")
    if local_files:
        print_info(f"Local files: {', '.join(local_files)}")
    print_info(f"Output directory: {output}")

    console.print()

    # Main conversation loop
    user_message = None
    while True:
        # Process turn
        with create_spinner("Processing..."):
            response = await orchestrator.process_turn(user_message)

        # Display response
        console.print()
        console.print(Panel(response.message, title="ISA-Forge", border_style="blue"))

        # Show field decisions if any
        if response.field_decisions:
            console.print()
            console.print("[bold]Field Decisions:[/bold]")
            for decision in response.field_decisions:
                confidence_color = "green" if decision.confidence >= 0.9 else "yellow" if decision.confidence >= 0.5 else "red"
                console.print(
                    f"  • {decision.field_path}: [bold]{decision.value}[/bold] "
                    f"[{confidence_color}]({decision.confidence:.0%})[/{confidence_color}]"
                )

        # Check if complete
        if response.is_complete:
            print_success("Generation complete!")
            break

        # Show questions if any
        if response.questions:
            console.print()
            for q in response.questions:
                print_warning(f"❓ {q}")

        # Get user input if needed
        if response.needs_user_input or response.questions:
            console.print()
            user_message = Prompt.ask("[bold cyan]Your response[/bold cyan]")

            if user_message.lower() in ("quit", "exit", "q"):
                print_info("Ending session...")
                orchestrator.state.user_requested_exit = True
                await orchestrator.process_turn(None)
                break
        else:
            user_message = None

    # Show final summary
    summary = orchestrator.get_confidence_summary()
    if summary:
        console.print()
        console.print(Panel(
            f"[bold]Session Summary[/bold]\n\n"
            f"Total fields: {summary.total_fields}\n"
            f"Auto-accepted: {summary.auto_accepted}\n"
            f"User-confirmed: {summary.user_confirmed}\n"
            f"User-edited: {summary.user_edited}\n"
            f"Flagged: {summary.flagged}\n"
            f"Average confidence: {summary.average_confidence:.0%}",
            title="Summary",
            border_style="green",
        ))
