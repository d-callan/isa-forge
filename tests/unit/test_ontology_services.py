"""Unit tests for ontology services using mocks."""

import pytest
from unittest.mock import AsyncMock, patch

from isaforge.ontology.services.ols import OLSService
from isaforge.ontology.services.zooma import ZoomaService
from isaforge.ontology.mapper import OntologyMapper
from isaforge.ontology.registry import OntologyRegistry, setup_default_services

from tests.fixtures.ontology_responses import (
    OLS_LIVER_TERMS,
    OLS_RNASEQ_TERMS,
    OLS_TERM_LIVER,
    ZOOMA_LIVER_TERMS,
    ZOOMA_CONFIDENCE_RESULTS,
    MAPPER_LIVER_RESULT,
    MAPPER_BATCH_RESULTS,
    MAPPER_CUSTOM_TERM_RESULT,
)


class TestOLSService:
    """Test OLS service with mocked responses."""

    @pytest.mark.asyncio
    async def test_search_terms(self):
        """Test searching for ontology terms."""
        ols = OLSService()

        with patch.object(ols, '_request', new_callable=AsyncMock) as mock_request:
            # Mock OLS API response structure
            mock_request.return_value = {
                "response": {
                    "docs": [
                        {
                            "label": "liver",
                            "obo_id": "UBERON:0002107",
                            "ontology_name": "uberon",
                            "iri": "http://purl.obolibrary.org/obo/UBERON_0002107",
                            "description": ["A large organ in the body"],
                            "obo_synonym": ["hepatic tissue", "hepar"]
                        }
                    ]
                }
            }

            results = await ols.search("liver", ontologies=["UBERON"], limit=5)

            assert len(results) > 0
            assert results[0].label == "liver"
            assert results[0].term_id == "UBERON:0002107"
            assert results[0].ontology == "UBERON"

    @pytest.mark.asyncio
    async def test_get_term_by_id(self):
        """Test getting a specific term by ID."""
        ols = OLSService()

        with patch.object(ols, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "label": "liver",
                "obo_id": "UBERON:0002107",
                "ontology_name": "uberon",
                "iri": "http://purl.obolibrary.org/obo/UBERON_0002107",
                "description": ["A large organ in the body"],
                "obo_synonym": ["hepatic tissue"]
            }

            term = await ols.get_term("UBERON:0002107")

            assert term is not None
            assert term.term_id == "UBERON:0002107"
            assert term.label == "liver"

    @pytest.mark.asyncio
    async def test_is_available(self):
        """Test OLS availability check."""
        ols = OLSService()

        with patch.object(ols, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "ok"}

            is_available = await ols.is_available()

            assert is_available is True

    @pytest.mark.asyncio
    async def test_search_with_no_results(self):
        """Test search with no results."""
        ols = OLSService()

        with patch.object(ols, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"response": {"docs": []}}

            results = await ols.search("nonexistent_term_xyz123")

            assert len(results) == 0


