# GOaudit: release-aware taxonomic quality control for Gene Ontology annotations in non-model organisms

> **Draft status:** Launch draft for a BMC Bioinformatics Software article, 29 July 2026. This version establishes the argument, article structure, principal case study, figures and tables. Bracketed text identifies author decisions or analyses still required. It is not submission-ready.

## Title page

**Title:** GOaudit: release-aware taxonomic quality control for Gene Ontology annotations in non-model organisms

**Running title:** Taxonomic quality control of GO annotations

**Authors:** Andy Bachler<sup>1,\*</sup>, [co-authors]

**Affiliations:**  
<sup>1</sup>[Department, institution, city, state, country]  
<sup>\*</sup>Correspondence: [email]

## Abstract

### Background

Automated genome annotation increasingly combines orthology transfer, protein signatures and machine-learning prediction to assign Gene Ontology (GO) terms to non-model organisms. Although useful, confidence scores and credible homologues do not establish that every GO term is compatible with the target organism. GO provides formal taxon constraints, but applying them to arbitrary annotation tables requires reconciling ontology releases, identifiers and the target taxon's complete lineage.

### Results

We developed GOaudit, a dependency-free Python command-line tool that audits precomputed protein–GO associations against the official GO computed taxon constraints and NCBI Taxonomy. GOaudit accepts a deliberately strict two-column table and an NCBI taxon identifier, then reports a decision and reason for every association. It resolves alternative GO identifiers, separates obsolete and unknown terms from taxon violations, records reference URLs and checksums, produces summary statistics and plots, and can write a taxon-filtered table without changing the underlying protein annotations.

We evaluated GOaudit on GO predictions generated for the 32,879-protein RefSeq proteome of the reef-building coral *Stylophora pistillata*. DeepGOPlus assigned 1,095,349 protein–GO associations with combined scores of at least 0.30. GOaudit identified 8,316 associations (0.759%) that were incompatible with the coral lineage under the 15 June 2026 GO release, representing 1,202 GO terms and affecting 1,285 proteins; 2,306 retained scores of at least 0.65. Frequent findings included circulatory system, inflammatory response, brain, blood vessel and heart development terms restricted to Bilateria, Vertebrata or Chordata. Matched InterProScan and eggNOG-mapper runs on the same proteome provided protein-signature and orthology controls. A matrix of eggNOG-mapper options showed that neither annotation scope nor hit stringency altered the taxon-violation rate, which remained between 4.6% and 5.1%; only restricting donor taxa removed violations entirely, and it reduced annotated proteins from 14,571 to 164. That taxonomically clean configuration added little information, as 82.3% of its proteins were already annotated by InterProScan and only 9.6% of its associations were both novel and specific.

### Conclusions

GOaudit adds a small, source-independent quality-control step between GO term generation and biological interpretation. It does not assess homology, retrain prediction models or replace annotation tools; it identifies the narrower class of associations that conflict with a stated organism and a dated GO constraint release. The coral case shows that this check remains useful for high-scoring predictions from modern automated workflows, and that it is most necessary precisely where upstream taxonomic controls are unavailable or, as the eggNOG-mapper matrix demonstrates, effective only at a coverage cost most projects will not accept.

**Keywords:** Gene Ontology; taxon constraints; functional annotation; non-model organism; protein function prediction; annotation quality control; DeepGOPlus; coral

# Background

Genome annotation has become increasingly effective at moving from a protein sequence to a set of plausible functions. Orthology-based tools such as eggNOG-mapper transfer functional information from fine-grained orthologues [1, 2]. InterProScan links protein signatures and domain models to curated functional annotations [3, 4], while phylogeny-aware approaches such as TreeGrafter place query proteins within annotated family trees [5]. More recent predictors use convolutional networks, protein language models, ontology structure or protein structure to assign GO terms when close experimental annotations are unavailable [6–9]. These methods differ in evidence and intended use, but their results converge on the same downstream object: a list of identifiers associated with GO terms.

This convergence allows annotations from different sources to be combined for enrichment, comparative genomics and organism-specific annotation resources. It can also hide an important distinction. Evidence that two proteins are related, or that a model strongly favours a GO label, is not evidence that the biological process described by that label can occur in the target lineage. The difference matters most for non-model organisms, where functional interpretation is transferred across evolutionary distance and where tissue, organ and developmental terms may be poorly represented in training or reference data.

GO provides a formal mechanism for describing these boundaries. Taxon constraints state that a term is applicable only within a taxonomic group (`in_taxon`) or is prohibited within one (`never_in_taxon`) [10]. A term restricted to Vertebrata is not applicable to a coral; a term prohibited in Metazoa is likewise incompatible. These rules support ontology development and GO annotation quality control [10, 11], but their existence does not mean that a table produced by an external workflow has been checked against the current constraints for its intended organism.

Several taxon-aware systems already exist, and GOaudit should be positioned alongside rather than above them (Table 1). The GO rules framework and Ontobio validate structured GO association records for contributors to GO [12]. The Ontology Access Kit (OAK) computes inherited taxon constraints for individual ontology terms and so provides the programmatic building blocks for an equivalent audit, but does not itself validate a protein–GO table against a declared target taxon [13]. FunTaxIS-lite generates taxon-specific prohibited-term sets by combining GO constraints with manually curated and annotation-distribution-derived rules [14, 15]. Argot2.5 and PANNZER incorporate taxonomic information within their own prediction workflows [16, 17], and GAEF evaluates coherence and consistency of genome-scale functional annotations [18]. These tools are more comprehensive in particular settings. The gap addressed here is narrower: a researcher has already obtained protein–GO associations and needs a small, reproducible check for a declared organism before those terms enter downstream analysis.

An important practical asymmetry motivates a post-hoc check. The annotation routes that expose explicit taxonomic controls are not the routes that contribute most of the annotation. eggNOG-mapper allows the donor pool to be restricted by taxon; InterProScan and current sequence-based predictors offer no equivalent control, because a protein signature or a learned label carries no notion of which lineage the query belongs to. Upstream configuration therefore cannot protect the majority of a typical non-model-organism annotation set, and we quantify this asymmetry below.

Here, we present GOaudit, a release-aware command-line tool for applying GO taxon constraints directly to simple protein–GO tables. We use the reef-building coral *Stylophora pistillata* as a case study and a current DeepGOPlus model as the principal stress test. The central question is deliberately simple: after an annotation method has generated its predictions, which individual GO associations are compatible with the complete NCBI lineage of the target organism?

