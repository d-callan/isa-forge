"""Investigation file (i_investigation.txt) builder."""

from isaforge.models.isa import Investigation
from isaforge.isa_builder.formatter import ISATabFormatter


class InvestigationBuilder:
    """Builder for i_investigation.txt files."""

    def build(self, investigation: Investigation) -> str:
        """Build investigation file content.

        Args:
            investigation: The Investigation model.

        Returns:
            ISA-Tab formatted investigation file content.
        """
        lines = []

        # ONTOLOGY SOURCE REFERENCE section
        lines.append("ONTOLOGY SOURCE REFERENCE")
        lines.append(ISATabFormatter.format_row(
            "Term Source Name",
            *[osr.name for osr in investigation.ontology_source_references]
        ))
        lines.append(ISATabFormatter.format_row(
            "Term Source File",
            *[osr.file or "" for osr in investigation.ontology_source_references]
        ))
        lines.append(ISATabFormatter.format_row(
            "Term Source Version",
            *[osr.version or "" for osr in investigation.ontology_source_references]
        ))
        lines.append(ISATabFormatter.format_row(
            "Term Source Description",
            *[osr.description or "" for osr in investigation.ontology_source_references]
        ))

        # INVESTIGATION section
        lines.append("INVESTIGATION")
        lines.append(ISATabFormatter.format_field("Investigation Identifier", investigation.identifier))
        lines.append(ISATabFormatter.format_field("Investigation Title", investigation.title))
        lines.append(ISATabFormatter.format_field("Investigation Description", investigation.description or ""))
        lines.append(ISATabFormatter.format_field("Investigation Submission Date", investigation.submission_date or ""))
        lines.append(ISATabFormatter.format_field("Investigation Public Release Date", investigation.public_release_date or ""))

        # INVESTIGATION PUBLICATIONS
        lines.append("INVESTIGATION PUBLICATIONS")
        lines.append(ISATabFormatter.format_row(
            "Investigation PubMed ID",
            *[pub.pubmed_id or "" for pub in investigation.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Publication DOI",
            *[pub.doi or "" for pub in investigation.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Publication Author List",
            *[pub.author_list or "" for pub in investigation.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Publication Title",
            *[pub.title or "" for pub in investigation.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Publication Status",
            *[pub.status or "" for pub in investigation.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Publication Status Term Accession Number",
            *[pub.status_term_accession or "" for pub in investigation.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Publication Status Term Source REF",
            *[pub.status_term_source or "" for pub in investigation.publications]
        ))

        # INVESTIGATION CONTACTS
        lines.append("INVESTIGATION CONTACTS")
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Last Name",
            *[c.last_name for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person First Name",
            *[c.first_name or "" for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Mid Initials",
            *[c.mid_initials or "" for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Email",
            *[c.email or "" for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Phone",
            *[c.phone or "" for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Fax",
            *[c.fax or "" for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Address",
            *[c.address or "" for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Affiliation",
            *[c.affiliation or "" for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Roles",
            *[";".join(c.roles) for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Roles Term Accession Number",
            *[";".join(c.roles_term_accessions) for c in investigation.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Investigation Person Roles Term Source REF",
            *[";".join(c.roles_term_sources) for c in investigation.contacts]
        ))

        # STUDY sections for each study
        for study in investigation.studies:
            lines.extend(self._build_study_section(study))

        return "\n".join(lines)

    def _build_study_section(self, study) -> list[str]:
        """Build the STUDY section for a study.

        Args:
            study: The Study model.

        Returns:
            List of lines for the study section.
        """
        lines = []

        # STUDY
        lines.append("STUDY")
        lines.append(ISATabFormatter.format_field("Study Identifier", study.identifier))
        lines.append(ISATabFormatter.format_field("Study Title", study.title))
        lines.append(ISATabFormatter.format_field("Study Description", study.description or ""))
        lines.append(ISATabFormatter.format_field("Study Submission Date", study.submission_date or ""))
        lines.append(ISATabFormatter.format_field("Study Public Release Date", study.public_release_date or ""))
        lines.append(ISATabFormatter.format_field("Study File Name", study.filename))

        # STUDY DESIGN DESCRIPTORS
        lines.append("STUDY DESIGN DESCRIPTORS")
        lines.append(ISATabFormatter.format_row(
            "Study Design Type",
            *[d.design_type for d in study.design_descriptors]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Design Type Term Accession Number",
            *[d.design_type_term_accession or "" for d in study.design_descriptors]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Design Type Term Source REF",
            *[d.design_type_term_source or "" for d in study.design_descriptors]
        ))

        # STUDY PUBLICATIONS
        lines.append("STUDY PUBLICATIONS")
        lines.append(ISATabFormatter.format_row(
            "Study PubMed ID",
            *[pub.pubmed_id or "" for pub in study.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Publication DOI",
            *[pub.doi or "" for pub in study.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Publication Author List",
            *[pub.author_list or "" for pub in study.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Publication Title",
            *[pub.title or "" for pub in study.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Publication Status",
            *[pub.status or "" for pub in study.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Publication Status Term Accession Number",
            *[pub.status_term_accession or "" for pub in study.publications]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Publication Status Term Source REF",
            *[pub.status_term_source or "" for pub in study.publications]
        ))

        # STUDY FACTORS
        lines.append("STUDY FACTORS")
        lines.append(ISATabFormatter.format_row(
            "Study Factor Name",
            *[f.name for f in study.factors]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Factor Type",
            *[f.factor_type for f in study.factors]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Factor Type Term Accession Number",
            *[f.factor_type_term_accession or "" for f in study.factors]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Factor Type Term Source REF",
            *[f.factor_type_term_source or "" for f in study.factors]
        ))

        # STUDY ASSAYS
        lines.append("STUDY ASSAYS")
        lines.append(ISATabFormatter.format_row(
            "Study Assay File Name",
            *[a.filename for a in study.assays]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Assay Measurement Type",
            *[a.measurement_type for a in study.assays]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Assay Measurement Type Term Accession Number",
            *[a.measurement_type_term_accession or "" for a in study.assays]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Assay Measurement Type Term Source REF",
            *[a.measurement_type_term_source or "" for a in study.assays]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Assay Technology Type",
            *[a.technology_type for a in study.assays]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Assay Technology Type Term Accession Number",
            *[a.technology_type_term_accession or "" for a in study.assays]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Assay Technology Type Term Source REF",
            *[a.technology_type_term_source or "" for a in study.assays]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Assay Technology Platform",
            *[a.technology_platform or "" for a in study.assays]
        ))

        # STUDY PROTOCOLS
        lines.append("STUDY PROTOCOLS")
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Name",
            *[p.name for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Type",
            *[p.protocol_type for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Type Term Accession Number",
            *[p.protocol_type_term_accession or "" for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Type Term Source REF",
            *[p.protocol_type_term_source or "" for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Description",
            *[p.description or "" for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol URI",
            *[p.uri or "" for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Version",
            *[p.version or "" for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Parameters Name",
            *[";".join(param.name for param in p.parameters) for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Components Name",
            *[";".join(c.name for c in p.components) for p in study.protocols]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Protocol Components Type",
            *[";".join(c.component_type or "" for c in p.components) for p in study.protocols]
        ))

        # STUDY CONTACTS
        lines.append("STUDY CONTACTS")
        lines.append(ISATabFormatter.format_row(
            "Study Person Last Name",
            *[c.last_name for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person First Name",
            *[c.first_name or "" for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Mid Initials",
            *[c.mid_initials or "" for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Email",
            *[c.email or "" for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Phone",
            *[c.phone or "" for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Fax",
            *[c.fax or "" for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Address",
            *[c.address or "" for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Affiliation",
            *[c.affiliation or "" for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Roles",
            *[";".join(c.roles) for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Roles Term Accession Number",
            *[";".join(c.roles_term_accessions) for c in study.contacts]
        ))
        lines.append(ISATabFormatter.format_row(
            "Study Person Roles Term Source REF",
            *[";".join(c.roles_term_sources) for c in study.contacts]
        ))

        return lines
