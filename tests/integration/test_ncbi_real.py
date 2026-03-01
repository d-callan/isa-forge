"""Integration tests with REAL NCBI API calls.

These tests make actual API calls to NCBI to verify our client works
and to capture real response formats for creating mocks.

Run with: pytest tests/integration/test_ncbi_real.py -v -s --capture=no

NOTE: These tests are marked as 'integration' and require internet connection.
They may be slow and can fail if NCBI is down.
"""

import json
import pytest
from pathlib import Path

from isaforge.retrieval.ncbi.client import NCBIClient
from isaforge.retrieval.ncbi.bioproject import BioProjectRetriever
from isaforge.retrieval.ncbi.pubmed import PubMedRetriever


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def response_cache_dir(tmp_path):
    """Directory to cache API responses for mock creation."""
    cache_dir = tmp_path / "api_responses"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def save_response(cache_dir: Path, name: str, data: dict):
    """Save API response to JSON file."""
    output_file = cache_dir / f"{name}.json"
    output_file.write_text(json.dumps(data, indent=2, default=str))
    print(f"\n✓ Saved response to: {output_file}")


class TestNCBIClientReal:
    """Test NCBI client with real API calls."""

    @pytest.mark.asyncio
    async def test_search_bioproject_real(self, response_cache_dir):
        """Test searching for a real BioProject."""
        client = NCBIClient()
        
        # Use a well-known BioProject
        accession = "PRJNA13"  # E. coli genome project
        
        result = await client.search_bioproject(accession)
        
        assert "idlist" in result
        assert len(result["idlist"]) > 0
        
        save_response(response_cache_dir, "bioproject_search", result)
        
        print(f"\nBioProject search result: {result}")

    @pytest.mark.asyncio
    async def test_get_bioproject_summary_real(self, response_cache_dir):
        """Test getting BioProject summary."""
        client = NCBIClient()
        
        # First search to get UID
        search_result = await client.search_bioproject("PRJNA13")
        bioproject_uid = search_result["idlist"][0]
        
        # Get summary
        summary = await client.get_bioproject_summary(bioproject_uid)
        
        assert bioproject_uid in summary
        project_data = summary[bioproject_uid]
        
        assert "project_title" in project_data or "project_acc" in project_data
        
        save_response(response_cache_dir, "bioproject_summary", summary)
        
        print(f"\nBioProject summary keys: {project_data.keys()}")

    @pytest.mark.asyncio
    async def test_get_linked_pubmed_real(self, response_cache_dir):
        """Test getting linked PubMed IDs."""
        client = NCBIClient()
        
        # Use a BioProject known to have publications
        search_result = await client.search_bioproject("PRJNA13")
        bioproject_uid = search_result["idlist"][0]
        
        pmids = await client.get_linked_pubmed(bioproject_uid)
        
        # May or may not have publications
        print(f"\nLinked PubMed IDs: {pmids}")
        
        save_response(response_cache_dir, "linked_pubmed", {"pmids": pmids})

    @pytest.mark.asyncio
    async def test_esearch_pubmed_real(self, response_cache_dir):
        """Test searching PubMed."""
        client = NCBIClient()
        
        result = await client.esearch("pubmed", "CRISPR", retmax=5)
        
        assert "idlist" in result
        assert len(result["idlist"]) > 0
        
        save_response(response_cache_dir, "pubmed_search", result)
        
        print(f"\nPubMed search found {len(result['idlist'])} results")


class TestBioProjectRetrieverReal:
    """Test BioProject retriever with real API calls."""

    @pytest.mark.asyncio
    async def test_fetch_bioproject_metadata_real(self, response_cache_dir):
        """Test fetching complete BioProject metadata."""
        retriever = BioProjectRetriever()
        
        # Use a small, well-documented BioProject
        accession = "PRJNA13"
        
        metadata = await retriever.fetch_metadata(accession)
        
        assert metadata["accession"] == accession
        assert "title" in metadata
        
        save_response(response_cache_dir, "bioproject_full_metadata", metadata)
        
        print(f"\nBioProject metadata keys: {metadata.keys()}")
        print(f"Title: {metadata.get('title', 'N/A')}")
        print(f"Organism: {metadata.get('organism', 'N/A')}")
        print(f"Samples: {len(metadata.get('samples', []))}")
        print(f"Experiments: {len(metadata.get('experiments', []))}")

    @pytest.mark.asyncio
    async def test_validate_bioproject_accession(self):
        """Test BioProject accession validation."""
        retriever = BioProjectRetriever()
        
        assert await retriever.validate_identifier("PRJNA13")
        assert await retriever.validate_identifier("PRJEB1234")
        assert await retriever.validate_identifier("PRJDA5678")
        assert not await retriever.validate_identifier("invalid")
        assert not await retriever.validate_identifier("PRJ123")