## Table 1. Position of GOaudit among related taxon-aware approaches

| Approach | Primary input and setting | Taxonomic policy | Main output | Relationship to GOaudit |
|---|---|---|---|---|
| GO rules / Ontobio | Structured GAF/GPAD, for GO data production | Official GO rules and external inference | Rule-level validation reports | Broader and authoritative; needs richer records and GO-production context |
| OAK | Ontology terms via a general CLI or Python interface | Computes inherited `only_in`/`never_in` constraints from the ontology graph and NCBI Taxonomy | Term-level constraint records | Supplies the core building blocks; the user must still add lineage comparison, the row join and audit outputs |
| FunTaxIS-lite | Taxon-specific prohibited-term list generation | GO constraints plus manual and annotation-distribution-derived rules | Extended prohibited-term lists | Broader constraint discovery; GOaudit applies only released official constraints |
| Argot2.5 / PANNZER | Sequences submitted to the predictor | Predictor-specific taxonomic filters | Taxon-filtered predictions | Upstream and predictor-specific; GOaudit is post hoc and source-independent |
| GAEF | Genome-scale annotation sets | Coherence, completeness and consistency checks | Multi-dimensional assessment | Broader evaluation; GOaudit answers one target-taxon question |
| **GOaudit** | Two-column protein–GO table plus NCBI taxid | Dated official GO computed constraints against the full target lineage | Association-level audit, summaries, plots, optional filtered table | Lightweight final checkpoint for arbitrary precomputed annotations |

# Implementation

## Software design and user interface

GOaudit version 0.1.0 is implemented in Python 3.10 or later using only the standard library. The command-line interface contains five operations: `update`, `validate`, `convert-eggnog`, `convert-interpro` and `prepare-orgdb`. The central `validate` command requires a tab-separated file with exactly two columns, `protein_id` and `go_id`, and one protein–GO association per row; a header is optional. Additional columns, comma-separated GO lists and malformed GO identifiers are rejected. This restriction keeps each row unambiguous and makes input problems visible before filtering.

The converter commands expand the GO fields of standard eggNOG-mapper and InterProScan outputs into that representation. They are conveniences, not annotation methods: any workflow able to write the two required columns can be audited.

The default `report` mode does not alter annotations. It writes:

- `audit.tsv`, containing the canonical GO identifier, term name, namespace, status, applicable constraint and human-readable reason for every input row;
- `summary.tsv` and `summary.json`, containing dataset and decision counts;
- plots showing status, namespace and frequent taxon violations; and
- `reference_manifest.json`, preserving the exact reference-data provenance.

The optional `flag` mode adds status and reason columns to the input associations. The `remove` mode writes a new two-column table excluding taxon violations. Obsolete and unknown identifiers are reported but retained by this mode, because ontology-version maintenance and taxonomic filtering are distinct decisions. GOaudit therefore remains report-first: researchers can inspect a constraint, identify upstream ontology or taxonomy edge cases and decide when exclusion is appropriate.

## Reference data and provenance

`goaudit update` downloads the GO ontology, computed taxon constraints and taxon groupings, together with NCBI Taxonomy nodes, scientific names, merged taxon identifiers and deleted identifiers, recording each with its source URL, retrieval timestamp and SHA-256 checksum. Reference data are held outside the Python package so that installation remains small and a project can pin, archive or update its own bundle.

This separation matters for reproducibility. GO terms become obsolete, alternative identifiers are consolidated, taxonomic nodes are merged and constraints are revised. A result such as "8,316 associations were incompatible" is therefore meaningful only alongside the GO release, NCBI taxon identifier, GOaudit version and validation mode used to obtain it.

## Identifier and taxon resolution

GOaudit parses the target taxon's complete lineage from NCBI Taxonomy. A supplied taxon identifier that has been merged is resolved to its current identifier, while deleted or unknown taxon identifiers cause validation to stop. GO alternative identifiers are resolved to their current primary term. Obsolete GO terms and identifiers absent from the selected ontology release receive separate statuses rather than being silently discarded or treated as taxon violations.

For each current term, GOaudit evaluates the constraints materialized in GO's computed constraint file. An `in_taxon` condition passes when the required group occurs in the target lineage. A `never_in_taxon` condition fails when the prohibited group occurs in the lineage. GO taxon grouping classes are expanded from the released grouping file. The result records the exact relation, constraint taxon and target-lineage comparison responsible for the decision.

## Optional protein-to-gene preparation

The core audit acts on the identifiers supplied by the user and does not assume that protein and gene identifiers are interchangeable. The optional `prepare-orgdb` command validates an EGAPx/RefSeq-style GFF3 protein-to-gene hierarchy and writes tables suitable for `AnnotationForge::makeOrgPackage()`, failing on ambiguous assignments. This workflow is ancillary to the audit and is documented in Supplementary File S3.

## Test organism and protein function prediction

The principal case study used the RefSeq proteome for *S. pistillata* assembly GCF_002571385.2 (NCBI taxid 50429), containing 32,879 protein sequences. [Add the primary assembly citation if one is available.] DeepGOPlus 1.0.2 was run with model bundle 1.0.28, released 14 June 2026. The bundle used the 19 May 2026 GO release and Swiss-Prot 2026_02 and modelled 5,692 GO terms.

DeepGOPlus combines a convolutional neural network with annotation transfer from DIAMOND sequence matches [6]. It should therefore be described as a hybrid machine-learning and similarity method, rather than a homology-free predictor. Its combined scores are propagated to GO ancestors before thresholding. Predictions with scores of at least 0.30 were retained, matching the threshold shown in the DeepGOWeb application programming interface example at the time of analysis. The complete command, environment, source checksums and conversion scripts are preserved in the benchmark directory.

The resulting three-column table (`protein_id`, `go_id`, `score`) was retained for analysis. Its first two columns were supplied unchanged to GOaudit 0.1.0 using the GO release dated 15 June 2026. Scores were then joined back to the association-level audit by the protein–GO key. Exact identifier equivalence between the input proteome and raw DeepGOPlus output was confirmed before validation.

## Workflow controls and comparisons

