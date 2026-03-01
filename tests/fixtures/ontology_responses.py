"""Mock ontology service API responses for testing.

These fixtures are based on real OLS and Zooma API responses but simplified for testing.
"""

from isaforge.models.metadata.ontology import OntologyTerm, OntologyMapping

# OLS search response for "liver"
OLS_LIVER_TERMS = [
    OntologyTerm(
        label="liver",
        term_id="UBERON:0002107",
        ontology="UBERON",
        iri="http://purl.obolibrary.org/obo/UBERON_0002107",
        description="A large organ in the body that cleans the blood and aids in digestion by secreting bile.",
        synonyms=["hepatic tissue", "hepar"]
    ),
    OntologyTerm(
        label="liver cell",
        term_id="CL:0000182",
        ontology="CL",
        iri="http://purl.obolibrary.org/obo/CL_0000182",
        description="A cell of the liver.",
        synonyms=["hepatocyte"]
    ),
]

# OLS search response for "RNA-Seq"
OLS_RNASEQ_TERMS = [
    OntologyTerm(
        label="RNA sequencing assay",
        term_id="OBI:0001271",
        ontology="OBI",
        iri="http://purl.obolibrary.org/obo/OBI_0001271",
        description="A transcription profiling assay that uses RNA-Seq technology.",
        synonyms=["RNA-seq", "RNA sequencing", "whole transcriptome shotgun sequencing"]
    ),
    OntologyTerm(
        label="transcription profiling by high throughput sequencing",
        term_id="EFO:0008896",
        ontology="EFO",
        iri="http://www.ebi.ac.uk/efo/EFO_0008896",
        description="A transcription profiling assay using high throughput sequencing.",
        synonyms=["RNA-seq"]
    ),
]

# OLS get term by ID response
OLS_TERM_LIVER = OntologyTerm(
    label="liver",
    term_id="UBERON:0002107",
    ontology="UBERON",
    iri="http://purl.obolibrary.org/obo/UBERON_0002107",
    description="A large organ in the body that cleans the blood and aids in digestion by secreting bile.",
    synonyms=["hepatic tissue", "hepar"]
)

# Zooma search response for "liver"
ZOOMA_LIVER_TERMS = [
    OntologyTerm(
        label="liver",
        term_id="UBERON:0002107",
        ontology="UBERON",
        iri="http://purl.obolibrary.org/obo/UBERON_0002107",
        description="liver tissue",
        synonyms=[]
    ),
]

# Zooma annotate with confidence response
ZOOMA_CONFIDENCE_RESULTS = [
    {
        "term": OntologyTerm(
            label="liver",
            term_id="UBERON:0002107",
            ontology="UBERON",
            iri="http://purl.obolibrary.org/obo/UBERON_0002107",
            description="liver tissue",
            synonyms=[]
        ),
        "confidence": 0.95
    },
]

# Ontology mapping result for "liver"
MAPPER_LIVER_RESULT = OntologyMapping(
    source_text="liver",
    mapped_term=OntologyTerm(
        label="liver",
        term_id="UBERON:0002107",
        ontology="UBERON",
        iri="http://purl.obolibrary.org/obo/UBERON_0002107",
        description="A large organ in the body that cleans the blood and aids in digestion by secreting bile.",
        synonyms=["hepatic tissue", "hepar"]
    ),
    confidence=0.95,
    mapping_source="ols",
    justification="Exact match found in UBERON ontology",
    alternatives=[
        OntologyTerm(
            label="liver cell",
            term_id="CL:0000182",
            ontology="CL",
            iri="http://purl.obolibrary.org/obo/CL_0000182",
            description="A cell of the liver.",
            synonyms=["hepatocyte"]
        ),
    ]
)

# Batch mapping results
MAPPER_BATCH_RESULTS = {
    "liver": OntologyMapping(
        source_text="liver",
        mapped_term=OLS_TERM_LIVER,
        confidence=0.95,
        mapping_source="ols",
        justification="Exact match in UBERON"
    ),
    "kidney": OntologyMapping(
        source_text="kidney",
        mapped_term=OntologyTerm(
            label="kidney",
            term_id="UBERON:0002113",
            ontology="UBERON",
            iri="http://purl.obolibrary.org/obo/UBERON_0002113",
            description="A paired organ that filters blood and produces urine.",
            synonyms=["renal organ"]
        ),
        confidence=0.95,
        mapping_source="ols",
        justification="Exact match in UBERON"
    ),
}

# Custom term fallback result
MAPPER_CUSTOM_TERM_RESULT = OntologyMapping(
    source_text="super rare tissue type xyz123",
    mapped_term=OntologyTerm(
        label="super rare tissue type xyz123",
        term_id="CUSTOM:000001",
        ontology="CUSTOM",
        iri=None,
        description="Custom term created for unmapped value",
        synonyms=[],
        is_custom=True
    ),
    confidence=0.5,
    mapping_source="custom",
    justification="No suitable ontology term found, created custom term",
    alternatives=[]
)