class TestPubMedRetrieverReal:
    """Test PubMed retriever with real API calls."""

    @pytest.mark.asyncio
    async def test_fetch_pubmed_article_real(self, response_cache_dir):
        """Test fetching a real PubMed article."""
        retriever = PubMedRetriever()
        
        # Use a well-known paper (first CRISPR paper)
        pmid = "12163470"  # Jansen et al. 2002 - CRISPR discovery
        
        metadata = await retriever.fetch_metadata(pmid)
        
        assert metadata["pmid"] == pmid
        assert "title" in metadata
        assert len(metadata.get("authors", [])) > 0
        
        save_response(response_cache_dir, "pubmed_article", metadata)
        
        print(f"\nPubMed article:")
        print(f"Title: {metadata.get('title', 'N/A')[:100]}...")
        print(f"Authors: {len(metadata.get('authors', []))}")
        print(f"Journal: {metadata.get('journal', 'N/A')}")
        print(f"DOI: {metadata.get('doi', 'N/A')}")

    @pytest.mark.asyncio
    async def test_fetch_multiple_pubmed_real(self, response_cache_dir):
        """Test fetching multiple PubMed articles."""
        retriever = PubMedRetriever()
        
        pmids = ["12163470", "15822210"]  # Two CRISPR-related papers
        
        publications = await retriever.fetch_multiple(pmids, max_count=2)
        
        assert len(publications) == 2
        
        save_response(response_cache_dir, "pubmed_multiple", publications)
        
        for pub in publications:
            print(f"\nPMID {pub.get('pmid')}: {pub.get('title', 'N/A')[:80]}...")

    @pytest.mark.asyncio
    async def test_validate_pmid(self):
        """Test PMID validation."""
        retriever = PubMedRetriever()
        
        assert await retriever.validate_identifier("12345678")
        assert await retriever.validate_identifier("1")
        assert not await retriever.validate_identifier("invalid")
        assert not await retriever.validate_identifier("PMC123456")


class TestSRAMetadataReal:
    """Test SRA metadata parsing with real data."""

    @pytest.mark.asyncio
    async def test_fetch_bioproject_with_sra_real(self, response_cache_dir):
        """Test fetching BioProject with SRA data."""
        retriever = BioProjectRetriever()
        
        # Use a BioProject known to have SRA data
        # PRJNA13 is old and may not have SRA, so try a more recent one
        accession = "PRJNA13"
        
        metadata = await retriever.fetch_metadata(accession)
        
        # Save the full metadata including SRA if present
        save_response(response_cache_dir, "bioproject_with_sra", metadata)
        
        print(f"\nSRA Experiments: {len(metadata.get('experiments', []))}")
        print(f"SRA Samples: {len(metadata.get('samples', []))}")
        print(f"SRA Runs: {len(metadata.get('runs', []))}")
        
        if metadata.get("experiments"):
            exp = metadata["experiments"][0]
            print(f"\nFirst experiment keys: {exp.keys()}")


@pytest.mark.asyncio
async def test_save_all_responses_for_mocks(tmp_path):
    """Comprehensive test to save all response types for mock creation.
    
    This test makes multiple API calls and saves all responses to files
    that can be used to create accurate mocks.
    """
    cache_dir = tmp_path / "mock_fixtures"
    cache_dir.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Saving API responses to: {cache_dir}")
    print(f"{'='*60}")
    
    client = NCBIClient()
    bioproject_retriever = BioProjectRetriever()
    pubmed_retriever = PubMedRetriever()
    
    # 1. BioProject search
    bp_search = await client.search_bioproject("PRJNA13")
    save_response(cache_dir, "mock_bioproject_search", bp_search)
    
    # 2. BioProject summary
    if bp_search.get("idlist"):
        bp_uid = bp_search["idlist"][0]
        bp_summary = await client.get_bioproject_summary(bp_uid)
        save_response(cache_dir, "mock_bioproject_summary", bp_summary)
    
    # 3. Full BioProject metadata
    bp_metadata = await bioproject_retriever.fetch_metadata("PRJNA13")
    save_response(cache_dir, "mock_bioproject_full", bp_metadata)
    
    # 4. PubMed article
    pm_metadata = await pubmed_retriever.fetch_metadata("12163470")
    save_response(cache_dir, "mock_pubmed_article", pm_metadata)
    
    # 5. Multiple PubMed articles
    pm_multiple = await pubmed_retriever.fetch_multiple(["12163470", "15822210"])
    save_response(cache_dir, "mock_pubmed_multiple", pm_multiple)
    
    print(f"\n{'='*60}")
    print(f"✓ All responses saved successfully!")
    print(f"{'='*60}")
    print(f"\nUse these files to create mock fixtures in tests/fixtures/")
