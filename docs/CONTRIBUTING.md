# Contributing to ISA-Forge

Thank you for your interest in contributing to ISA-Forge!

## Development Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### Quick Start

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or use Makefile
make install-dev

# Or create Conda environment
make conda-env
conda activate isaforge
```

## Development Workflow

### Making Changes

1. **Write clear, documented code**
   - Follow existing code style
   - Add type hints
   - Include docstrings (Google style)

2. **Add tests for new functionality**
   - Unit tests in `tests/unit/`
   - Aim for 70%+ coverage on new code

3. **Run tests and checks before committing**
   ```bash
   # Using Makefile (recommended)
   make test          # Run all tests
   make test-cov      # Run with coverage
   make lint          # Check code style
   make format        # Auto-format code
   make type-check    # Run mypy
   
   # Or run directly
   pytest tests/ -v
   ruff check src/ tests/
   ruff format src/ tests/
   mypy src/isaforge/ --ignore-missing-imports
   ```

### Commit Messages

Use conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

Example: `feat: add ontology mapping confidence threshold`

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting

### Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update README.md if adding user-facing features

### Example Docstring
```python
def map_term(self, source_text: str, context: str | None = None) -> OntologyMapping:
    """Map a source text to an ontology term.
    
    Args:
        source_text: The text to map to an ontology term.
        context: Optional context to improve mapping accuracy.
        
    Returns:
        OntologyMapping with the best match and confidence score.
        
    Raises:
        OntologyMappingError: If mapping fails.
    """
```

## Testing Guidelines

### Writing Tests

1. **Unit tests** - Test individual components in isolation
   - Use mocks for external dependencies
   - Fast execution (< 1 second per test)
   - Located in `tests/unit/`

2. **Integration tests** - Test real API interactions
   - Mark with `@pytest.mark.integration`
   - Used to validate mocks
   - Located in `tests/integration/`

### Test Coverage
- Aim for 70%+ coverage on new code
- All new features must include tests
- Bug fixes should include regression tests

### Example Test
```python
import pytest
from isaforge.models.isa import Investigation

def test_investigation_creation():
    """Test creating an Investigation model."""
    inv = Investigation(
        identifier="INV001",
        title="Test Investigation",
    )
    assert inv.identifier == "INV001"
    assert inv.title == "Test Investigation"

@pytest.mark.asyncio
async def test_async_retrieval():
    """Test async NCBI retrieval."""
    # Test implementation
    pass
```

## Pull Request Checklist

Before submitting a PR:
- [ ] All tests pass: `make test`
- [ ] Code is formatted: `make format`
- [ ] No linting errors: `make lint`
- [ ] Type checking passes: `make type-check`
- [ ] Tests added for new features
- [ ] Documentation updated if needed

CI will automatically run all checks on your PR. All checks must pass before merge.

## Project Structure

```
isa-forge/
├── src/isaforge/          # Main package
│   ├── agents/           # LLM orchestration
│   ├── cli/              # Command-line interface
│   ├── core/             # Core utilities
│   ├── isa_builder/      # ISA-Tab generation
│   ├── models/           # Pydantic models
│   ├── observability/    # Logging, metrics
│   ├── ontology/         # Ontology mapping
│   ├── reporting/        # Report generation
│   ├── retrieval/        # Data retrieval
│   └── session/          # Session management
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── conftest.py      # Shared fixtures
└── docs/                # Documentation
```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue with reproduction steps
- **Features**: Open a GitHub Issue with use case description

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