The DeepGOPlus run is intended as a stress test of modern automated prediction, not a comparison of biological accuracy among annotation methods. Two widely used annotation workflows were run on the identical 32,879-protein FASTA to assess whether GOaudit could accept GO tables produced through different evidence strategies.

InterProScan 5.72-103.0 scanned the sequences locally against its 22 enabled signature libraries, disabled the precalculated-match service and requested GO cross-references with `--goterms`. The native TSV retained whether each cross-reference came from InterPro or PANTHER.

eggNOG-mapper 2.1.12 with eggNOG 5.0.2 was run as a matched option matrix, because its taxonomic controls are optional and their effect on both coverage and formal compatibility is the quantity of interest. Two DIAMOND searches were performed on the same FASTA: one using eggNOG-mapper's own defaults with no score or coverage filtering, and one applying stringent hit filtering (E-value ≤1×10<sup>-10</sup>, bit score ≥60, identity ≥40%, query and subject coverage ≥50%). Eight annotation passes then reused these seed-ortholog tables through `-m no_search`, so that search stringency and annotation-donor policy vary independently. The passes spanned the tool's documented defaults (`--tax_scope auto`, `--tax_scope_mode inner_narrowest`, `--go_evidence non-electronic`, unrestricted donors); admission of electronically inferred terms (`--go_evidence all`); a Metazoa annotation scope without donor restriction; donors restricted to non-bilaterian Metazoa (`--target_taxa 33208 --excluded_taxa 33213`); and donors restricted to Cnidaria (`--target_taxa 6073`) under both evidence policies. All native outputs were converted to one protein–GO association per row and audited with the same GOaudit code and 15 June 2026 GO/NCBI reference snapshot used for DeepGOPlus.

To assess how much information a taxonomically well-configured orthology run contributes beyond protein-signature annotation, the donor-restricted eggNOG-mapper output was compared with the InterProScan output on the same proteins. Because eggNOG-mapper propagates GO ancestors while InterProScan reports signature-level mappings, exact protein–GO pair matching understates agreement. Overlap was therefore also computed under ancestor closure over `is_a` and `part_of`: an eggNOG-mapper association was counted as already covered when its term was an ancestor or a descendant of an InterProScan term on the same protein. Specificity of the remaining eggNOG-mapper-only associations was summarized by ontology depth, defined as the shortest `is_a`/`part_of` path from the namespace root, with depth ≥5 used as a pragmatic threshold for a term specific enough to support biological interpretation.

These comparisons measure output scale, coverage, information contribution and formal taxon compatibility; they do not estimate the biological precision or recall of the annotators. The tools use different databases, evidence filters, propagation policies and release dates, so a lower violation count is not an accuracy ranking. RefSeq GO associations for the same assembly provide an additional reference-workflow control.

Direct software comparisons address a separate question: whether a researcher can apply the same check with existing taxon-aware utilities. The submission version should report the input conversion, setup burden, reference release, association-level agreement, runtime and output provenance for GOaudit, Ontobio and FunTaxIS-lite on a small frozen multi-taxon fixture. “More terms removed” must not be used as a measure of correctness because FunTaxIS-lite deliberately applies a broader policy than official GO constraints.

## Software verification and resource use

The repository contains unit and integration tests for taxon constraints, merged NCBI taxon identifiers, alternative and obsolete GO identifiers, strict input parsing, converters, report generation, EGAPx/RefSeq GFF3 mapping and DeepGOPlus output conversion. All 16 tests passed under Python 3.11.0, 3.12.3, 3.13.12 and 3.14.2 on SUSE Linux Enterprise High Performance Computing 15 SP5. The full DeepGOPlus run completed in 28 min 2 s on 16 allocated CPUs and used approximately 4.02 GB maximum resident memory; most of that cost belongs to function prediction rather than GOaudit. On the same compute system, GOaudit validated the complete 1,095,349-row DeepGOPlus table in 19.46 s on one CPU with a peak resident memory of 479,812 kB (approximately 469 MB). The complete eggNOG-mapper option matrix, comprising two DIAMOND searches and eight annotation passes with a GOaudit run after each, completed in 53 min 17 s on 16 allocated CPUs. Resource use for each annotation control was recorded separately.

# Results

## GOaudit produced a complete, inspectable decision table

GOaudit read the DeepGOPlus associations without requiring model-specific metadata. The audit retained the input protein–GO key and added the current term name, namespace, decision status and exact taxonomic reason. This separation allowed a taxon-incompatible term to be excluded without rejecting the protein sequence, the DIAMOND match, the neural-network output or compatible GO terms assigned to the same protein (Figure 1).

Across the 32,879 input proteins, DeepGOPlus assigned at least one GO term with score ≥0.30 to 31,035 proteins (94.392%). The output contained 1,095,349 protein–GO associations and 10,799 unique GO identifiers. GOaudit classified 1,087,006 associations as current and taxonomically compatible. A further 27 associations used six obsolete GO identifiers, no identifiers were unknown and no alternative identifiers occurred in this model output (Table 2).

## Taxon-incompatible predictions affected 1,285 coral proteins

GOaudit identified 8,316 protein–GO associations (0.759%) that conflicted with the *S. pistillata* lineage. The findings comprised 1,202 distinct GO terms and affected 1,285 proteins, corresponding to 4.140% of proteins with at least one DeepGOPlus prediction and 3.908% of all input proteins. Biological-process terms accounted for 8,121 violations (97.65%), compared with 178 cellular-component and 17 molecular-function associations.

The most frequent incompatible annotations were not borderline differences in terminology. They described circulatory system development, inflammatory response, central nervous system development, head development, vasculature, brain, blood vessel and heart development (Table 3; Figure 2). The largest constraint categories were Vertebrata (4,554 associations), Bilateria (1,383), Chordata (394), Gnathostomata (325), Viridiplantae (271), Craniata (197), Arthropoda (171) and Insecta (168). A further 85 associations violated a `never_in_taxon Metazoa` constraint.

These findings arose from the frozen full-proteome benchmark rather than from a preselected sentinel term. They included many independent bilaterian-, vertebrate-, plant-, arthropod- and bacterial-restricted annotations.

## High-scoring predictions still required taxonomic review

