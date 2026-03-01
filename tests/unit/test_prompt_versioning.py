"""Tests for prompt versioning."""

import pytest

from isaforge.agents.prompts.versioning import (
    PromptRegistry,
    PromptVersion,
    compute_hash,
    get_prompt_registry,
    register_prompt,
)


def test_compute_hash():
    """Test hash computation is consistent."""
    content = "This is a test prompt"
    hash1 = compute_hash(content)
    hash2 = compute_hash(content)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 produces 64 hex characters
    
    # Different content produces different hash
    different_hash = compute_hash("Different content")
    assert different_hash != hash1


def test_prompt_version_from_content():
    """Test creating PromptVersion from content."""
    name = "test_prompt"
    content = "You are a helpful assistant."
    
    version = PromptVersion.from_content(name, content)
    
    assert version.name == name
    assert version.content == content
    assert len(version.content_hash) == 64
    assert version.created_at is not None


def test_prompt_registry_register():
    """Test registering prompts."""
    registry = PromptRegistry()
    
    name = "system_prompt"
    content = "You are an ISA-Tab generator."
    
    version = registry.register(name, content)
    
    assert version.name == name
    assert version.content == content
    assert version.content_hash == compute_hash(content)


def test_prompt_registry_get():
    """Test retrieving registered prompts."""
    registry = PromptRegistry()
    
    name = "test_prompt"
    content = "Test content"
    registry.register(name, content)
    
    retrieved = registry.get(name)
    assert retrieved is not None
    assert retrieved.name == name
    assert retrieved.content == content
    
    # Non-existent prompt returns None
    assert registry.get("nonexistent") is None


def test_prompt_registry_get_hash():
    """Test getting hash for a registered prompt."""
    registry = PromptRegistry()
    
    name = "test_prompt"
    content = "Test content"
    expected_hash = compute_hash(content)
    
    registry.register(name, content)
    
    hash_result = registry.get_hash(name)
    assert hash_result == expected_hash
    
    # Non-existent prompt returns None
    assert registry.get_hash("nonexistent") is None


def test_prompt_registry_get_by_hash():
    """Test retrieving prompt by hash."""
    registry = PromptRegistry()
    
    name = "test_prompt"
    content = "Test content"
    version = registry.register(name, content)
    
    retrieved = registry.get_by_hash(version.content_hash)
    assert retrieved is not None
    assert retrieved.name == name
    assert retrieved.content == content
    
    # Non-existent hash returns None
    assert registry.get_by_hash("nonexistent_hash") is None


def test_prompt_registry_list_prompts():
    """Test listing all registered prompts."""
    registry = PromptRegistry()
    
    registry.register("prompt1", "Content 1")
    registry.register("prompt2", "Content 2")
    registry.register("prompt3", "Content 3")
    
    prompts = registry.list_prompts()
    
    assert len(prompts) == 3
    assert all("name" in p for p in prompts)
    assert all("hash" in p for p in prompts)
    assert all("created_at" in p for p in prompts)
    
    names = [p["name"] for p in prompts]
    assert "prompt1" in names
    assert "prompt2" in names
    assert "prompt3" in names


def test_prompt_registry_clear():
    """Test clearing the registry."""
    registry = PromptRegistry()
    
    registry.register("prompt1", "Content 1")
    registry.register("prompt2", "Content 2")
    
    assert len(registry.list_prompts()) == 2
    
    registry.clear()
    
    assert len(registry.list_prompts()) == 0
    assert registry.get("prompt1") is None


def test_prompt_registry_duplicate_registration():
    """Test registering the same prompt twice."""
    registry = PromptRegistry()
    
    name = "test_prompt"
    content = "Test content"
    
    version1 = registry.register(name, content)
    version2 = registry.register(name, content)
    
    # Should overwrite, both hashes should be the same
    assert version1.content_hash == version2.content_hash
    assert len(registry.list_prompts()) == 1


def test_prompt_registry_content_change_detection():
    """Test that changing content produces different hash."""
    registry = PromptRegistry()
    
    name = "test_prompt"
    content1 = "Original content"
    content2 = "Modified content"
    
    version1 = registry.register(name, content1)
    version2 = registry.register(name, content2)
    
    assert version1.content_hash != version2.content_hash


def test_global_registry():
    """Test global registry functions."""
    # Clear any existing state
    registry = get_prompt_registry()
    registry.clear()
    
    name = "global_test"
    content = "Global test content"
    
    version = register_prompt(name, content)
    
    assert version.name == name
    assert version.content == content
    
    # Verify it's in the global registry
    from isaforge.agents.prompts.versioning import get_prompt_hash
    
    hash_result = get_prompt_hash(name)
    assert hash_result == version.content_hash


def test_hash_consistency_across_instances():
    """Test that hash computation is consistent across different instances."""
    content = "Consistent content"
    
    registry1 = PromptRegistry()
    registry2 = PromptRegistry()
    
    version1 = registry1.register("test", content)
    version2 = registry2.register("test", content)
    
    assert version1.content_hash == version2.content_hash
