"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_bioproject_metadata():
    """Sample BioProject metadata for testing."""
    return {
        "accession": "PRJNA123456",
        "title": "Test BioProject",
        "description": "A test BioProject for unit testing",
        "organism": "Homo sapiens",
        "taxon_id": 9606,
        "submission_date": "2024-01-01",
        "linked_pubmed_ids": ["12345678", "87654321"],
        "experiments": [
            {
                "accession": "SRX123456",
                "title": "Test Experiment",
                "library_strategy": "RNA-Seq",
                "library_source": "TRANSCRIPTOMIC",
                "platform": "ILLUMINA",
            }
        ],
        "samples": [
            {
                "accession": "SRS123456",
                "title": "Test Sample 1",
                "organism": "Homo sapiens",
                "attributes": {
                    "tissue": "liver",
                    "cell_type": "hepatocyte",
                },
            }
        ],
    }


@pytest.fixture
def sample_publication_metadata():
    """Sample publication metadata for testing."""
    return {
        "pmid": "12345678",
        "title": "Test Publication Title",
        "abstract": "This is a test abstract for unit testing purposes.",
        "authors": [
            {"name": "Smith, John", "affiliation": "Test University"},
            {"name": "Doe, Jane", "affiliation": "Test Institute"},
        ],
        "journal": "Test Journal",
        "doi": "10.1234/test.123",
        "publication_date": "2024-01-15",
    }


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing local file parsing."""
    return """sample_id,organism,tissue,treatment
S001,Homo sapiens,liver,control
S002,Homo sapiens,liver,treated
S003,Homo sapiens,kidney,control
S004,Homo sapiens,kidney,treated
"""


@pytest.fixture
def sample_investigation_model():
    """Sample Investigation model for testing ISA builder."""
    from isaforge.models.isa.investigation import (
        Investigation,
        OntologySourceReference,
    )
    from isaforge.models.isa.study import (
        Person,
        Study,
        StudyDesignDescriptor,
        StudyFactor,
    )
    from isaforge.models.isa.sample import Characteristic, Sample, Source
    from isaforge.models.isa.protocol import Protocol

    return Investigation(
        identifier="INV001",
        title="Test Investigation",
        description="A test investigation for unit testing",
        ontology_source_references=[
            OntologySourceReference(
                name="OBI",
                version="2024-01-01",
                description="Ontology for Biomedical Investigations",
            ),
        ],
        studies=[
            Study(
                identifier="STUDY001",
                title="Test Study",
                description="A test study",
                filename="s_study.txt",
                design_descriptors=[
                    StudyDesignDescriptor(
                        design_type="intervention design",
                        design_type_term_accession="OBI:0000115",
                        design_type_term_source="OBI",
                    ),
                ],
                factors=[
                    StudyFactor(
                        name="treatment",
                        factor_type="chemical compound",
                        factor_type_term_accession="CHEBI:37577",
                        factor_type_term_source="CHEBI",
                    ),
                ],
                protocols=[
                    Protocol(
                        name="sample collection",
                        protocol_type="sample collection",
                    ),
                ],
                sources=[
                    Source(
                        name="source1",
                        characteristics=[
                            Characteristic(
                                category="organism",
                                value="Homo sapiens",
                                term_accession="NCBITaxon:9606",
                                term_source="NCBITaxon",
                            ),
                        ],
                    ),
                ],
                samples=[
                    Sample(
                        name="sample1",
                        derives_from=["source1"],
                        characteristics=[
                            Characteristic(
                                category="tissue",
                                value="liver",
                                term_accession="UBERON:0002107",
                                term_source="UBERON",
                            ),
                        ],
                    ),
                ],
                contacts=[
                    Person(
                        last_name="Smith",
                        first_name="John",
                        email="john.smith@test.edu",
                        roles=["principal investigator"],
                    ),
                ],
            ),
        ],
    )


@pytest_asyncio.fixture
async def test_session_manager():
    """Create a test session manager with in-memory database."""
    from isaforge.session.database import init_database
    from isaforge.session.manager import SessionManager

    await init_database()
    return SessionManager()
