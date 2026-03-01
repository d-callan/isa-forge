<img src="isa-forge-logo.png" alt="ISA-Forge Logo" width="60" align="left" style="margin-right: 15px;">

# ISA-Forge

**Human-in-the-loop ISA-Tab generator using LLMs**

<br clear="left"/>

ISA-Forge is a CLI tool that generates ISA-Tab metadata files from BioProject data, publications, and local metadata files. It uses Large Language Models (LLMs) to infer study design, map terms to ontologies, and resolve uncertainties through interactive conversation.

## Features

- **Multi-source metadata retrieval**: Fetch data from NCBI BioProject, PubMed, and local files (CSV, JSON, TSV)
- **LLM-powered inference**: Use Anthropic Claude, Google Gemini, or local Ollama models
- **Ontology mapping**: Automatic term mapping via OLS and Zooma with LLM assistance
- **Confidence scoring**: Every field includes confidence scores and justifications
- **Human-in-the-loop**: Interactive clarification for uncertain fields
- **Session persistence**: Resume interrupted sessions from SQLite database
- **ISA-Tab validation**: Validate output using isatools

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/isa-forge.git
cd isa-forge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Required settings:
- `ISAFORGE_LLM_PROVIDER`: Choose `anthropic`, `google`, or `ollama`
- `ISAFORGE_ANTHROPIC_API_KEY` or `ISAFORGE_GOOGLE_API_KEY`: API key for cloud providers

Optional but recommended:
- `ISAFORGE_NCBI_API_KEY`: For higher NCBI API rate limits
- `ISAFORGE_NCBI_EMAIL`: For NCBI API identification

## Usage

### Generate ISA-Tab from BioProject

```bash
isaforge generate --bioproject PRJNA123456 --output ./my_study
```

### Generate from local metadata files

```bash
isaforge generate --local samples.csv --local experiment.json --output ./my_study
```

### Resume a previous session

```bash
isaforge resume <session-id>
```

### List previous sessions

```bash
isaforge list-sessions
```

### Validate ISA-Tab files

```bash
isaforge validate ./my_study
```

## Output Files

ISA-Forge generates the following files in the output directory:

| File | Description |
|------|-------------|
| `i_investigation.txt` | Investigation metadata |
| `s_*.txt` | Study files with samples and factors |
| `a_*.txt` | Assay files with measurements |
| `confidence_summary.json` | Field-level confidence scores |
| `provenance.json` | Data source tracking |
| `data_dictionary.json` | Custom term definitions |
| `chat_log.md` | Conversation history |

## Architecture

```
src/isaforge/
├── agents/          # LLM orchestration and tools
├── cli/             # Command-line interface
├── core/            # Configuration, logging, exceptions
├── evaluation/      # Benchmarking framework
├── isa_builder/     # ISA-Tab file generation
├── models/          # Pydantic data models
├── observability/   # Logging, metrics, circuit breakers
├── ontology/        # OLS, Zooma, term mapping
├── reporting/       # Output report generation
├── retrieval/       # NCBI and local file parsers
└── session/         # SQLite session management
```

## Confidence Scoring

Every field populated by ISA-Forge includes:
- **Confidence score** (0.0-1.0)
- **Justification** explaining the score
- **Source** (API data, publication, user input, LLM inference)

Fields with confidence ≥ 0.9 are auto-accepted. Lower confidence fields require user confirmation.

## Ontology Mapping

ISA-Forge maps terms to standard ontologies in this order of preference:
1. **OBI** - Ontology for Biomedical Investigations
2. **EFO** - Experimental Factor Ontology
3. **NCIT** - NCI Thesaurus
4. **UBERON** - Uber-anatomy ontology
5. **CL** - Cell Ontology
6. **CHEBI** - Chemical Entities of Biological Interest

If no suitable term is found, a custom term is created and documented in `data_dictionary.json`.

## Development

### Running tests

```bash
pytest tests/
```

### Code formatting

```bash
ruff check src/
ruff format src/
```

### Type checking

```bash
mypy src/isaforge/
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development setup, code style, and PR process
- **[Testing Guide](docs/TESTING.md)** - Running tests locally and in CI, coverage reports
- **[Architecture](docs/ARCHITECTURE.md)** - System design, components, and LLM integration
- **[Pydantic AI Integration](docs/PYDANTIC_AI_INTEGRATION.md)** - Complete LLM integration implementation

See [docs/README.md](docs/README.md) for a complete overview.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.