Applying increasingly stringent DeepGOPlus score thresholds reduced the number of reported associations but did not monotonically reduce the fraction of taxon violations (Figure 3; Supplementary Table S1). At scores ≥0.40, 3,225 of 712,875 associations (0.452%) were incompatible. At scores ≥0.60, 2,361 of 331,926 (0.711%) were incompatible, and 2,306 incompatible associations remained among the 270,955 predictions with scores ≥0.65 (0.851%). No incompatible association had a score ≥0.70 in this model release.

These values should not be interpreted as a calibration analysis. DeepGOPlus scores combine neural-network and sequence-similarity components and are propagated over GO ancestry; they are not direct probabilities that an association is biologically true. The result instead demonstrates that confidence thresholding and taxon validation answer different questions. A threshold controls how strongly the predictor supports its own label, whereas GOaudit tests whether the label is compatible with the declared organism under the selected ontology release.

## Protein-signature annotation covered most of the proteome

InterProScan assigned 95,381 associations to 23,338 proteins (71.0% of the proteome), using 5,375 unique GO terms. Of these, 248 associations (0.260%) across 212 proteins and 72 terms were flagged as taxon-incompatible, and 2,414 associations used terms obsolete in the 15 June 2026 GO release (Table 4). In the native InterProScan TSV, 212 flagged associations carried only a PANTHER-source GO label, 35 only an InterPro-source label and one both. The largest constraint groups were Vertebrata (118 associations), Bilateria (48) and Bacteria (37); the last of these arose from a `syntaxin binding` constraint discussed below.

## eggNOG-mapper taxonomic controls traded coverage against compatibility

The eggNOG-mapper option matrix separated the effects of hit stringency, annotation scope and donor restriction on the same proteome (Table 5). Default search settings returned seed orthologs for 28,670 proteins; the stringent filter returned 15,848, a 44.7% reduction. The earlier benchmark's `--score 40 --query_cover 20 --subject_cover 20` filter returned 28,252, within 1.5% of no filtering at all, and so had almost no effect on which proteins entered annotation.

Run with its own defaults, eggNOG-mapper annotated 14,571 proteins (44.3% of the proteome) with 2,160,345 associations across 20,541 unique GO terms. GOaudit flagged 110,903 of these associations (5.134%) as incompatible with the coral lineage, and a further 328,694 (15.2%) used obsolete terms. As with DeepGOPlus, the incompatible terms were not marginal: circulatory system development (1,797 associations), central nervous system development (1,505), head development (1,262), brain development (1,186) and chordate embryonic development (988) were the most frequent, and the constraint groups were led by Vertebrata (47,464), Bilateria (17,630) and Insecta (8,056). Insect-specific terms such as imaginal disc development (733) and instar larval or pupal development (718) appeared among the ten most frequent findings.

Two configurations that might reasonably be assumed to address this did not. Setting a Metazoa annotation scope without restricting donors left both coverage and compatibility essentially unchanged (14,606 proteins; 4.898% incompatible). Stringent hit filtering was applied hard — it removed 44.7% of seed orthologs and a third of the annotated proteins (9,595; 29.2% of the proteome) — yet reduced the violation rate only from 5.134% to 4.648%. Admitting electronically inferred terms increased coverage to 15,893 proteins without materially changing the violation rate (4.802%). Alignment stringency establishes that a match is real; it carries no information about whether the matched protein's function is transferable to the target lineage.

Only donor restriction eliminated taxon violations, and it did so at a severe cost to coverage. Restricting donors to non-bilaterian Metazoa produced zero violations but annotated 164 proteins (0.499%), an 89-fold reduction relative to defaults. Cnidaria-only donors gave 156 proteins with all evidence and 112 with non-electronic evidence, likewise with no violations. Combining stringent hits with non-bilaterian donors gave 137 proteins. Every donor-restricted configuration was formally clean and covered under 0.5% of the proteome.

## The taxonomically clean eggNOG configuration added little information

Because the donor-restricted configuration was the only formally compatible one, we asked how much it contributed beyond InterProScan on the same proteins (Table 6). It produced 6,048 usable associations over 164 proteins and 892 unique terms. Of those 164 proteins, 135 (82.3%) were already annotated by InterProScan, leaving 29 proteins unique to eggNOG-mapper.

Exact protein–GO pair agreement was low (385 pairs, 6.4%), but this understates agreement because eggNOG-mapper propagates GO ancestors while InterProScan reports signature-level mappings. Under ancestor closure, 3,347 associations (55.3%) were already implied by an InterProScan term on the same protein. Of the 2,701 remaining eggNOG-mapper-only associations, most were near the ontology roots: only 583 (9.6% of all its usable associations) reached depth ≥5, spanning 190 terms and 104 proteins. Of the 135 proteins annotated by both tools, 58 gained no specific term at all from eggNOG-mapper. Genuinely specific contributions existed — 2',3'-cyclic GMP-AMP synthase activity on 18 proteins, microtubule cytoskeleton on six — but were rare.

The default configuration behaved oppositely. After GOaudit filtering it still contributed 455,913 specific (depth ≥5) associations not implied by InterProScan, across 12,991 proteins, including 1,697 proteins InterProScan did not annotate at all. The coverage that orthology transfer can add to a non-model proteome is therefore real and large, but under these releases it is available only in the configuration that also generates a 5% taxon-incompatible fraction.

## Table 2. DeepGOPlus–GOaudit case-study summary

| Measure | Result |
|---|---:|
| Input proteins | 32,879 |
| Proteins with ≥1 prediction at score ≥0.30 | 31,035 (94.392%) |
| Protein–GO associations | 1,095,349 |
| Unique GO terms | 10,799 |
| Current, taxonomically compatible associations | 1,087,006 |
| Taxon-incompatible associations | 8,316 (0.759%) |
| Unique taxon-incompatible GO terms | 1,202 |
| Proteins with ≥1 incompatible association | 1,285 |
| Affected fraction of annotated proteins | 4.140% |
| Obsolete associations | 27 across 6 terms |
| Unknown GO identifiers | 0 |
| Associations retained after taxon filtering | 1,087,033 |

## Table 3. Ten most frequent taxon-incompatible DeepGOPlus annotations