class TestZoomaService:
    """Test Zooma service with mocked responses."""

    @pytest.mark.asyncio
    async def test_search_annotations(self):
        """Test searching for annotations."""
        zooma = ZoomaService()

        with patch.object(zooma, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "annotatedProperty": {"propertyValue": "liver"},
                    "semanticTags": ["http://purl.obolibrary.org/obo/UBERON_0002107"],
                    "confidence": "HIGH"
                }
            ]

            results = await zooma.search("liver", limit=5)

            assert len(results) > 0
            assert "liver" in results[0].label.lower() or results[0].term_id == "UBERON:0002107"

    @pytest.mark.asyncio
    async def test_annotate_with_confidence(self):
        """Test annotation with confidence scores."""
        zooma = ZoomaService()

        with patch.object(zooma, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "annotatedProperty": {"propertyValue": "liver"},
                    "semanticTags": ["http://purl.obolibrary.org/obo/UBERON_0002107"],
                    "confidence": "HIGH"
                }
            ]

            results = await zooma.annotate_with_confidence("liver")

            assert len(results) > 0
            assert "confidence" in results[0]
            # Zooma returns string confidence values: HIGH, GOOD, MEDIUM, LOW
            assert results[0]["confidence"] in ["HIGH", "GOOD", "MEDIUM", "LOW"]

    @pytest.mark.asyncio
    async def test_is_available(self):
        """Test Zooma availability check."""
        zooma = ZoomaService()

        with patch.object(zooma, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []

            is_available = await zooma.is_available()

            assert is_available is True


class TestOntologyMapper:
    """Test ontology mapper with mocked services."""

    @pytest.mark.asyncio
    async def test_map_term_with_services(self):
        """Test mapping a term using provided services."""
        # Create mock service with proper interface
        mock_service = AsyncMock()
        mock_service.search = AsyncMock(return_value=OLS_LIVER_TERMS)
        mock_service.get_service_name = lambda: "mock_ols"

        mapper = OntologyMapper(services=[mock_service])

        mapping = await mapper.map_term("liver")

        assert mapping.source_text == "liver"
        assert mapping.mapped_term is not None
        assert mapping.mapped_term.term_id == "UBERON:0002107"

    @pytest.mark.asyncio
    async def test_map_batch(self):
        """Test batch mapping multiple terms."""
        mock_service = AsyncMock()
        mock_service.search = AsyncMock(side_effect=[OLS_LIVER_TERMS, [OLS_LIVER_TERMS[1]]])
        mock_service.get_service_name = lambda: "mock_ols"

        mapper = OntologyMapper(services=[mock_service])

        mappings = await mapper.map_batch(["liver", "kidney"])

        assert len(mappings) == 2
        assert "liver" in mappings
        assert "kidney" in mappings

    @pytest.mark.asyncio
    async def test_map_or_create_custom(self):
        """Test mapping with custom term creation fallback."""
        mock_service = AsyncMock()
        mock_service.search = AsyncMock(return_value=[])
        mock_service.get_service_name = lambda: "mock_ols"

        mapper = OntologyMapper(services=[mock_service])

        mapping = await mapper.map_or_create_custom("rare_term_xyz", min_confidence=0.8)

        assert mapping.source_text == "rare_term_xyz"
        assert mapping.mapped_term is not None
        assert mapping.mapped_term.is_custom is True


class TestOntologyRegistry:
    """Test ontology registry."""

    def test_register_service(self):
        """Test registering a service."""
        ols = OLSService()

        OntologyRegistry.register("test_ols", ols)

        assert OntologyRegistry.get("test_ols") == ols

    def test_get_service(self):
        """Test getting a registered service."""
        ols = OLSService()
        OntologyRegistry.register("ols", ols)

        service = OntologyRegistry.get("ols")

        assert service == ols

    def test_get_nonexistent_service(self):
        """Test getting a service that doesn't exist."""
        service = OntologyRegistry.get("nonexistent_xyz_123")

        assert service is None

    def test_list_services(self):
        """Test listing registered services."""
        # Clear and register test services
        OntologyRegistry._services = {}
        OntologyRegistry.register("test1", OLSService())
        OntologyRegistry.register("test2", ZoomaService())

        services = OntologyRegistry.list_services()

        assert len(services) >= 2
        assert "test1" in services
        assert "test2" in services


class TestOntologyScoring:
    """Test ontology term scoring logic."""

    @pytest.mark.asyncio
    async def test_exact_match_high_confidence(self):
        """Test that exact matches get high confidence."""
        mock_service = AsyncMock()
        mock_service.search = AsyncMock(return_value=[OLS_TERM_LIVER])
        mock_service.get_service_name = lambda: "mock_ols"

        mapper = OntologyMapper(services=[mock_service])

        mapping = await mapper.map_term("liver")

        assert mapping.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_partial_match_lower_confidence(self):
        """Test that partial matches still work."""
        mock_service = AsyncMock()
        mock_service.search = AsyncMock(return_value=[OLS_LIVER_TERMS[1]])  # "liver cell"
        mock_service.get_service_name = lambda: "mock_ols"

        mapper = OntologyMapper(services=[mock_service])

        mapping = await mapper.map_term("liver")

        # Should still map
        assert mapping.mapped_term is not None
