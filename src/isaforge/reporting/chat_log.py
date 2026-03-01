"""Chat log export for conversation history."""

from datetime import datetime
from pathlib import Path

from isaforge.core.constants import CHAT_LOG_FILE
from isaforge.models.session import Message
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


def generate_chat_log(
    session_id: str,
    messages: list[Message],
    output_dir: str | Path,
    metadata: dict | None = None,
) -> Path:
    """Generate chat_log.md file.

    Args:
        session_id: The session ID.
        messages: List of conversation messages.
        output_dir: Directory to write the file to.
        metadata: Optional metadata to include in header.

    Returns:
        Path to the generated file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / CHAT_LOG_FILE

    lines = []

    # Header
    lines.append("# ISA-Forge Chat Log")
    lines.append("")
    lines.append(f"**Session ID:** {session_id}")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z")

    if metadata:
        if metadata.get("bioproject_id"):
            lines.append(f"**BioProject:** {metadata['bioproject_id']}")
        if metadata.get("local_files"):
            lines.append(f"**Local Files:** {', '.join(metadata['local_files'])}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Messages
    for msg in messages:
        role_display = {
            "system": "System",
            "user": "User",
            "assistant": "ISA-Forge",
            "tool": "Tool",
        }.get(msg.role.value, msg.role.value.title())

        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        lines.append(f"### {role_display}")
        lines.append(f"*{timestamp}*")
        lines.append("")

        # Format content
        content = msg.content
        if msg.role.value == "tool":
            # Format tool responses as code blocks
            lines.append("```json")
            lines.append(content)
            lines.append("```")
        else:
            lines.append(content)

        lines.append("")

        # Add tool calls if present
        if msg.tool_calls:
            lines.append("**Tool Calls:**")
            for tc in msg.tool_calls:
                tool_name = tc.get("name", "unknown")
                lines.append(f"- `{tool_name}`")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Write file
    output_path.write_text("\n".join(lines), encoding="utf-8")

    logger.info(
        "chat_log_generated",
        path=str(output_path),
        message_count=len(messages),
    )

    return output_path


def format_message_for_display(message: Message) -> str:
    """Format a single message for display.

    Args:
        message: The message to format.

    Returns:
        Formatted message string.
    """
    role_display = {
        "system": "[System]",
        "user": "[You]",
        "assistant": "[ISA-Forge]",
        "tool": "[Tool]",
    }.get(message.role.value, f"[{message.role.value}]")

    return f"{role_display} {message.content}"
