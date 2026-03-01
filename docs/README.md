# ISA-Forge Documentation

Developer documentation for ISA-Forge architecture, testing, and LLM integration.

## Documentation

- **[Contributing Guide](CONTRIBUTING.md)** - Development setup and contribution guidelines
- **[Testing Guide](TESTING.md)** - Running tests, coverage, and CI/CD workflows
- **[Architecture](ARCHITECTURE.md)** - System design, components, and data flow
- **[Pydantic AI Integration](PYDANTIC_AI_INTEGRATION.md)** - Complete LLM integration implementation

## Quick Start

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Code quality checks
ruff check src/ tests/
ruff format src/ tests/
```