| GO term | Description | Associations | Maximum score | Restriction |
|---|---|---:|---:|---|
| `GO:0072359` | circulatory system development | 286 | 0.687 | in Bilateria |
| `GO:0006954` | inflammatory response | 214 | 0.666 | in Vertebrata |
| `GO:0007417` | central nervous system development | 201 | 0.669 | in Bilateria |
| `GO:0060322` | head development | 141 | 0.664 | in Bilateria |
| `GO:0001944` | vasculature development | 136 | 0.668 | in Vertebrata |
| `GO:0007420` | brain development | 123 | 0.660 | in Bilateria |
| `GO:0001568` | blood vessel development | 121 | 0.667 | in Vertebrata |
| `GO:0007507` | heart development | 112 | 0.674 | in Bilateria |
| `GO:0043009` | chordate embryonic development | 107 | 0.665 | in Chordata |
| `GO:0048514` | blood vessel morphogenesis | 103 | 0.666 | in Vertebrata |

## Table 4. Matched annotation-workflow controls on the *S. pistillata* proteome

All three workflows were applied to the identical 32,879-protein RefSeq FASTA and audited against the 15 June 2026 GO release for NCBI taxid 50429. eggNOG-mapper is shown in its default configuration and in the taxonomically restricted configuration; the full option matrix is given in Table 5.

| Annotation workflow | Evidence strategy and configuration | Proteins with GO terms | Protein–GO associations | Taxon-incompatible associations | Obsolete associations |
|---|---|---:|---:|---:|---:|
| DeepGOPlus 1.0.2 | Hybrid CNN and DIAMOND transfer; score ≥0.30 | 31,035 | 1,095,349 | 8,316 (0.759%) | 27 |
| InterProScan 5.72-103.0 | 22 signature libraries; InterProScan GO cross-references | 23,338 | 95,381 | 248 (0.260%) | 2,414 |
| eggNOG-mapper 2.1.12, defaults | Orthology transfer; unrestricted donors | 14,571 | 2,160,345 | 110,903 (5.134%) | 328,694 |
| eggNOG-mapper 2.1.12, restricted | Orthology transfer; Metazoa donors excluding Bilateria; all GO evidence | 164 | 8,155 | 0 (0%) | 1,990 |

## Table 5. eggNOG-mapper option matrix on the *S. pistillata* proteome

Two DIAMOND searches were performed on the same FASTA; all annotation passes reused a seed-ortholog table through `-m no_search`, so search stringency and donor policy vary independently. Percentages are of the 32,879 input proteins (coverage) and of each run's own associations (violations). Machine-readable form: `tables/table_5_eggnog_option_matrix.tsv`.

| Search | Annotation options | Proteins with GO terms | Proteome coverage | Associations | Unique GO terms | Taxon-incompatible | Obsolete |
|---|---|---:|---:|---:|---:|---:|---:|
| Defaults | eggNOG-mapper defaults (`--tax_scope auto`, non-electronic) | 14,571 | 44.32% | 2,160,345 | 20,541 | 110,903 (5.134%) | 328,694 |
| Defaults | `--go_evidence all` | 15,893 | 48.34% | 2,353,479 | 21,022 | 113,013 (4.802%) | 368,014 |
| Defaults | `--tax_scope Metazoa`, donors unrestricted, all evidence | 14,606 | 44.42% | 2,235,546 | 20,522 | 109,490 (4.898%) | 347,677 |
| Defaults | Donors Metazoa excluding Bilateria, all evidence | 164 | 0.50% | 8,155 | 1,062 | 0 (0%) | 1,990 |
| Defaults | Donors Cnidaria, all evidence | 156 | 0.47% | 7,705 | 1,008 | 0 (0%) | 1,866 |
| Defaults | Donors Cnidaria, non-electronic | 112 | 0.34% | 3,633 | 764 | 0 (0%) | 926 |
| Stringent | eggNOG-mapper default annotation policy | 9,595 | 29.18% | 1,432,157 | 19,344 | 66,570 (4.648%) | 226,354 |
| Stringent | Donors Metazoa excluding Bilateria, all evidence | 137 | 0.42% | 6,852 | 1,029 | 0 (0%) | 1,807 |

## Table 6. Information contributed by eggNOG-mapper beyond InterProScan

Usable associations only (GOaudit status `valid` or `alternate_id`). Coverage under ancestor closure counts an eggNOG-mapper association as already present when its term is an ancestor or descendant of an InterProScan term on the same protein. Depth is the shortest `is_a`/`part_of` path from the namespace root.

| Measure | Restricted donors | Defaults |
|---|---:|---:|
| Usable eggNOG-mapper associations | 6,048 | 1,683,713 |
| Proteins annotated | 164 | 14,571 |
| Unique GO terms | 892 | 15,400 |
| Proteins also annotated by InterProScan | 135 (82.3%) | 12,874 (88.4%) |
| Proteins not annotated by InterProScan | 29 | 1,697 |
| Exact protein–GO pair overlap | 385 (6.4%) | 42,028 (2.5%) |
| Already implied under ancestor closure | 3,347 (55.3%) | 363,687 (21.6%) |
| eggNOG-mapper-only associations | 2,701 (44.7%) | 1,320,026 (78.4%) |
| eggNOG-mapper-only and specific (depth ≥5) | 583 (9.6%) | 455,913 (27.1%) |
| Proteins receiving a specific novel term | 104 | 12,991 |
| Shared proteins gaining nothing specific | 58 of 135 | 1,371 of 12,874 |

# Discussion

## A final checkpoint for heterogeneous annotation workflows

The main value of GOaudit is not a new biological rule. It is the reduction of a formal but awkward quality-control task to a small, inspectable workflow that can sit after almost any annotation method. Researchers working on non-model organisms commonly combine orthology, domains, curated mappings and prediction models. Requiring each upstream method to expose the same taxonomic controls is unrealistic, and restricting analysis to a single annotation ecosystem discards complementary evidence.

The coral case illustrates why this checkpoint is useful. Only 0.759% of DeepGOPlus association rows violated a constraint, so most predictions passed. The affected rows were nevertheless distributed across 1,285 proteins and included specific developmental and immune terms that would be conspicuous in enrichment or comparative analyses. Automated interpretation is vulnerable to exactly this combination: a small subset of implausible but highly specific terms can attract more attention than a much larger background of compatible, general ones.

GOaudit is intentionally association-preserving. It does not claim that the sequence match, protein family or model is wrong. If a protein has 50 GO associations and one is incompatible with the target lineage, only that association is flagged, avoiding an overcorrection in which a single problematic term discards otherwise useful evidence.

## Confidence and taxonomy are orthogonal quality dimensions

