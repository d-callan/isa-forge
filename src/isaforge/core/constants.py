"""Global constants and enums for ISA-Forge."""

from enum import Enum


class FieldSource(str, Enum):
    """Source of a field value."""

    API_DATA = "api_data"
    LLM_INFERENCE = "llm_inference"
    USER_INPUT = "user_input"
    LOCAL_FILE = "local_file"
    PUBLICATION = "publication"


class UserAction(str, Enum):
    """User action on a field."""

    AUTO_ACCEPTED = "auto_accepted"
    USER_CONFIRMED = "user_confirmed"
    USER_EDITED = "user_edited"
    FLAGGED = "flagged"
    PENDING = "pending"


class SessionStatus(str, Enum):
    """Status of a generation session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class TerminationReason(str, Enum):
    """Reason for session termination."""

    SUCCESS = "success"
    USER_EXIT = "user_exit"
    MAX_TURNS_EXCEEDED = "max_turns_exceeded"
    STUCK = "stuck_needs_manual_intervention"
    ERROR = "error"


class MessageRole(str, Enum):
    """Role in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# NCBI API endpoints
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_ESEARCH = f"{NCBI_BASE_URL}/esearch.fcgi"
NCBI_EFETCH = f"{NCBI_BASE_URL}/efetch.fcgi"
NCBI_ELINK = f"{NCBI_BASE_URL}/elink.fcgi"
NCBI_ESUMMARY = f"{NCBI_BASE_URL}/esummary.fcgi"

# PMC API for full-text
PMC_OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"

# Default ontologies
DEFAULT_ONTOLOGIES = [
    "OBI",  # Ontology for Biomedical Investigations
    "EFO",  # Experimental Factor Ontology
    "NCIT",  # NCI Thesaurus
    "UBERON",  # Uber-anatomy ontology
    "CL",  # Cell Ontology
    "CHEBI",  # Chemical Entities of Biological Interest
]

# ISA-Tab file names
ISA_INVESTIGATION_FILE = "i_investigation.txt"
ISA_STUDY_FILE_PREFIX = "s_"
ISA_ASSAY_FILE_PREFIX = "a_"

# Output file names
CONFIDENCE_SUMMARY_FILE = "confidence_summary.json"
DATA_DICTIONARY_FILE = "data_dictionary.json"
PROVENANCE_FILE = "provenance.json"
CHAT_LOG_FILE = "chat_log.md"
METHODS_FILE = "methods.md"
ONTOLOGIES_USED_FILE = "ontologies_used.json"

# Custom term prefix for unmapped ontology terms
CUSTOM_TERM_PREFIX = "ISAFORGE"
