"""Unit tests for NCBI retrieval modules using mocks."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from isaforge.retrieval.ncbi.client import NCBIClient
from isaforge.retrieval.ncbi.bioproject import BioProjectRetriever
from isaforge.retrieval.ncbi.pubmed import PubMedRetriever
from isaforge.core.exceptions import NCBIError

from tests.fixtures.ncbi_responses import (
    BIOPROJECT_SEARCH_RESPONSE,
    BIOPROJECT_SUMMARY_RESPONSE,
    BIOPROJECT_FULL_METADATA,
    PUBMED_SEARCH_RESPONSE,
    PUBMED_ARTICLE_RESPONSE,
    PUBMED_MULTIPLE_RESPONSE,
    LINKED_PUBMED_RESPONSE,
)


class TestNCBIClient:
    """Test NCBI client with mocked responses."""

    @pytest.mark.asyncio
    async def test_search_bioproject(self):
        """Test searching for a BioProject."""
        client = NCBIClient()

        with patch.object(client, 'esearch', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = BIOPROJECT_SEARCH_RESPONSE["esearchresult"]

            result = await client.search_bioproject("PRJNA13")

            assert "idlist" in result
            assert "13" in result["idlist"]
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_bioproject_summary(self):
        """Test getting BioProject summary."""
        client = NCBIClient()

        with patch.object(client, 'esummary', new_callable=AsyncMock) as mock_summary:
            mock_summary.return_value = BIOPROJECT_SUMMARY_RESPONSE["result"]

            result = await client.get_bioproject_summary("13")

            assert "13" in result
            assert result["13"]["project_acc"] == "PRJNA13"
            assert "Escherichia coli" in result["13"]["project_title"]

    @pytest.mark.asyncio
    async def test_esearch_pubmed(self):
        """Test searching PubMed."""
        client = NCBIClient()

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = PUBMED_SEARCH_RESPONSE

            result = await client.esearch("pubmed", "CRISPR", retmax=5)

            assert "idlist" in result
            assert len(result["idlist"]) == 2

    @pytest.mark.asyncio
    async def test_get_linked_pubmed(self):
        """Test getting linked PubMed IDs."""
        client = NCBIClient()

        with patch.object(client, 'elink', new_callable=AsyncMock) as mock_link:
            mock_link.return_value = LINKED_PUBMED_RESPONSE

            pmids = await client.get_linked_pubmed("13")

            assert len(pmids) == 2
            assert "12345678" in pmids

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test HTTP error handling."""
        client = NCBIClient()

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = NCBIError("API error: 500")

            with pytest.raises(NCBIError):
                await client.search_bioproject("INVALID")


class TestBioProjectRetriever:
    """Test BioProject retriever with mocked responses."""

    @pytest.mark.asyncio
    async def test_fetch_metadata(self):
        """Test fetching BioProject metadata."""
        retriever = BioProjectRetriever()

        # Mock the client methods with proper return structures
        with patch.object(retriever.client, 'search_bioproject', new_callable=AsyncMock) as mock_search, \
             patch.object(retriever.client, 'get_bioproject_summary', new_callable=AsyncMock) as mock_summary, \
             patch.object(retriever.client, 'get_linked_pubmed', new_callable=AsyncMock) as mock_pubmed, \
             patch.object(retriever.client, 'get_linked_sra', new_callable=AsyncMock) as mock_sra:

            mock_search.return_value = {"idlist": ["13"]}
            mock_summary.return_value = {"13": BIOPROJECT_SUMMARY_RESPONSE["result"]["13"]}
            mock_pubmed.return_value = []
            mock_sra.return_value = []

            metadata = await retriever.fetch_metadata("PRJNA13")

            assert metadata["accession"] == "PRJNA13"
            assert "Escherichia coli" in metadata["title"]
            assert metadata["organism"] == "Escherichia coli str. K-12 substr. MG1655"
            assert metadata["taxon_id"] == 511145

    @pytest.mark.asyncio
    async def test_validate_identifier(self):
        """Test BioProject identifier validation."""
        retriever = BioProjectRetriever()

        assert await retriever.validate_identifier("PRJNA13")
        assert await retriever.validate_identifier("PRJEB1234")
        assert await retriever.validate_identifier("PRJDA5678")
        assert not await retriever.validate_identifier("invalid")
        assert not await retriever.validate_identifier("PRJ123")