The high-scoring DeepGOPlus findings provide the clearest justification for the tool. A model can be confident according to its learned labels and similarity evidence while still returning a term outside the target lineage. This is not surprising: taxon compatibility is a constraint on the meaning of the output, not necessarily an objective optimized by the predictor. The result argues for reporting both score thresholds and taxonomic validation rather than treating one as a substitute for the other.

Ancestor propagation deserves care. DeepGOPlus propagates predictions through the GO hierarchy, so the 1.095 million association rows are not independent claims, and a constrained ancestral term can appear on many proteins through the structure of the output alone. GOaudit reports at the association level because those are the rows used downstream, but papers should also report unique terms and affected proteins, as done here.

## Comparison across annotation workflows

The matched analyses demonstrate that GOaudit can consume outputs from three common but methodologically different routes to GO annotation: orthology transfer, protein-signature matching and a hybrid machine-learning/similarity predictor. They also expose a structural problem that post-hoc auditing is well placed to address.

eggNOG-mapper is the only one of the three that offers explicit taxonomic controls, and those controls work: with donors restricted to non-bilaterian Metazoa, the run produced no taxon violations at all. The option matrix also shows how narrowly they work. Neither a Metazoa annotation scope nor stringent hit filtering materially changed the violation rate, which stayed between 4.6% and 5.1% across every configuration that did not restrict donors, even though stringent filtering discarded 44.7% of seed orthologs. A user who sets `--tax_scope Metazoa` and a bit-score threshold, and who reasonably believes they have run the tool "properly for a coral", obtains almost exactly the violation rate of the untouched defaults. Only `--target_taxa`/`--excluded_taxa` changed the outcome, and only by reducing annotated proteins from 14,571 to 164.

This leaves a genuine dilemma rather than a clean recommendation. The donor-restricted configuration is formally clean but contributes little: 82.3% of its proteins were already annotated by InterProScan, 55.3% of its associations were already implied under ancestor closure, and only 9.6% were both novel and specific enough to interpret. The default configuration is the opposite. Even after filtering, it contributed 455,913 specific associations not implied by InterProScan across 12,991 proteins, including 1,697 proteins InterProScan missed entirely. Orthology transfer can add substantial coverage to a non-model proteome, but under eggNOG 5.0.2 that coverage is available only in the configuration that also produces a 5% taxon-incompatible fraction. The trade-off is a property of donor availability — non-bilaterian metazoan proteins carrying curated GO annotations are sparse — not of the software.

Meanwhile the two workflows that performed most of the annotation, InterProScan and DeepGOPlus, provide no taxonomic control mechanism at all: a signature match and a learned GO label carry no representation of the query's lineage. Configuring eggNOG-mapper carefully therefore protects only whichever part of the annotation set came from eggNOG-mapper. It does nothing for the 23,338 proteins annotated by InterProScan or the 31,035 covered by DeepGOPlus. For those, an external check against the declared organism is the only control available, which is the practical argument for a source-independent audit.

It would nonetheless be a misreading of these results to conclude that upstream configuration can be replaced by permissive annotation followed by GOaudit. Taxon constraints exist for a minority of GO terms, so filtering removes formally incompatible associations while leaving untouched a larger class that is taxonomically permitted but evolutionarily unsupported — a term transferred from a distant bilaterian orthologue with no coral counterpart will typically carry no constraint at all. A default run followed by a taxon audit is therefore not equivalent to a donor-restricted run; the two procedures remove different and only partially overlapping sets of associations, and the 5.134% that GOaudit reports should be read as a detectable lower bound on transfer error, not an estimate of it. What the audit does provide is a reproducible, release-anchored floor beneath a configuration that would otherwise carry tens of thousands of vertebrate, bilaterian and insect developmental terms into a coral annotation set.

Among the InterProScan flags, most were supplied only by PANTHER-labelled mappings, and the set also exposed reference-maintenance questions: the audited GO release constrained `syntaxin binding` to Bacteria even though the term is used in eukaryotic annotations and carries an active ontology tracker item. These associations must therefore be interpreted as review candidates, not demonstrated annotation errors. Differences among the three outputs should not be read as a league table: the workflows differ in coverage, evidence, GO release and propagation, and GOaudit tests only one formal property of their results.

## Comparison with existing software

FunTaxIS-lite is the closest conceptual comparator and provides a light route to taxon-specific functional filtering [14]. Its scope is more ambitious: it extends official GO constraints using manual rules and empirical absences in annotation data, and so may identify implausible terms for which GO has no formal constraint. GOaudit makes the opposite policy choice, applying only dated official constraints, recording the source of every decision and declining to treat an absence of annotation as an impossibility. Neither policy is universally superior, and a comparison should report agreement, release effects and policy-specific findings rather than reward whichever tool removes more terms.

Ontobio and the GO rules framework remain the appropriate choice for complete GO annotation submissions and broader rule conformance. OAK already performs the central ontology operation required here: its `taxon-constraints` command computes inherited constraints for supplied terms when the ontology resource includes NCBI Taxonomy. An equivalent audit could be constructed by querying each distinct term, resolving the target lineage, evaluating the returned constraints and joining decisions back to the input rows; OAK does not package those steps as a protein–GO-table validator, and its `apply-taxon-constraints` command tests candidate ontology constraints rather than applying existing ones to annotation rows. GOaudit's contribution is consequently workflow-level rather than algorithmic. This usability claim should be supported with a frozen, same-release benchmark rather than asserted from feature lists alone.

## Limitations

GOaudit detects only constraints encoded in the selected GO release, and taxon constraints exist for a minority of GO terms. A term that is biologically implausible for the target organism but carries no formal constraint will pass. This is the most important limit on what a taxon audit can achieve, and it is why the audit complements rather than replaces appropriate upstream configuration. Conversely, ontology and taxonomy resources can contain mistakes or temporary inconsistencies, so a reported violation is a reproducible reason for review rather than proof that the input biology is wrong. The default mode accordingly removes nothing, and every output retains the constraint and release provenance.

The strict two-column format does not preserve annotation source, evidence code or confidence. This simplicity aids interoperability but limits source-specific comparisons after datasets are merged; users should retain the original outputs, command lines and model/database versions, as was done here for the scored DeepGOPlus table.

