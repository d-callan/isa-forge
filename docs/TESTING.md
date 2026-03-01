# Testing Guide

## Overview

ISA-Forge uses pytest for testing with a focus on unit tests with mocked dependencies and integration tests for validating real API interactions.

**Coverage Goal**: 70%+ overall coverage

To check current coverage:
```bash
make test-cov
```

## Running Tests

### Quick Start

```bash
# Using Makefile (recommended)
make test              # Run all tests
make test-cov          # Run with coverage report
make test-html         # Generate HTML coverage report

# Or run pytest directly
pytest tests/ -v
pytest tests/ --cov=src/isaforge --cov-report=html
```

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or use Conda
conda env create -f environment.yml
conda activate isaforge
```

## CI/CD Workflows

### GitHub Actions - No Secrets Required

Two workflows run automatically on pushes and pull requests:

1. **tests.yml** - Standard Python testing
   - **OS**: Ubuntu, macOS, Windows
   - **Python**: 3.10, 3.11, 3.12
   - **Includes**: pytest, coverage, linting, type checking
   - **Artifacts**: HTML coverage reports, test results (JUnit XML)

2. **conda-tests.yml** - Conda environment testing
   - **OS**: Ubuntu, macOS
   - **Python**: 3.10, 3.11, 3.12
   - **Artifacts**: HTML coverage reports, test results

### Viewing CI Results in GitHub

#### Test Results Summary (GitHub UI)
1. Go to **Actions** tab in your repository
2. Click on the workflow run
3. View **Test Results** check at the bottom
4. See pass/fail counts, individual failures, execution times

#### Downloadable Artifacts (30-day retention)
- **coverage-report**: Interactive HTML coverage report
  - Download from Artifacts section
  - Unzip and open `index.html` in browser
  - Browse line-by-line coverage with color coding
- **test-results-{os}-py{version}**: JUnit XML test results
  - Compatible with any JUnit viewer

#### Coverage in Logs
- Coverage percentage printed in workflow logs
- Expand "Run tests with coverage" step
- Look for coverage summary table

### Code Quality Checks

```bash
make lint          # Check code style
make format        # Auto-format code
make type-check    # Run type checking
```

## Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Fast, isolated unit tests
└── integration/          # Real API integration tests
```

## Writing Tests

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
async def test_async_function():
    """Test async functionality."""
    result = await some_async_function()
    assert result is not None
```

### Using Fixtures

```python
def test_with_temp_dir(temp_dir):
    """Use temp_dir fixture from conftest.py."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
```

## Test Types

### Unit Tests
- Fast, isolated tests with mocked dependencies
- Run on every commit in CI
- Located in `tests/unit/`

### Integration Tests
- Real API calls to NCBI, OLS, Zooma
- Marked with `@pytest.mark.integration`
- Used to validate mocks and capture real responses
- Run manually or in separate CI workflow

```bash
# Run only unit tests (fast)
pytest tests/unit/ -v

# Run only integration tests (slow, requires network)
pytest tests/integration/ -v -m integration

# Skip integration tests
pytest tests/ -v -m "not integration"
```

## Understanding Coverage Reports

### HTML Coverage Report
- **index.html**: Overall coverage summary
- **Click any file**: Line-by-line coverage view
- **Green lines**: Covered by tests
- **Red lines**: Not covered
- **Yellow lines**: Partially covered (branches)

### Coverage Metrics
- **Statements**: Total lines of code
- **Missing**: Lines not executed by tests
- **Coverage %**: Percentage of lines covered

### Coverage Target
- **Goal**: 70%+ overall coverage
- Run `make test-cov` to see current coverage

## Troubleshooting

### Tests Fail Locally But Pass in CI
- Check Python version matches CI (3.10, 3.11, or 3.12)
- Ensure all dev dependencies installed: `pip install -e ".[dev]"`
- Clear pytest cache: `pytest --cache-clear`

### Coverage Report Missing Files
- Ensure `--cov=src/isaforge` flag is present
- Check that source code is in correct location
- Verify pytest is finding all test files

### Integration Tests Timeout
- NCBI API may rate limit without API key
- Set `ISAFORGE_NCBI_API_KEY` in `.env`
- Use `@pytest.mark.slow` to skip in quick runs
