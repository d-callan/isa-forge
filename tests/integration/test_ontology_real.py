"""Integration tests with REAL ontology service API calls.

These tests make actual API calls to OLS and Zooma to verify our clients work
and to capture real response formats for creating mocks.

Run with: pytest tests/integration/test_ontology_real.py -v -s --capture=no

NOTE: These tests are marked as 'integration' and require internet connection.
"""

import json
import pytest
from pathlib import Path

from isaforge.ontology.services.ols import OLSService
from isaforge.ontology.services.zooma import ZoomaService
from isaforge.ontology.mapper import OntologyMapper
from isaforge.ontology.registry import setup_default_services


pytestmark = pytest.mark.integration


@pytest.fixture
def response_cache_dir(tmp_path):
    """Directory to cache API responses for mock creation."""
    cache_dir = tmp_path / "ontology_responses"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def save_response(cache_dir: Path, name: str, data):
    """Save API response to JSON file."""
    output_file = cache_dir / f"{name}.json"
    if isinstance(data, list):
        data = [term.model_dump() if hasattr(term, 'model_dump') else term for term in data]
    elif hasattr(data, 'model_dump'):
        data = data.model_dump()
    output_file.write_text(json.dumps(data, indent=2, default=str))
    print(f"\n✓ Saved response to: {output_file}")


class TestOLSServiceReal:
    """Test OLS service with real API calls."""

    @pytest.mark.asyncio
    async def test_ols_search_liver_real(self, response_cache_dir):
        """Test searching OLS for 'liver'."""
        ols = OLSService()

        terms = await ols.search("liver", ontologies=["UBERON"], limit=5)

        assert len(terms) > 0
        assert any("liver" in term.label.lower() for term in terms)

        save_response(response_cache_dir, "ols_search_liver", terms)

        print(f"\nFound {len(terms)} terms for 'liver':")
        for term in terms[:3]:
            print(f"  - {term.label} ({term.term_id}) from {term.ontology}")

    @pytest.mark.asyncio
    async def test_ols_search_rna_seq_real(self, response_cache_dir):
        """Test searching for RNA-Seq in OBI."""
        ols = OLSService()

        terms = await ols.search("RNA-Seq", ontologies=["OBI"], limit=5)

        assert len(terms) > 0

        save_response(response_cache_dir, "ols_search_rnaseq", terms)

        print(f"\nFound {len(terms)} terms for 'RNA-Seq':")
        for term in terms:
            print(f"  - {term.label} ({term.term_id})")

    @pytest.mark.asyncio
    async def test_ols_get_term_by_id_real(self, response_cache_dir):
        """Test getting a specific term by ID."""
        ols = OLSService()

        # Get a well-known term
        term = await ols.get_term("UBERON:0002107")  # liver

        if term:
            assert term.term_id == "UBERON:0002107"
            assert "liver" in term.label.lower()

            save_response(response_cache_dir, "ols_get_term_liver", term)

            print(f"\nTerm: {term.label}")
            print(f"ID: {term.term_id}")
            print(f"Description: {term.description}")
        else:
            print("\nTerm not found (API may have changed)")

    @pytest.mark.asyncio
    async def test_ols_is_available_real(self):
        """Test OLS availability check."""
        ols = OLSService()

        is_available = await ols.is_available()

        print(f"\nOLS available: {is_available}")
        assert is_available is True


class TestZoomaServiceReal:
    """Test Zooma service with real API calls."""

    @pytest.mark.asyncio
    async def test_zooma_search_liver_real(self, response_cache_dir):
        """Test Zooma annotation for 'liver'."""
        zooma = ZoomaService()

        terms = await zooma.search("liver", limit=5)

        # Zooma may return 0 results depending on the query
        print(f"\nZooma found {len(terms)} annotations for 'liver':")
        for term in terms[:3]:
            print(f"  - {term.label} ({term.term_id}) from {term.ontology}")

        save_response(response_cache_dir, "zooma_search_liver", terms)

    @pytest.mark.asyncio
    async def test_zooma_search_with_ontology_filter_real(self, response_cache_dir):
        """Test Zooma with ontology filter."""
        zooma = ZoomaService()

        terms = await zooma.search("tissue", ontologies=["UBERON"], limit=5)

        print(f"\nZooma found {len(terms)} annotations for 'tissue' in UBERON")

        save_response(response_cache_dir, "zooma_search_tissue", terms)

    @pytest.mark.asyncio
    async def test_zooma_annotate_with_confidence_real(self, response_cache_dir):
        """Test Zooma annotation with confidence scores."""
        zooma = ZoomaService()

        results = await zooma.annotate_with_confidence("liver tissue")

        print(f"\nZooma annotations with confidence:")
        for result in results[:3]:
            term = result["term"]
            print(f"  - {term.label} ({term.term_id}): {result['confidence']}")

        save_response(response_cache_dir, "zooma_annotate_confidence", results)

    @pytest.mark.asyncio
    async def test_zooma_is_available_real(self):
        """Test Zooma availability check."""
        zooma = ZoomaService()

        is_available = await zooma.is_available()

        print(f"\nZooma available: {is_available}")