The biological case study uses one coral proteome, and the ontology-depth threshold used to summarize annotation specificity is a pragmatic convention rather than a standard measure. The InterProScan control used the complete archived release installed on the compute cluster (5.72-103.0), not the latest release available at the time of writing, so its counts should not be extrapolated to newer versions. Likewise, the eggNOG-mapper coverage results reflect the taxonomic composition of eggNOG 5.0.2, in which non-bilaterian metazoan donors carrying curated GO annotations are sparse; a future eggNOG release with denser cnidarian annotation would shift the coverage-versus-compatibility trade-off reported here. Before submission, a compact multi-taxon conformance suite spanning bacteria, plants, fungi, arthropods, vertebrates and cnidarians should test semantic agreement among GOaudit and official constraint-aware tooling on the same frozen releases.

Finally, GOaudit checks GO annotations rather than the underlying gene models. Chimeric, fragmented or otherwise incorrect proteins can still receive taxonomically valid GO terms [19]. Protein-model quality, annotation evidence, taxonomic compatibility and downstream enrichment design are related but distinct quality-control layers.

## Recommended use

A conservative workflow is:

1. configure each annotation method as well as its own options allow, including taxonomic scope and donor controls where the tool provides them;
2. preserve the original output, evidence, scores, command line and database/model releases;
3. convert associations to one protein–GO pair per row;
4. run GOaudit in `report` mode with the intended organism's NCBI taxid;
5. inspect recurrent or high-impact violations and possible upstream resource issues;
6. use `remove` mode only after review; and
7. retain the GOaudit manifest and use the same pre- and post-filter gene universe for downstream comparisons.

Step 1 is deliberately first. GOaudit is a checkpoint, not a licence to annotate permissively and filter afterwards, and the eggNOG-mapper matrix reported here shows why the distinction matters: donor restriction and taxon auditing remove different sets of associations, and only the former addresses annotations that are taxonomically permitted but evolutionarily unsupported. Where a tool offers no taxonomic control — as is the case for protein-signature and current sequence-based prediction methods — the audit is the only control available, and that is the setting in which it contributes most.

# Conclusions

GOaudit makes one formal quality-control question easy to ask of any GO annotation table: are these terms compatible with this organism under this release of GO? Applied to current DeepGOPlus predictions for *S. pistillata*, the tool identified 8,316 incompatible protein–GO associations, including 2,306 with scores of at least 0.65. These findings do not invalidate the predictor or the proteins. They show that prediction confidence, homology support and taxonomic applicability are separate properties.

For non-model-organism projects, a small final audit can prevent lineage-specific terms from becoming prominent biological conclusions while retaining the large majority of useful annotation. GOaudit provides that checkpoint through a strict input contract, association-level explanations and reference provenance, and is intended to complement rather than replace established annotation and ontology software.

# Availability and requirements

- **Project name:** GOaudit
- **Project home page:** https://github.com/Andy-B-123/GOaudit
- **Operating system(s):** Linux (tested on SUSE Linux Enterprise High Performance Computing 15 SP5); the standard-library implementation is designed to be portable
- **Programming language:** Python 3.10 or later
- **Other requirements:** Internet access for initial GO and NCBI reference download; no Python runtime dependencies
- **License:** MIT
- **Any restrictions to use by non-academics:** None

# List of abbreviations

**CNN:** convolutional neural network; **GAF:** Gene Association File; **GO:** Gene Ontology; **GFF3:** General Feature Format version 3; **NCBI:** National Center for Biotechnology Information; **OAK:** Ontology Access Kit; **OrgDb:** organism annotation database; **QC:** quality control.

# Declarations

## Ethics approval and consent to participate

Not applicable.

## Consent for publication

Not applicable.

## Availability of data and materials

GOaudit source code, tests, examples and benchmark workflows are available at https://github.com/Andy-B-123/GOaudit under the MIT licence. The *S. pistillata* RefSeq proteome, GAF and GFF3 are available from NCBI under assembly accession GCF_002571385.2. The DeepGOPlus model bundle, exact reference URLs, checksums, commands and derived summary files are documented in the repository, together with the matched eggNOG-mapper and InterProScan commands and resource-use records. [Before submission: create an immutable software release and archive it with Zenodo; deposit the minimum derived scored/audit tables or a compact reproducible fixture; replace repository URLs in the manuscript with numbered references and add the DOI.]

## Competing interests

The authors declare that they have no competing interests. [Confirm for all authors.]

## Funding

[List funding bodies, grant numbers and the role of each funder. If none: “This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.”]

## Authors' contributions

AB conceived the study, developed the software, performed the analyses and drafted the manuscript. [Add co-author contributions using initials and the CRediT taxonomy where helpful.] All authors read and approved the final manuscript.

## Acknowledgements

[Add people who tested the software, provided annotation advice or contributed resources but do not meet authorship criteria. Obtain permission before naming them. If none: “Not applicable.”]

## Authors' information

[Optional.]

# Figures and legends

## Figure 1. GOaudit adds a release-aware checkpoint between GO term generation and interpretation

Orthology transfer, protein-signature annotation and machine-learning prediction are reduced to a strict table containing one protein–GO association per row. GOaudit resolves the complete NCBI lineage of the target taxon and applies a dated release of the official GO computed constraints. It returns a decision and reason for every row, summary statistics, plots and an optional table in which only taxon violations are removed. Annotation evidence and the original protein assignment remain unchanged.

File: `figures/figure1_workflow.svg`

## Figure 2. Frequent taxon-incompatible DeepGOPlus predictions for *Stylophora pistillata*

**A:** Ten most frequent taxon-incompatible GO terms among predictions with DeepGOPlus score ≥0.30. **B:** The eight most frequent constraint taxa responsible for incompatible associations. Bars count protein–GO associations after DeepGOPlus propagation to GO ancestors. Restriction categories are not mutually exclusive at the biological level, but each plotted row records the constraint reported for its GOaudit decision.

File: `figures/figure2_deepgoplus_violations.svg`

## Figure 3. DeepGOPlus score thresholding does not substitute for a taxon audit

Bars show the number of taxon-incompatible associations retained at each minimum DeepGOPlus score; the line shows their percentage among all retained protein–GO associations. A total of 2,306 incompatible associations remained at score ≥0.65. No incompatible association scored ≥0.70 in this model release. Scores combine CNN and sequence-similarity components and are propagated to GO ancestors; the graph is not a calibration analysis.

