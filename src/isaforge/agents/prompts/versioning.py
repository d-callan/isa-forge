"""Prompt versioning with hash-based tracking."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PromptVersion:
    """A versioned prompt with its content hash."""

    name: str
    content: str
    content_hash: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_content(cls, name: str, content: str) -> "PromptVersion":
        """Create a PromptVersion from content, computing the hash.

        Args:
            name: Name/identifier for the prompt.
            content: The prompt content.

        Returns:
            PromptVersion with computed hash.
        """
        content_hash = compute_hash(content)
        return cls(name=name, content=content, content_hash=content_hash)


def compute_hash(content: str) -> str:
    """Compute SHA256 hash of content.

    Args:
        content: String content to hash.

    Returns:
        Hex-encoded SHA256 hash (64 characters).
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class PromptRegistry:
    """Registry for tracking prompt versions.

    Prompts are stored in code files; this registry tracks which versions
    have been used and provides hash-based versioning for reproducibility.
    """

    def __init__(self):
        """Initialize the registry."""
        self._prompts: dict[str, PromptVersion] = {}
        self._hash_to_name: dict[str, str] = {}

    def register(self, name: str, content: str) -> PromptVersion:
        """Register a prompt and compute its hash (synchronous, no DB persistence).

        Args:
            name: Unique name for the prompt.
            content: The prompt content.

        Returns:
            PromptVersion with computed hash.
        """
        version = PromptVersion.from_content(name, content)
        self._prompts[name] = version
        self._hash_to_name[version.content_hash] = name

        logger.debug(
            "prompt_registered",
            name=name,
            hash=version.content_hash[:12],
        )

        return version

    async def register_async(self, name: str, content: str) -> PromptVersion:
        """Register a prompt and persist to database.

        Args:
            name: Unique name for the prompt.
            content: The prompt content.

        Returns:
            PromptVersion with computed hash.
        """
        version = self.register(name, content)
        
        # Persist to database
        await self._persist_to_db(version)
        
        return version

    async def _persist_to_db(self, version: PromptVersion) -> None:
        """Persist a prompt version to the database.

        Args:
            version: The PromptVersion to persist.
        """
        from isaforge.session.manager import session_manager
        
        try:
            await session_manager.save_prompt_version(
                name=version.name,
                content_hash=version.content_hash,
            )
            logger.debug(
                "prompt_persisted",
                name=version.name,
                hash=version.content_hash[:12],
            )
        except Exception as e:
            logger.warning(
                "prompt_persist_failed",
                name=version.name,
                error=str(e),
            )

    def get(self, name: str) -> PromptVersion | None:
        """Get a registered prompt by name.

        Args:
            name: The prompt name.

        Returns:
            PromptVersion or None if not found.
        """
        return self._prompts.get(name)

    def get_hash(self, name: str) -> str | None:
        """Get the hash for a registered prompt.

        Args:
            name: The prompt name.

        Returns:
            Content hash or None if not found.
        """
        version = self._prompts.get(name)
        return version.content_hash if version else None

    def get_by_hash(self, content_hash: str) -> PromptVersion | None:
        """Get a prompt by its content hash.

        Args:
            content_hash: The SHA256 hash.

        Returns:
            PromptVersion or None if not found.
        """
        name = self._hash_to_name.get(content_hash)
        return self._prompts.get(name) if name else None

    def list_prompts(self) -> list[dict[str, Any]]:
        """List all registered prompts.

        Returns:
            List of prompt info dictionaries.
        """
        return [
            {
                "name": v.name,
                "hash": v.content_hash,
                "created_at": v.created_at.isoformat(),
            }
            for v in self._prompts.values()
        ]

    def clear(self) -> None:
        """Clear all registered prompts."""
        self._prompts.clear()
        self._hash_to_name.clear()


# Global registry instance
_registry: PromptRegistry | None = None


def get_prompt_registry() -> PromptRegistry:
    """Get the global prompt registry, creating if needed.

    Returns:
        The global PromptRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def register_prompt(name: str, content: str) -> PromptVersion:
    """Register a prompt in the global registry.

    Args:
        name: Unique name for the prompt.
        content: The prompt content.

    Returns:
        PromptVersion with computed hash.
    """
    return get_prompt_registry().register(name, content)


def get_prompt_hash(name: str) -> str | None:
    """Get the hash for a registered prompt.

    Args:
        name: The prompt name.

    Returns:
        Content hash or None if not found.
    """
    return get_prompt_registry().get_hash(name)