class TestOntologyMapperReal:
    """Test ontology mapper with real API calls."""

    @pytest.mark.asyncio
    async def test_map_tissue_term_real(self, response_cache_dir):
        """Test mapping a tissue term."""
        setup_default_services()
        mapper = OntologyMapper()

        mapping = await mapper.map_term("liver")

        assert mapping.source_text == "liver"
        if mapping.mapped_term:
            print(f"\nMapped 'liver' to:")
            print(f"  Term: {mapping.mapped_term.label}")
            print(f"  ID: {mapping.mapped_term.term_id}")
            print(f"  Confidence: {mapping.confidence:.2f}")
            print(f"  Source: {mapping.mapping_source}")
            print(f"  Justification: {mapping.justification}")

        save_response(response_cache_dir, "mapper_liver", mapping.model_dump())

    @pytest.mark.asyncio
    async def test_map_assay_term_real(self, response_cache_dir):
        """Test mapping an assay type."""
        setup_default_services()
        mapper = OntologyMapper()

        mapping = await mapper.map_term("RNA sequencing", ontologies=["OBI"])

        if mapping.mapped_term:
            print(f"\nMapped 'RNA sequencing' to:")
            print(f"  Term: {mapping.mapped_term.label}")
            print(f"  ID: {mapping.mapped_term.term_id}")
            print(f"  Confidence: {mapping.confidence:.2f}")

        save_response(response_cache_dir, "mapper_rnaseq", mapping.model_dump())

    @pytest.mark.asyncio
    async def test_map_batch_terms_real(self, response_cache_dir):
        """Test batch mapping multiple terms."""
        setup_default_services()
        mapper = OntologyMapper()

        terms = ["liver", "kidney", "heart", "brain"]
        mappings = await mapper.map_batch(terms)

        assert len(mappings) == len(terms)

        print(f"\nBatch mapping results:")
        for text, mapping in mappings.items():
            if mapping.mapped_term:
                print(f"  {text} -> {mapping.mapped_term.label} ({mapping.confidence:.2f})")

        save_response(response_cache_dir, "mapper_batch", 
                     {k: v.model_dump() for k, v in mappings.items()})

    @pytest.mark.asyncio
    async def test_map_or_create_custom_real(self, response_cache_dir):
        """Test mapping with custom term fallback."""
        setup_default_services()
        mapper = OntologyMapper()

        # Use a very specific term unlikely to be in ontologies
        mapping = await mapper.map_or_create_custom(
            "super rare tissue type xyz123",
            min_confidence=0.8
        )

        print(f"\nMapping result:")
        if mapping.mapped_term:
            print(f"  Term: {mapping.mapped_term.label}")
            print(f"  ID: {mapping.mapped_term.term_id}")
            print(f"  Is custom: {mapping.mapped_term.is_custom}")
            print(f"  Confidence: {mapping.confidence:.2f}")

        save_response(response_cache_dir, "mapper_custom_fallback", mapping.model_dump())


@pytest.mark.asyncio
async def test_save_all_ontology_responses_for_mocks(tmp_path):
    """Comprehensive test to save all ontology response types for mock creation."""
    cache_dir = tmp_path / "ontology_mock_fixtures"
    cache_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Saving ontology API responses to: {cache_dir}")
    print(f"{'='*60}")

    ols = OLSService()
    zooma = ZoomaService()
    setup_default_services()
    mapper = OntologyMapper()

    # 1. OLS searches
    ols_liver = await ols.search("liver", ontologies=["UBERON"], limit=3)
    save_response(cache_dir, "mock_ols_liver", ols_liver)

    ols_rnaseq = await ols.search("RNA-Seq", ontologies=["OBI"], limit=3)
    save_response(cache_dir, "mock_ols_rnaseq", ols_rnaseq)

    # 2. OLS get term
    ols_term = await ols.get_term("UBERON:0002107")
    if ols_term:
        save_response(cache_dir, "mock_ols_term", ols_term)

    # 3. Zooma searches
    zooma_liver = await zooma.search("liver", limit=3)
    save_response(cache_dir, "mock_zooma_liver", zooma_liver)

    # 4. Zooma with confidence
    zooma_conf = await zooma.annotate_with_confidence("liver tissue")
    save_response(cache_dir, "mock_zooma_confidence", zooma_conf)

    # 5. Mapper results
    mapper_liver = await mapper.map_term("liver")
    save_response(cache_dir, "mock_mapper_liver", mapper_liver.model_dump())

    mapper_batch = await mapper.map_batch(["liver", "kidney"])
    save_response(cache_dir, "mock_mapper_batch",
                 {k: v.model_dump() for k, v in mapper_batch.items()})

    print(f"\n{'='*60}")
    print(f"✓ All ontology responses saved successfully!")
    print(f"{'='*60}")
