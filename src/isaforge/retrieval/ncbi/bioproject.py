"""BioProject metadata retrieval from NCBI."""

import re
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

from isaforge.core.exceptions import NCBIError, RetrievalError
from isaforge.models.metadata.bioproject import (
    BioProjectMetadata,
    SRAExperiment,
    SRARun,
    SRASample,
)
from isaforge.observability.logger import get_logger
from isaforge.retrieval.base import BaseRetriever
from isaforge.retrieval.ncbi.client import NCBIClient

logger = get_logger(__name__)

# Regex for BioProject accession
BIOPROJECT_PATTERN = re.compile(r"^PRJ[A-Z]{2}\d+$")


class BioProjectRetriever(BaseRetriever):
    """Retriever for BioProject metadata from NCBI."""

    def __init__(self, client: NCBIClient | None = None):
        """Initialize the retriever.

        Args:
            client: Optional NCBI client instance.
        """
        self.client = client or NCBIClient()

    async def validate_identifier(self, identifier: str) -> bool:
        """Validate a BioProject accession.

        Args:
            identifier: The accession to validate.

        Returns:
            True if valid BioProject accession format.
        """
        return bool(BIOPROJECT_PATTERN.match(identifier.upper()))

    def get_source_name(self) -> str:
        """Get the source name.

        Returns:
            'ncbi_bioproject'
        """
        return "ncbi_bioproject"

    async def fetch_metadata(self, identifier: str) -> dict[str, Any]:
        """Fetch BioProject metadata.

        Args:
            identifier: BioProject accession (e.g., 'PRJNA123456').

        Returns:
            Dictionary with BioProject metadata.

        Raises:
            RetrievalError: If retrieval fails.
        """
        accession = identifier.upper()

        if not await self.validate_identifier(accession):
            raise RetrievalError(f"Invalid BioProject accession: {identifier}")

        try:
            # Search for the BioProject
            search_result = await self.client.search_bioproject(accession)
            id_list = search_result.get("idlist", [])

            if not id_list:
                raise RetrievalError(f"BioProject not found: {accession}")

            bioproject_uid = id_list[0]

            # Get summary
            summary = await self.client.get_bioproject_summary(bioproject_uid)
            project_data = summary.get(bioproject_uid, {})

            # Get linked PubMed IDs
            pubmed_ids = await self.client.get_linked_pubmed(bioproject_uid)

            # Get linked SRA data
            sra_ids = await self.client.get_linked_sra(bioproject_uid)

            # Build metadata object
            metadata = self._parse_bioproject_summary(
                accession, project_data, pubmed_ids
            )

            # Fetch SRA metadata if available
            if sra_ids:
                sra_metadata = await self._fetch_sra_metadata(sra_ids[:100])  # Limit
                metadata["experiments"] = sra_metadata.get("experiments", [])
                metadata["samples"] = sra_metadata.get("samples", [])
                metadata["runs"] = sra_metadata.get("runs", [])

            metadata["raw_metadata"] = {
                "bioproject_summary": project_data,
                "bioproject_uid": bioproject_uid,
            }

            logger.info(
                "bioproject_fetched",
                accession=accession,
                pubmed_count=len(pubmed_ids),
                sra_count=len(sra_ids),
            )

            return metadata

        except NCBIError:
            raise
        except Exception as e:
            raise RetrievalError(f"Failed to fetch BioProject: {e}") from e

    def _parse_bioproject_summary(
        self,
        accession: str,
        data: dict[str, Any],
        pubmed_ids: list[str],
    ) -> dict[str, Any]:
        """Parse BioProject summary into metadata dict.

        Args:
            accession: BioProject accession.
            data: Summary data from NCBI.
            pubmed_ids: Linked PubMed IDs.

        Returns:
            Parsed metadata dictionary.
        """
        # Parse dates
        submission_date = None
        release_date = None

        if "project_acc_registration_date" in data:
            try:
                submission_date = date.fromisoformat(
                    data["project_acc_registration_date"].split("T")[0]
                )
            except (ValueError, AttributeError):
                pass

        return {
            "accession": accession,
            "title": data.get("project_title"),
            "description": data.get("project_description"),
            "organism": data.get("organism_name"),
            "taxon_id": data.get("organism_taxid"),
            "submission_date": submission_date,
            "release_date": release_date,
            "data_type": data.get("project_data_type"),
            "scope": data.get("project_scope"),
            "organization": data.get("submitter_organization"),
            "submitter": data.get("submitter_name"),
            "linked_pubmed_ids": pubmed_ids,
            "experiments": [],
            "samples": [],
            "runs": [],
        }

    async def _fetch_sra_metadata(
        self, sra_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch SRA metadata for linked experiments.

        Args:
            sra_ids: List of SRA UIDs.

        Returns:
            Dictionary with experiments, samples, and runs.
        """
        if not sra_ids:
            return {"experiments": [], "samples": [], "runs": []}

        try:
            # Fetch SRA XML
            xml_content = await self.client.efetch(
                db="sra",
                ids=sra_ids,
                rettype="xml",
            )

            if not isinstance(xml_content, str):
                return {"experiments": [], "samples": [], "runs": []}

            return self._parse_sra_xml(xml_content)

        except Exception as e:
            logger.warning("sra_fetch_failed", error=str(e))
            return {"experiments": [], "samples": [], "runs": []}

    def _parse_sra_xml(self, xml_content: str) -> dict[str, list[dict[str, Any]]]:
        """Parse SRA XML response.

        Args:
            xml_content: XML string from NCBI.

        Returns:
            Parsed experiments, samples, and runs.
        """
        experiments = []
        samples = []
        runs = []
        seen_experiments = set()
        seen_samples = set()

        try:
            root = ET.fromstring(xml_content)

            for exp_pkg in root.findall(".//EXPERIMENT_PACKAGE"):
                # Parse experiment
                exp_elem = exp_pkg.find("EXPERIMENT")
                if exp_elem is not None:
                    exp_acc = exp_elem.get("accession", "")
                    if exp_acc and exp_acc not in seen_experiments:
                        seen_experiments.add(exp_acc)
                        experiments.append(self._parse_experiment(exp_elem))

                # Parse sample
                sample_elem = exp_pkg.find("SAMPLE")
                if sample_elem is not None:
                    sample_acc = sample_elem.get("accession", "")
                    if sample_acc and sample_acc not in seen_samples:
                        seen_samples.add(sample_acc)
                        samples.append(self._parse_sample(sample_elem))

                # Parse runs
                for run_elem in exp_pkg.findall(".//RUN"):
                    runs.append(self._parse_run(run_elem, exp_elem, sample_elem))

        except ET.ParseError as e:
            logger.warning("sra_xml_parse_error", error=str(e))

        return {"experiments": experiments, "samples": samples, "runs": runs}

    def _parse_experiment(self, elem: ET.Element) -> dict[str, Any]:
        """Parse an SRA experiment element."""
        design = elem.find("DESIGN")
        lib_desc = design.find("LIBRARY_DESCRIPTOR") if design is not None else None

        platform_elem = elem.find("PLATFORM")
        platform = None
        instrument = None
        if platform_elem is not None:
            for child in platform_elem:
                platform = child.tag
                instrument = child.findtext("INSTRUMENT_MODEL")
                break

        return {
            "accession": elem.get("accession", ""),
            "title": elem.findtext("TITLE"),
            "library_strategy": lib_desc.findtext("LIBRARY_STRATEGY") if lib_desc else None,
            "library_source": lib_desc.findtext("LIBRARY_SOURCE") if lib_desc else None,
            "library_selection": lib_desc.findtext("LIBRARY_SELECTION") if lib_desc else None,
            "library_layout": (
                "PAIRED" if lib_desc is not None and lib_desc.find("LIBRARY_LAYOUT/PAIRED") is not None
                else "SINGLE" if lib_desc is not None else None
            ),
            "platform": platform,
            "instrument_model": instrument,
        }

    def _parse_sample(self, elem: ET.Element) -> dict[str, Any]:
        """Parse an SRA sample element."""
        attributes = {}
        for attr in elem.findall(".//SAMPLE_ATTRIBUTE"):
            tag = attr.findtext("TAG", "").strip()
            value = attr.findtext("VALUE", "").strip()
            if tag and value:
                attributes[tag] = value

        # Get BioSample accession from identifiers
        biosample_acc = None
        for ext_id in elem.findall(".//EXTERNAL_ID"):
            if ext_id.get("namespace") == "BioSample":
                biosample_acc = ext_id.text
                break

        return {
            "accession": elem.get("accession", ""),
            "biosample_accession": biosample_acc,
            "title": elem.findtext("TITLE"),
            "organism": elem.findtext(".//SCIENTIFIC_NAME"),
            "taxon_id": int(elem.findtext(".//TAXON_ID") or 0) or None,
            "attributes": attributes,
        }

    def _parse_run(
        self,
        run_elem: ET.Element,
        exp_elem: ET.Element | None,
        sample_elem: ET.Element | None,
    ) -> dict[str, Any]:
        """Parse an SRA run element."""
        return {
            "accession": run_elem.get("accession", ""),
            "experiment_accession": exp_elem.get("accession", "") if exp_elem is not None else "",
            "sample_accession": sample_elem.get("accession", "") if sample_elem is not None else "",
            "total_spots": int(run_elem.get("total_spots", 0)) or None,
            "total_bases": int(run_elem.get("total_bases", 0)) or None,
            "size": int(run_elem.get("size", 0)) or None,
        }

    async def to_pydantic(self, identifier: str) -> BioProjectMetadata:
        """Fetch and return as Pydantic model.

        Args:
            identifier: BioProject accession.

        Returns:
            BioProjectMetadata model.
        """
        data = await self.fetch_metadata(identifier)

        return BioProjectMetadata(
            accession=data["accession"],
            title=data.get("title"),
            description=data.get("description"),
            organism=data.get("organism"),
            taxon_id=data.get("taxon_id"),
            submission_date=data.get("submission_date"),
            release_date=data.get("release_date"),
            data_type=data.get("data_type"),
            scope=data.get("scope"),
            organization=data.get("organization"),
            submitter=data.get("submitter"),
            linked_pubmed_ids=data.get("linked_pubmed_ids", []),
            experiments=[SRAExperiment(**e) for e in data.get("experiments", [])],
            samples=[SRASample(**s) for s in data.get("samples", [])],
            runs=[SRARun(**r) for r in data.get("runs", [])],
            raw_metadata=data.get("raw_metadata", {}),
        )