File: `figures/figure3_score_thresholds.svg`

# Supplementary material scaffold

## Supplementary Table S1. Score-threshold sensitivity analysis

See `tables/table_s1_score_thresholds.tsv`.

## Supplementary Table S2. Reproducibility manifest for the coral case study

See `tables/table_s2_reproducibility_manifest.tsv`.

## Supplementary Table S3. Constraint taxa represented in the DeepGOPlus audit

See `tables/table_s3_constraint_taxa.tsv`.

## Supplementary Table S4. Source of InterProScan taxon-constraint flags

See `tables/table_s4_interpro_violation_sources.tsv`.

## Supplementary Table S5. eggNOG-mapper-only GO terms not implied by InterProScan

Terms contributed by the donor-restricted eggNOG-mapper run that were neither ancestors nor descendants of an InterProScan term on the same protein, with ontology depth and protein counts. See `tables/table_s5_eggnog_only_terms.tsv`.

## Supplementary File S1. Frozen multi-taxon conformance fixture

[To build before submission. Include explicit valid and invalid associations for multiple taxonomic lineages, expected decisions, a frozen constraint release and agreement results for comparator tools.]

## Supplementary File S2. Source archive

[At submission, attach an archive of the tagged source release as recommended by BMC Bioinformatics, even though the canonical development repository remains online.]

## Supplementary File S3. Optional OrgDb preparation workflow

Documentation for `goaudit prepare-orgdb`, covering the required EGAPx/RefSeq GFF3 schema, protein-to-gene mapping QC, combined-source validation and construction of a Bioconductor `OrgDb` with `AnnotationForge`. See `docs/orgdb-workflow.md` in the source repository.

# References

1. Huerta-Cepas J, Forslund K, Coelho LP, Szklarczyk D, Jensen LJ, von Mering C, Bork P. Fast genome-wide functional annotation through orthology assignment by eggNOG-mapper. Mol Biol Evol. 2017;34:2115–2122. doi:10.1093/molbev/msx148.
2. Cantalapiedra CP, Hernández-Plaza A, Letunic I, Bork P, Huerta-Cepas J. eggNOG-mapper v2: functional annotation, orthology assignments, and domain prediction at the metagenomic scale. Mol Biol Evol. 2021;38:5825–5829. doi:10.1093/molbev/msab293.
3. Jones P, Binns D, Chang HY, Fraser M, Li W, McAnulla C, et al. InterProScan 5: genome-scale protein function classification. Bioinformatics. 2014;30:1236–1240. doi:10.1093/bioinformatics/btu031.
4. Blum M, Andreeva A, Florentino LC, Chuguransky SR, Grego T, Hobbs E, et al. InterPro: the protein sequence classification resource in 2025. Nucleic Acids Res. 2025;53:D444–D456. doi:10.1093/nar/gkae1082.
5. Tang H, Finn RD, Thomas PD. TreeGrafter: phylogenetic tree-based annotation of proteins with Gene Ontology terms and other annotations. Bioinformatics. 2019;35:518–520. doi:10.1093/bioinformatics/bty625.
6. Kulmanov M, Hoehndorf R. DeepGOPlus: improved protein function prediction from sequence. Bioinformatics. 2020;36:422–429. doi:10.1093/bioinformatics/btz595.
7. Cao Y, Shen Y. TALE: Transformer-based protein function annotation with joint sequence-label embedding. Bioinformatics. 2021;37:2825–2833. doi:10.1093/bioinformatics/btab198.
8. Kulmanov M, Guzmán-Vega FJ, Duek Roggli P, Lane L, Hoehndorf R. Protein function prediction as approximate semantic entailment. Nat Mach Intell. 2024;6:220–228. doi:10.1038/s42256-024-00795-w.
9. Gligorijević V, Renfrew PD, Kosciolek T, Leman JK, Berenberg D, Vatanen T, et al. Structure-based protein function prediction using graph convolutional networks. Nat Commun. 2021;12:3168. doi:10.1038/s41467-021-23303-9.
10. Deegan JI, Dimmer EC, Mungall CJ. Formalization of taxon-based constraints to detect inconsistencies in annotation and ontology development. BMC Bioinformatics. 2010;11:530. doi:10.1186/1471-2105-11-530.
11. Gene Ontology Consortium. The Gene Ontology knowledgebase in 2026. Nucleic Acids Res. 2026;54:D1779–D1792. doi:10.1093/nar/gkaf1292.
12. Ontobio developers. Ontobio command-line and GO rules documentation. https://ontobio.readthedocs.io/en/latest/commandline.html. Accessed 28 Jul 2026.
13. Ontology Access Kit developers. OAK `taxon-constraints` command and taxon-constraint reporting data model. https://incatools.github.io/ontology-access-kit/cli.html; https://incatools.github.io/ontology-access-kit/datamodels/taxon-constraints/index.html. Accessed 28 Jul 2026.
14. Falda M, Lavezzo E, Fontana P, Bianco L, Berselli M, Formentin E, Toppo S. Eliciting the Functional Taxonomy from protein annotations and taxa. Sci Rep. 2016;6:31971. doi:10.1038/srep31971.
15. Bianca F, Ispano E, Gazzola E, Lavezzo E, Fontana P, Toppo S. FunTaxIS-lite: a simple and light solution to investigate protein functions in all living organisms. Bioinformatics. 2023;39:btad549. doi:10.1093/bioinformatics/btad549.
16. Lavezzo E, Falda M, Fontana P, Bianco L, Toppo S. Enhancing protein function prediction with taxonomic constraints—the Argot2.5 web server. Methods. 2016;93:15–23. doi:10.1016/j.ymeth.2015.08.021.
17. Törönen P, Holm L. PANNZER—a practical tool for protein function prediction. Protein Sci. 2022;31:118–128. doi:10.1002/pro.4193.
18. Tawfiq R, Kulmanov M, Hoehndorf R. Evaluating completeness, coherence, and consistency of genome-scale function annotations. Brief Bioinform. 2026;27:bbag336. doi:10.1093/bib/bbag336.
19. Bachler A, Walsh TK, Rane RV, Pandey G. Chimeric mis-annotations of genes remain pervasive in eukaryotic non-model organisms. BMC Genomics. 2025;26:630. doi:10.1186/s12864-025-11765-w.
