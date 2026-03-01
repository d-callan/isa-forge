"""Mock NCBI API responses for testing.

These fixtures are based on real NCBI API responses but simplified for testing.
"""

# BioProject search response
BIOPROJECT_SEARCH_RESPONSE = {
    "header": {
        "type": "esearch",
        "version": "0.3"
    },
    "esearchresult": {
        "count": "1",
        "retmax": "1",
        "retstart": "0",
        "idlist": ["13"],
        "translationset": [],
        "querytranslation": "PRJNA13[BioProject Accession]"
    }
}

# BioProject summary response
BIOPROJECT_SUMMARY_RESPONSE = {
    "header": {
        "type": "esummary",
        "version": "0.3"
    },
    "result": {
        "uids": ["13"],
        "13": {
            "uid": "13",
            "project_acc": "PRJNA13",
            "project_id": 13,
            "project_type": "Primary submission",
            "project_target_scope": "Monoisolate",
            "project_target_material": "Genome",
            "project_target_capture": "Whole",
            "project_methodtype": "Sequencing",
            "project_datatype": "Genome sequencing",
            "project_title": "Escherichia coli K-12 substr. MG1655",
            "project_description": "Escherichia coli K-12 is the most extensively studied bacterial organism. The complete genome sequence was published in 1997.",
            "organism_name": "Escherichia coli str. K-12 substr. MG1655",
            "organism_taxid": 511145,
            "organism_strain": "K-12",
            "organism_label": "Escherichia coli K-12",
            "registration_date": "2002/11/07 00:00",
            "modification_date": "2023/05/15 00:00"
        }
    }
}

# PubMed search response
PUBMED_SEARCH_RESPONSE = {
    "header": {
        "type": "esearch",
        "version": "0.3"
    },
    "esearchresult": {
        "count": "2",
        "retmax": "2",
        "retstart": "0",
        "idlist": ["12163470", "15822210"],
        "translationset": [],
        "querytranslation": "CRISPR"
    }
}

# PubMed article response (efetch XML parsed)
PUBMED_ARTICLE_RESPONSE = {
    "pmid": "12163470",
    "title": "Identification of genes that are associated with DNA repeats in prokaryotes",
    "abstract": "A novel family of repeats, called clustered regularly interspaced short palindromic repeats (CRISPR), was identified in prokaryotic genomes. These repeats are found in many bacterial and archaeal species.",
    "authors": [
        {
            "name": "Jansen R",
            "affiliation": "Department of Molecular Microbiology, Utrecht University, Netherlands"
        },
        {
            "name": "Embden JD",
            "affiliation": "Department of Molecular Microbiology, Utrecht University, Netherlands"
        },
        {
            "name": "Gaastra W",
            "affiliation": "Department of Molecular Microbiology, Utrecht University, Netherlands"
        },
        {
            "name": "Schouls LM",
            "affiliation": "Laboratory for Infectious Diseases and Perinatal Screening, Netherlands"
        }
    ],
    "journal": "Molecular Microbiology",
    "publication_date": "2002-03-01",
    "doi": "10.1046/j.1365-2958.2002.02839.x",
    "volume": "43",
    "issue": "6",
    "pages": "1565-1575",
    "pmcid": None,
    "full_text": None
}

# Multiple PubMed articles
PUBMED_MULTIPLE_RESPONSE = [
    PUBMED_ARTICLE_RESPONSE,
    {
        "pmid": "15822210",
        "title": "CRISPR provides acquired resistance against viruses in prokaryotes",
        "abstract": "Clustered regularly interspaced short palindromic repeats (CRISPR) provide acquired immunity against viruses in prokaryotes.",
        "authors": [
            {"name": "Barrangou R", "affiliation": "Danisco USA Inc"},
            {"name": "Fremaux C", "affiliation": "Danisco France SAS"},
        ],
        "journal": "Science",
        "publication_date": "2007-03-23",
        "doi": "10.1126/science.1138140",
        "volume": "315",
        "issue": "5819",
        "pages": "1709-1712",
        "pmcid": None,
        "full_text": None
    }
]

# Linked PubMed IDs response (elink returns a list of linksets)
LINKED_PUBMED_RESPONSE = [
    {
        "dbfrom": "bioproject",
        "ids": ["13"],
        "linksetdbs": [
            {
                "dbto": "pubmed",
                "linkname": "bioproject_pubmed",
                "links": [{"id": "12345678"}, {"id": "87654321"}]
            }
        ]
    }
]

# SRA experiment data (from BioProject)
SRA_EXPERIMENT_DATA = {
    "accession": "SRX123456",
    "title": "RNA-Seq of E. coli K-12",
    "library_strategy": "RNA-Seq",
    "library_source": "TRANSCRIPTOMIC",
    "library_selection": "cDNA",
    "library_layout": "PAIRED",
    "platform": "ILLUMINA",
    "instrument_model": "Illumina HiSeq 2500",
    "design_description": "Transcriptome sequencing of E. coli K-12 under standard growth conditions"
}

# SRA sample data
SRA_SAMPLE_DATA = {
    "accession": "SRS123456",
    "title": "E. coli K-12 sample 1",
    "organism": "Escherichia coli str. K-12 substr. MG1655",
    "taxon_id": 511145,
    "attributes": {
        "strain": "K-12",
        "tissue": "bacterial culture",
        "growth_condition": "LB medium, 37C"
    }
}

# SRA run data
SRA_RUN_DATA = {
    "accession": "SRR123456",
    "total_spots": 25000000,
    "total_bases": 5000000000,
    "size": 2500000000,
    "published": "2023-01-15"
}

# Full BioProject metadata with SRA
BIOPROJECT_FULL_METADATA = {
    "accession": "PRJNA13",
    "title": "Escherichia coli K-12 substr. MG1655",
    "description": "Escherichia coli K-12 is the most extensively studied bacterial organism. The complete genome sequence was published in 1997.",
    "organism": "Escherichia coli str. K-12 substr. MG1655",
    "taxon_id": 511145,
    "project_type": "Primary submission",
    "submission_date": "2002-11-07",
    "modification_date": "2023-05-15",
    "linked_pubmed_ids": [],
    "experiments": [SRA_EXPERIMENT_DATA],
    "samples": [SRA_SAMPLE_DATA],
    "runs": [SRA_RUN_DATA]
}
