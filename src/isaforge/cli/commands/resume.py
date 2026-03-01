"""Resume command implementation."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from isaforge.agents.orchestrator import ISAForgeOrchestrator
from isaforge.cli.ui.console import print_error, print_info, print_success
from isaforge.cli.ui.progress import create_spinner
from isaforge.core.exceptions import SessionNotFoundError
from isaforge.observability.logger import setup_logging
from isaforge.session.database import init_database

console = Console()


async def run_resume(session_id: str) -> None:
    """Run the resume command.

    Args:
        session_id: Session ID to resume.
    """
    setup_logging()
    await init_database()

    # Initialize orchestrator
    orchestrator = ISAForgeOrchestrator()

    # Resume session
    try:
        with create_spinner(f"Resuming session {session_id}..."):
            await orchestrator.resume_session(session_id)
    except SessionNotFoundError:
        print_error(f"Session not found: {session_id}")
        return

    state = orchestrator.get_state()
    if state is None:
        print_error("Failed to load session state")
        return

    print_success(f"Session resumed: {session_id}")

    if state.bioproject_id:
        print_info(f"BioProject: {state.bioproject_id}")
    if state.local_metadata_paths:
        print_info(f"Local files: {', '.join(state.local_metadata_paths)}")
    print_info(f"Turn count: {state.turn_count}")
    print_info(f"Fields resolved: {len(state.fields_resolved)}")
    print_info(f"Fields pending: {len(state.fields_pending)}")

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
