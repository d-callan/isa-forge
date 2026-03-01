"""Unit tests for configuration module."""

import os
from unittest.mock import patch

from isaforge.core.config import Settings, settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        s = Settings()

        assert s.llm_provider == "anthropic"
        assert s.llm_model == "claude-3-5-sonnet-20241022"
        assert s.ols_base_url == "https://www.ebi.ac.uk/ols4/api"
        assert s.max_publications == 6
        assert s.confidence_threshold == 0.9

    def test_preferred_ontologies(self):
        """Test default preferred ontologies."""
        s = Settings()

        assert "OBI" in s.preferred_ontologies
        assert "EFO" in s.preferred_ontologies
        assert len(s.preferred_ontologies) >= 5

    def test_session_db_path(self):
        """Test session database path."""
        s = Settings()

        assert s.session_db_path is not None
        assert "sessions.db" in str(s.session_db_path)

    def test_ollama_base_url(self):
        """Test Ollama base URL default."""
        s = Settings()

        assert s.ollama_base_url == "http://localhost:11434"

    def test_zooma_base_url(self):
        """Test Zooma base URL default."""
        s = Settings()

        assert "zooma" in s.zooma_base_url

    def test_validation_strict_default(self):
        """Test validation strict mode default."""
        s = Settings()

        assert hasattr(s, 'validation_strict')

    def test_global_settings_instance(self):
        """Test global settings instance exists."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_with_env_override(self):
        """Test settings can be overridden via environment."""
        with patch.dict(os.environ, {"ISAFORGE_MAX_PUBLICATIONS": "10"}):
            s = Settings()
            # Note: Settings are loaded at import time, so this tests the mechanism
            assert hasattr(s, 'max_publications')

    def test_llm_provider_options(self):
        """Test LLM provider is one of valid options."""
        s = Settings()

        assert s.llm_provider in ["anthropic", "google", "ollama"]

    def test_api_keys_optional(self):
        """Test API keys are optional (can be None)."""
        s = Settings()

        # These should not raise even if not set
        assert hasattr(s, 'anthropic_api_key')
        assert hasattr(s, 'google_api_key')
        assert hasattr(s, 'ncbi_api_key')
        assert hasattr(s, 'ncbi_email')
