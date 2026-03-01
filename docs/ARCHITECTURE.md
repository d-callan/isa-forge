# ISA-Forge Architecture

This document describes the high-level architecture and design decisions for ISA-Forge.

## Overview

ISA-Forge is a human-in-the-loop ISA-Tab generator that uses Large Language Models (LLMs) to intelligently map biological metadata to the ISA-Tab standard. The system retrieves metadata from multiple sources, uses LLMs for inference and ontology mapping, and maintains conversation state for interactive clarification.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (commands: generate, resume, list-sessions, validate)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
│  • Manages conversation flow                                │
│  • Coordinates retrieval, inference, and building            │
│  • Handles user interaction and clarification                │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Retrieval   │    │   LLM Provider   │    │ ISA Builder  │
│              │    │                  │    │              │
│ • NCBI       │    │ • Anthropic      │    │ • Formatter  │
│ • PubMed     │    │ • Google         │    │ • Validator  │
│ • Local CSV  │    │ • Ollama         │    │ • Writer     │
└──────────────┘    └──────────────────┘    └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────────────────────────────────────────────┐
│                   Supporting Services                     │
│                                                           │
│  Ontology Mapping    Session Management    Observability │
│  • OLS               • SQLite DB           • Metrics     │
│  • Zooma             • State tracking      • Logging     │
│  • Custom terms      • Persistence         • Circuit     │
│                                              breakers    │
└──────────────────────────────────────────────────────────┘
```

## Core Components

### 1. CLI Layer (`cli/`)
- **Purpose**: User interface for all ISA-Forge operations
- **Commands**:
  - `generate` - Start new ISA-Tab generation
  - `resume` - Continue interrupted session
  - `list-sessions` - View session history
  - `validate` - Validate ISA-Tab files
- **Technology**: Click framework with Rich for UI

### 2. Agent Orchestrator (`agents/`)
- **Purpose**: Coordinates the entire generation workflow
- **Responsibilities**:
  - Manage conversation turns with LLM
  - Execute tool calls (retrieval, ontology mapping)
  - Track field resolution state
  - Handle user clarifications
  - Decide when generation is complete
- **Key Files**:
  - `orchestrator.py` - Main orchestration logic
  - `state.py` - Conversation state management
  - `tools/` - Tool definitions for LLM

### 3. Retrieval Layer (`retrieval/`)
- **Purpose**: Fetch metadata from various sources
- **Components**:
  - `ncbi/` - BioProject and PubMed retrieval
  - `local/` - CSV, JSON, TSV parsers
  - `publications/` - Full-text extraction
- **Features**:
  - Async API calls with rate limiting
  - Caching and retry logic
  - Structured metadata extraction

### 4. Ontology Services (`ontology/`)
- **Purpose**: Map free-text terms to ontology terms
- **Services**:
  - **OLS** - Ontology Lookup Service (primary)
  - **Zooma** - Automated annotation service
  - **Custom Terms** - User-defined term dictionary
- **Features**:
  - Multi-service fallback
  - Confidence scoring
  - Context-aware mapping
  - LLM-assisted disambiguation

### 5. ISA Builder (`isa_builder/`)
- **Purpose**: Generate ISA-Tab files from Pydantic models
- **Components**:
  - `formatter.py` - Tab-delimited formatting
  - `investigation.py` - Investigation file builder
  - `study.py` - Study file builder
  - `assay.py` - Assay file builder
  - `validator.py` - ISA-Tab validation
- **Output**: Compliant ISA-Tab directory structure

### 6. Session Management (`session/`)
- **Purpose**: Persist conversation state for resumability
- **Storage**: SQLite database
- **Tracked Data**:
  - Conversation messages
  - LLM calls and responses
  - Field resolution status
  - Retry counts and errors
- **Benefits**: Resume after crashes, audit trail

### 7. Observability (`observability/`)
- **Purpose**: Monitor system health and performance
- **Components**:
  - **Circuit Breaker** - Prevent cascading failures
  - **Metrics** - Track LLM calls, tokens, latency
  - **Logger** - Structured logging with context

## Data Flow

### Typical Generation Flow

1. **User initiates generation**
   ```
   isaforge generate --bioproject PRJNA123456
   ```

2. **Orchestrator retrieves metadata**
   - Fetch BioProject metadata from NCBI
   - Retrieve linked publications from PubMed
   - Parse any local metadata files

3. **LLM analyzes metadata**
   - Infer study design and experimental details
   - Identify required ISA-Tab fields
   - Map terms to ontologies

4. **Interactive clarification**
   - Present low-confidence fields to user
   - Accept user input or edits
   - Update confidence scores

5. **Build ISA-Tab files**
   - Convert Pydantic models to ISA-Tab format
   - Validate against ISA-Tab specification
   - Write to output directory

6. **Generate reports**
   - Confidence summary (JSON)
   - Provenance record (JSON)
   - Data dictionary (JSON)
   - Chat log (Markdown)

## Design Decisions

### Why LLMs?

Traditional metadata mapping relies on exact string matching or simple heuristics. LLMs enable:
- **Contextual understanding** - Interpret abbreviations, synonyms, and domain-specific language
- **Inference** - Fill gaps in metadata using domain knowledge
- **Flexibility** - Adapt to diverse data sources and formats
- **Natural interaction** - Clarify uncertainties through conversation

### Why Human-in-the-Loop?

While LLMs are powerful, they can hallucinate or misinterpret. Human oversight ensures:
- **Accuracy** - Expert validation of critical fields
- **Trust** - Transparent confidence scores and justifications
- **Control** - User can override or edit any field

### Why Session Persistence?

ISA-Tab generation can take 10-30 minutes for complex projects. Persistence provides:
- **Resumability** - Continue after interruptions
- **Audit trail** - Track all decisions and changes
- **Debugging** - Inspect conversation history
- **Cost savings** - Avoid re-running expensive LLM calls

### Why Multiple Ontology Services?

No single ontology service covers all biomedical terms. Multi-service approach provides:
- **Coverage** - Fallback to alternative services
- **Validation** - Cross-check mappings across services
- **Flexibility** - Support custom terms when needed

## LLM Provider Support

### Supported Providers

1. **Anthropic Claude** (Recommended)
   - Best reasoning and instruction following
   - Supports tool use (function calling)
   - 200K token context window

2. **Google Gemini**
   - Good performance, lower cost
   - Supports tool use
   - 1M+ token context window

3. **Ollama** (Local)
   - Privacy-preserving
   - No API costs
   - Requires local GPU

### Provider Selection

Configure via environment variable:
```bash
ISAFORGE_LLM_PROVIDER=anthropic  # or google, ollama
```

### Tool Use (Function Calling)

ISA-Forge uses LLM tool calling for:
- `fetch_bioproject_metadata` - Retrieve NCBI data
- `fetch_publication_metadata` - Retrieve PubMed data
- `map_ontology_term` - Map to ontology
- `get_user_clarification` - Request user input

## Configuration

### Environment Variables

All configuration via `.env` file:
- **LLM Settings**: Provider, model, API keys
- **NCBI Settings**: API key, email
- **Ontology Settings**: Preferred ontologies, base URLs
- **Behavior**: Confidence thresholds, max turns
- **Validation**: Strict mode, custom rules

### Defaults

Sensible defaults for all settings:
- Confidence threshold: 0.9
- Max conversation turns: 50
- Preferred ontologies: OBI, EFO, NCIT, UBERON, CL, CHEBI

## Testing Strategy

### Unit Tests
- Mock external dependencies (APIs, LLMs)
- Fast execution (< 10 seconds total)
- 52% coverage (target: 70%+)

### Integration Tests
- Real API calls to validate mocks
- Marked with `@pytest.mark.integration`
- Used to capture actual responses

### CI/CD
- GitHub Actions on all PRs
- No secrets required
- Artifacts: Coverage reports, test results

See [TESTING.md](TESTING.md) for details.

## Future Enhancements

### Planned Features
- **Batch processing** - Generate ISA-Tab for multiple BioProjects
- **Template support** - Reuse study designs across projects
- **Validation rules** - Custom validation beyond ISA-Tab spec
- **Export formats** - Support additional metadata standards

### Performance Optimizations
- **Caching** - Cache ontology lookups and LLM responses
- **Parallel retrieval** - Fetch metadata sources concurrently
- **Streaming** - Stream LLM responses for better UX

### AI Improvements
- **Fine-tuning** - Train on ISA-Tab examples
- **RAG** - Retrieve similar projects for context
- **Active learning** - Learn from user corrections