class TestPubMedRetriever:
    """Test PubMed retriever with mocked responses."""

    @pytest.mark.asyncio
    async def test_fetch_metadata(self):
        """Test fetching PubMed article metadata."""
        retriever = PubMedRetriever()

        with patch.object(retriever.client, 'efetch', new_callable=AsyncMock) as mock_efetch:
            # Mock XML response with proper structure
            mock_xml = """<?xml version="1.0"?>
            <PubmedArticleSet>
                <PubmedArticle>
                    <MedlineCitation>
                        <PMID>12163470</PMID>
                        <Article>
                            <ArticleTitle>Identification of genes that are associated with DNA repeats in prokaryotes</ArticleTitle>
                            <Abstract><AbstractText>A novel family of repeats, called CRISPR.</AbstractText></Abstract>
                            <AuthorList>
                                <Author>
                                    <LastName>Jansen</LastName>
                                    <ForeName>R</ForeName>
                                    <Initials>R</Initials>
                                    <Affiliation>Department of Molecular Microbiology, Utrecht University</Affiliation>
                                </Author>
                            </AuthorList>
                            <Journal>
                                <Title>Molecular Microbiology</Title>
                            </Journal>
                        </Article>
                    </MedlineCitation>
                    <PubmedData>
                        <ArticleIdList>
                            <ArticleId IdType="doi">10.1046/j.1365-2958.2002.02839.x</ArticleId>
                        </ArticleIdList>
                    </PubmedData>
                </PubmedArticle>
            </PubmedArticleSet>
            """
            mock_efetch.return_value = mock_xml

            metadata = await retriever.fetch_metadata("12163470")

            assert metadata["pmid"] == "12163470"
            assert "repeats" in metadata["title"].lower() or "CRISPR" in metadata.get("abstract", "")

    @pytest.mark.asyncio
    async def test_fetch_multiple(self):
        """Test fetching multiple PubMed articles."""
        retriever = PubMedRetriever()

        with patch.object(retriever, 'fetch_metadata', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = PUBMED_MULTIPLE_RESPONSE

            publications = await retriever.fetch_multiple(["12163470", "15822210"], max_count=2)

            assert len(publications) == 2
            assert publications[0]["pmid"] == "12163470"
            assert publications[1]["pmid"] == "15822210"

    @pytest.mark.asyncio
    async def test_validate_identifier(self):
        """Test PMID validation."""
        retriever = PubMedRetriever()

        assert await retriever.validate_identifier("12345678")
        assert await retriever.validate_identifier("1")
        assert not await retriever.validate_identifier("invalid")
        assert not await retriever.validate_identifier("PMC123456")



class TestNCBIErrorHandling:
    """Test error handling in NCBI modules."""

    @pytest.mark.asyncio
    async def test_bioproject_not_found(self):
        """Test handling of non-existent BioProject."""
        from isaforge.core.exceptions import RetrievalError
        retriever = BioProjectRetriever()

        with patch.object(retriever.client, 'search_bioproject', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"idlist": []}

            with pytest.raises(RetrievalError):
                await retriever.fetch_metadata("PRJNANONEXISTENT")

    @pytest.mark.asyncio
    async def test_pubmed_not_found(self):
        """Test handling of non-existent PubMed article."""
        from isaforge.core.exceptions import RetrievalError
        retriever = PubMedRetriever()

        with patch.object(retriever.client, 'efetch', new_callable=AsyncMock) as mock_efetch:
            mock_efetch.return_value = "<PubmedArticleSet></PubmedArticleSet>"

            with pytest.raises(RetrievalError):
                await retriever.fetch_metadata("99999999")

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test handling of rate limit errors."""
        client = NCBIClient()

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = NCBIError("API error: 429")

            with pytest.raises(NCBIError, match="429"):
                await client.search_bioproject("PRJNA13")
