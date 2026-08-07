# GOaudit manuscript draft

> **Current drafting route:** This broad exploratory draft is retained for
> background material. The focused BMC Bioinformatics Software article launch
> draft, DeepGOPlus-centred figures, machine-readable tables and next-session
> brief are in [`manuscript/bmc/`](bmc/README.md).

> Working draft: 14 July 2026. The text below is written as a full software/application article. Square-bracketed text marks information or analyses that still need to be supplied before submission; the numerical results without brackets were calculated from the supplied *Stylophora pistillata* data. DOI links are included during drafting and can later be converted to the target journal's reference style.

## Editorial position

The most defensible paper is not that taxon-aware GO filtering has never been attempted. The Gene Ontology (GO) Consortium uses taxon constraints in its own quality-control system; Ontobio and OWLTools can validate complete GO association records; OmicsBox provides taxon filtering within its annotation environment; and FunTaxIS-lite generates official and data-derived prohibited-term sets. FunTaxIS-lite already supports *Stylophora pistillata* through its Cnidaria reference node, and its public Cnidaria list contains the motivating term GO:0035070. GAEF, published in June 2026, also uses GO taxon constraints within a broader genome-scale consistency framework. The specific gap claimed for GOaudit is therefore narrower and practical: an open, lightweight command-line workflow that applies a dated release of the official constraints directly to heterogeneous, precomputed protein–GO rows, while auditing ontology identifiers and retaining the reference and association-level provenance of every decision.

This scaffold follows the structure of a **BMC Bioinformatics Software article**, with **Bioinformatics Advances** as another sensible venue. It is not yet submission-ready for either route and, in its present one-coral form, is at material risk of being judged a convenient wrapper around an existing rule. BMC Bioinformatics asks software articles to represent a significant advance over related software, usually demonstrated by direct comparison. GOaudit therefore needs a same-release conformance comparison with Ontobio and the official-only mode of FunTaxIS-lite, followed by a full-policy comparison with FunTaxIS-lite, a multi-taxon benchmark, runtime and memory measurements, and a before/after enrichment analysis. These additions are listed under “Work required before submission”.

## Title

**GOaudit: taxonomic quality control for Gene Ontology annotations in non-model organisms**

### Alternative titles

1. **Taxon-incompatible Gene Ontology terms persist in automated annotation of a non-model genome**
2. **A simple taxonomic validation layer for automated Gene Ontology annotation**
3. **GOaudit identifies taxon-constraint violations in automated functional annotations**

### Running title

Taxonomic quality control of GO annotations

## Authors and affiliations

Andreas Bachler^1,*^, [co-authors]

^1^ [Affiliation]

*Correspondence: [email address]

## Abstract

### Background

Functional annotation of non-model organism genomes increasingly relies on automated transfer from homologues, orthologues, protein signatures and learned sequence or structure representations. These approaches provide essential biological coverage, but the resulting Gene Ontology (GO) terms are often passed directly into enrichment and comparative analyses. Some GO terms are only valid within particular lineages. GO supplies formal `in_taxon` and `never_in_taxon` constraints, and several curation, annotation and constraint-generation systems use them. However, an independent, release-auditable check of the flat association tables commonly used by researchers is not yet a routine part of non-model-genome workflows.

### Results

We developed GOaudit, a standard-library-only Python command-line tool that evaluates protein–GO associations against the target organism's complete NCBI taxonomic lineage. GOaudit downloads GO ontology, computed taxon-constraint and taxon-grouping files together with NCBI Taxonomy, records their provenance and checksums, resolves alternative identifiers, reports obsolete and unknown terms separately, and records the status and reason for every input association. The input is deliberately restricted to a two-column protein–GO table, with converters provided for eggNOG-mapper and InterProScan output. Applying GOaudit to eggNOG-mapper annotations for the coral *Stylophora pistillata* identified 90,920 taxon-constraint violations among 1,796,068 protein–GO associations (5.06%). These involved 2,914 unique GO terms and 5,070 of 11,979 annotated proteins (42.3%). A further 274,495 associations used terms obsolete in the 15 June 2026 GO release, while 33,954 associations supplied alternative identifiers that could be resolved. The motivating term, GO:0035070 (`salivary gland histolysis`), occurred on 46 coral proteins despite being restricted to Arthropoda. For one representative protein, this term accompanied a strong eggNOG-mapper seed hit to another cnidarian, demonstrating that a credible orthology result and an inappropriate item of transferred metadata can coexist.

### Conclusions

GOaudit does not predict protein function and a passing result does not prove that an annotation is correct. Instead, it provides a reproducible post-annotation check for a defined class of taxonomic inconsistencies. Removing an incompatible GO association does not require removing the underlying protein hit. This distinction is particularly useful for non-model organisms, where automated annotations are abundant but organism-specific curation remains limited.

**Keywords:** Gene Ontology; taxon constraints; functional annotation; non-model organism; eggNOG-mapper; InterProScan; annotation quality control; coral

## Author summary

Genome annotation tools can assign thousands or millions of GO associations to a non-model organism, but researchers still need a simple way to ask whether each term is biologically compatible with that organism. We encountered this problem when `salivary gland histolysis` was one of the strongest GO results in a coral analysis. The underlying protein match was plausible; the GO association was incompatible with the coral lineage under the selected ontology release. GOaudit adds a small, independent validation step between annotation and interpretation. It reads a two-column protein–GO table and an NCBI taxonomic identifier, checks released GO taxon constraints, and returns an auditable report and optional filtered table. It therefore exposes a clearly defined class of inconsistency without pretending to solve the larger and much harder problem of protein function prediction.

# Background

High-quality genome assemblies are now available for organisms across much of the tree of life. However, the experimental evidence used to interpret these genomes remains concentrated in a comparatively small number of species. This imbalance is especially apparent for non-model organisms, where gene models can be predicted at genome scale but their biological interpretation still depends heavily on information transferred from better characterised proteins. The available tools are remarkably useful: without them, most new genomes would contain thousands of protein-coding genes with little or no functional context. However, the quality of downstream biological inference remains dependent on both the transferred annotation and the assumptions made during that transfer.

The Gene Ontology provides a controlled, species-spanning vocabulary for molecular functions, biological processes and cellular components (Ashburner *et al.*, 2000; Gene Ontology Consortium, 2026a). GO terms are now generated or transferred by a wide range of methods. Orthology-based tools such as eggNOG-mapper infer functional information from fine-grained orthologues (Huerta-Cepas *et al.*, 2017; Cantalapiedra *et al.*, 2021), while similarity-based environments including Blast2GO/OmicsBox and PANNZER score annotations associated with homologous sequences (Conesa *et al.*, 2005; Götz *et al.*, 2008; Törönen *et al.*, 2018). InterProScan assigns curated functional information from protein signatures and domain models (Burge *et al.*, 2012; Jones *et al.*, 2014; Blum *et al.*, 2025, 2026). Phylogeny-aware methods such as TreeGrafter place query sequences onto annotated family trees (Tang *et al.*, 2019), while NetGO combines sequence, similarity, domain, network and protein-language information (Wang *et al.*, 2023). More recently, sequence language models and structure-aware predictors have increased the functions that can be proposed in the absence of a close, experimentally characterised homologue (Kulmanov and Hoehndorf, 2020; Cao and Shen, 2021; Kulmanov *et al.*, 2024; Gligorijević *et al.*, 2021; Wang *et al.*, 2025). Community evaluations demonstrate continuing progress, but also substantial variation among ontology branches, terms and evidence settings (Radivojac *et al.*, 2013; Zhou *et al.*, 2019). These methods differ substantially in their evidence and intended use, but their outputs frequently converge on the same downstream representation: a list of protein or gene identifiers associated with GO terms.

This convergence is convenient, although it can hide important differences in provenance. Curated and rule-based resources such as UniProtKB/GOA and UniRule retain information about evidence and annotation rules (MacDougall *et al.*, 2020; UniProt Consortium, 2025), but a GO term inferred from a curated catalytic signature, transferred from an orthologue, or predicted by a neural network is not supported in the same way. Once the term is reduced to an identifier in a two-column table, evidence codes, source records, confidence values and donor taxa may no longer be available. This is of particular concern in non-model organisms because the final GO table is often used directly to construct gene sets, test enrichment, label expression clusters or compare biological processes among species. An individual annotation error can then be repeated across several downstream results, while an enriched term that is incompatible with the target lineage may appear statistically convincing because it occurs on many proteins.

Annotation errors can propagate through sequence databases and become evidence for subsequent annotations (Gilks *et al.*, 2005; Schnoes *et al.*, 2009). We recently showed an analogous form of annotation inertia for chimeric gene models in eukaryotic non-model organisms, where apparently strong homology could reinforce an incorrect structural annotation (Bachler *et al.*, 2025). Functional annotations create a related problem. Orthology is generally stronger evidence for conserved function than unrestricted sequence similarity, but it does not establish that every biological-process or cellular-component term attached to a donor record is applicable to the recipient organism. A protein can be genuinely homologous, and the selected seed orthologue can be appropriate, while one term within the associated annotation payload describes a lineage-specific tissue, developmental stage or organ that the target organism does not possess.

The GO Consortium has already formalised a biological framework for detecting such inconsistencies. GO terms are intended to be taxon neutral wherever possible, but some functions and processes have implicit taxonomic specificity. Relationships including `in_taxon` and `never_in_taxon` state that a term is restricted to, or excluded from, a particular lineage (Deegan *et al.*, 2010). These constraints are inherited through `is_a` and `part_of` relationships, and GO uses them to detect and filter inconsistent public annotations. Since September 2024, asserted and inferred taxon constraints have been materialised directly on affected terms in the released computed-constraint ontology (Gene Ontology Consortium, 2026b). GO also provides union classes for biologically meaningful groups that cannot be represented as a single NCBI taxonomic clade.

The existence of these constraints does not mean that researchers routinely apply them to their own results. GO's provider-facing validation stack can identify taxon-inappropriate annotation records. Ontobio applies GORULE:0000013 to GAF/GPAD records when the rule and its Gaferencer inference input are supplied; current rule semantics retain experimental violations as warnings but reject non-experimental violations, while negated annotations are exempt (Ontobio developers, 2026a, 2026b). This is appropriate for rich annotation records, but a complete GAF contains 17 fields and requires evidence, references and provenance that are absent from most simplified annotation-tool exports. OWLTools provides related ontology-reasoning and GAF-validation infrastructure. OmicsBox offers a user-facing taxon option during annotation and can filter imported GO annotations within its integrated project environment (OmicsBox, 2026).

FunTaxIS and FunTaxIS-lite address the coverage of the constraint system itself. FunTaxIS-lite combines GOC constraints with manual rules and `never_in` constraints inferred from annotation frequencies and absences, reporting an average threefold extension of GOC coverage (Falda *et al.*, 2016; Bianca *et al.*, 2023). It accepts taxonomic targets, distributes prohibited-term lists through its web interface and local pipeline, and is explicitly intended to filter automatic function predictions. Importantly, the public FunTaxIS-lite service maps *S. pistillata* to a Cnidaria reference node and its Cnidaria list already includes GO:0035070 (FunTaxIS-lite, 2026); the motivating salivary-gland term is therefore not a unique detection capability of GOaudit. Other approaches are complementary: the RAR method identifies empirical taxon-specific annotation outliers from comparative GOA frequencies (Wei *et al.*, 2020), while PANNZER and Argot2.5 apply taxonomic filters within their own prediction workflows (Lavezzo *et al.*, 2016; Törönen and Holm, 2022).

GAEF recently introduced a broader genome-scale framework for completeness, coherence and consistency using GO, GO-Plus, pathway structure and taxon constraints (Tawfiq *et al.*, 2026). Its consistency measure deliberately avoids comparison with a declared target taxon; instead, it asks whether the collection of functions implies mutually compatible taxonomic restrictions. OAK and the QuickGO API can expose taxon constraints programmatically, but leave the association-versus-target-lineage audit to the user. These systems establish substantial prior art. The narrower workflow gap addressed here is the combination of a two-column, source-independent association audit; a user-declared arbitrary NCBI taxid; conservative use of the current official computed constraints and union classes; explicit alternative, obsolete and unknown identifier status; row-level reasons; and a checksummed reference manifest.

Here, we present GOaudit, a deliberately narrow post-annotation quality-control tool. GOaudit asks a single question: is each supplied GO term compatible with the declared taxonomic lineage under the selected official GO release? We demonstrate the tool using automated annotations from the reef-building coral *Stylophora pistillata*. The analysis was motivated by GO:0035070, `salivary gland histolysis`, which appeared prominently in a coral GO analysis even though the term describes the breakdown of larval salivary glands during *Drosophila* metamorphosis and is restricted to Arthropoda. The example motivates the workflow rather than a claim of unique detection. We use it to show that an inappropriate GO association can be identified and removed without rejecting the underlying protein match, and then quantify the same class of inconsistency across the complete annotation set.

## Table 1. Common routes from protein sequence to GO terms, and their relevance to non-model organisms

| Approach | Representative tools or resources | How GO terms arise | Principal strength | Relevant limitation for non-model organisms |
|---|---|---|---|---|
| Orthology transfer | eggNOG-mapper | Functional information is transferred after orthology assignment within a selected taxonomic scope | Fast, scalable and generally more specific than unrestricted best-hit transfer | Restricting the donor lineage does not test whether every GO term attached to an accepted donor is valid in the target lineage |
| Similarity transfer | Blast2GO/OmicsBox; PANNZER | GO terms associated with homologous database sequences are filtered or scored | Broad coverage and accessible workflows | Results depend on donor annotation, database version and user thresholds; similarity alone may not conserve organism-level process or context |
| Protein signatures | InterProScan | Curated InterPro entries and member-database signatures are mapped to GO | Explainable domain- or family-level evidence | Only some signatures have GO mappings; partial and multidomain proteins require care; mappings change between releases |
| Phylogeny-aware transfer | TreeGrafter/PANTHER | Query proteins are placed on annotated family trees | Can separate lineage-specific gains and losses from family-wide function | Dependent on family coverage and the annotations available at internal or terminal nodes |
| Learned sequence prediction | DeepGOPlus; TALE; DeepGO-SE | Models predict GO probabilities using sequence, embeddings and ontology structure | Can propose functions without close homologues | Training-label, calibration, species and ontology-version biases remain; ontology-aware is not necessarily taxon-aware |
| Multimodal prediction | NetGO | Sequence, homology, domains, networks, literature and protein-language representations are combined | Integrates complementary evidence | Many evidence types are sparse or unavailable for newly sequenced organisms |
| Structure-aware prediction | DeepFRI; DPFunc | GO terms are predicted from residue contacts or domain-guided structural representations | Useful for remote relationships, particularly molecular function | Structure alone may not establish a lineage-specific biological process, tissue or cellular context |
| Curated and rule-based reference annotation | UniProtKB/GOA; UniRule/ARBA | Manual curation and automatic annotation rules supply GO associations | Evidence codes and traceable, curated rules | Downstream transfer or simplified export can remove the original provenance; non-model taxa remain less directly characterised |

# Implementation

## Software design and input

GOaudit version 0.1.0 was implemented in Python 3.10 or later using only the Python standard library. The command-line interface provides four principal operations: reference-data update, input conversion, taxonomic validation and preparation of gene-level tables for an optional organism-specific Bioconductor `OrgDb`. The validation input is intentionally strict: a tab-separated file containing exactly two columns, `protein_id` and `go_id`, with one protein–GO association per row. A header is optional. Additional columns, comma-separated GO lists and malformed identifiers are rejected, making the interpretation of each input row unambiguous. Dedicated converters expand the GO columns in standard eggNOG-mapper annotation output and InterProScan TSV output into this representation.

The target organism is supplied as an NCBI Taxonomy identifier. This design is source-agnostic: associations produced by several tools can be concatenated and assessed in a consistent way. It also has a deliberate cost. The minimal format does not preserve evidence codes, donor records or source-specific confidence values unless users archive those original files separately. GOaudit therefore evaluates taxonomic compatibility, not the overall strength of evidence for function.

## Reference data and release provenance

The `goaudit update` command obtains four current reference resources: the GO ontology in OBO format, GO's computed taxon constraints, GO's taxon-grouping definitions, and the NCBI Taxonomy archive (Schoch *et al.*, 2020). From the taxonomy archive, GOaudit retains `nodes.dmp`, `names.dmp` and `merged.dmp`. Reference files are downloaded to a user-selected cache rather than packaged with the software. Each update writes a manifest containing the retrieval time, original URLs and SHA-256 checksum of every retained file. The manifest is copied into each result directory, allowing an analysis to be associated with the exact local reference snapshot.

This separation keeps the Python package small and avoids distributing large or rapidly changing data. It also reflects an important property of the analysis: GO is not static. Terms can be added, merged, redefined or made obsolete, and taxon constraints can be tightened or relaxed. Results should therefore report the GO release, the NCBI taxon, the GOaudit version and the filtering mode. For the analyses described here, reference data were retrieved on 13 July 2026 and the ontology identified itself as `releases/2026-06-15`.

## Resolution of taxonomy and GO identifiers

GOaudit first resolves a supplied taxonomic identifier through NCBI's merged-taxid records and constructs the complete lineage from the target taxon to the taxonomy root. Scientific names are recovered for the target and any constraint taxa used in the report. NCBI taxonomic union classes defined by GO are expanded using the released `go-taxon-groupings.obo` file.

For each input association, the GO identifier is resolved against the selected ontology. Alternative identifiers are mapped to the current primary identifier and reported with an `alternate_id` status. A term explicitly marked obsolete is reported as `obsolete`, together with its replacement where one is provided. An identifier absent from the selected ontology is reported as `unknown_go_term`. These outcomes are kept separate from taxonomic incompatibility because they describe different problems and may require different decisions.

## Taxon-constraint evaluation

GOaudit reads `in_taxon` (RO:0002162) and `never_in_taxon` (RO:0002161) relationships from GO's released computed taxon-constraint file. A `never_in_taxon` constraint is violated when its taxon, or a member of its GO union class, occurs in the target lineage. An `in_taxon` constraint is violated when the required taxon or grouping does not occur in that lineage. As inherited constraints have been materialised on affected terms in GO releases since September 2024, GOaudit uses the released computed relationships rather than attempting to reconstruct propagation over the GO graph.

Each association receives one of five statuses: `valid`, `alternate_id`, `taxon_violation`, `obsolete` or `unknown_go_term`. For a violation, the audit records the canonical GO identifier, term name, namespace, constraint relation, constraint taxon, taxon name and a plain-language explanation. The report therefore identifies the released rule that led to an exclusion rather than inferring incompatibility from the wording of a term. A coral association with `heart development`, for example, is excluded because the selected GO release restricts that term to Bilateria, not because GOaudit searches for anatomical words such as “heart”.

## Output and filtering modes

All runs write a row-level `audit.tsv`, machine- and human-readable summaries, three SVG plots, and the reference manifest. Summary metrics include the number of annotated proteins, annotation rows, unique terms, current valid associations, taxon violations, proteins affected by a violation, obsolete terms, unknown terms and resolved alternative identifiers. The plots show status counts, namespace counts and the most frequent taxon violations.

GOaudit provides `report`, `flag` and `remove` modes. `report` is the default and does not create a filtered annotation set. `flag` appends the status and reason to each association. `remove` writes a two-column table after excluding taxon violations. Obsolete and unknown terms remain in the taxon-filtered table because ontology maintenance and taxon compatibility are separate operations; their status remains available in the audit. Users preparing an `OrgDb` can subsequently retain only `valid` and `alternate_id` records. A pipeline can optionally return a non-zero exit status when any taxon violation is detected.

## EGAPx/RefSeq protein-to-gene validation

GO enrichment is usually performed at gene rather than protein-isoform level, making protein-to-gene mapping a separate source of possible error. The optional `prepare-orgdb` command supports a strict EGAPx/RefSeq-style GFF3 schema. It requires genes with `ID` and `locus_tag`, transcripts or mRNAs with a single gene `Parent`, and CDS features with `protein_id` and transcript `Parent`. Protein identifiers are first matched exactly; the only permitted normalisation removes a pipe-delimited prefix, and this match method is recorded. Ambiguous transcript–gene relationships, protein mappings to more than one gene, identifier collisions and mapping coverage below a user-selected threshold cause the command to fail rather than silently discarding records. The output tables can be supplied to `AnnotationForge::makeOrgPackage()` in R.

## Coral annotation data

The test proteome contained 28,285 predicted proteins from *S. pistillata* [assembly accession, genome version and primary genome citation to add]. Proteins were annotated using eggNOG-mapper 2.1.12 in DIAMOND mode with a database archive dated 31 March 2025. The run used minimum bit score 40, query coverage 20% and subject coverage 20%; otherwise the supplied workflow defaults were retained. The annotation file contained 23,936 query rows, of which 11,979 had at least one GO term. Expansion of comma-separated annotations generated 1,796,068 protein–GO associations.

InterProScan output was also converted and combined with the eggNOG-mapper associations to test a multi-source input. This file contained 27,359 unique queried proteins, including 19,805 with at least one InterPro-derived GO term. [Add the exact InterProScan software and InterPro data releases, command line and member databases before submission.] The combined table contained 1,883,008 associations for 20,746 proteins.

Both datasets were evaluated for *S. pistillata* using NCBI taxid 50429 and the 15 June 2026 GO release. Counts were calculated over associations, unique canonical GO identifiers and unique protein identifiers. Percentages reported here are descriptive; no inferential comparison between annotation tools was attempted because the present case study was not designed as a balanced tool benchmark.

## Verification of the motivating association

GO:0035070 was traced from the GOaudit report to the original eggNOG-mapper annotation and seed-orthologue files. For protein `egapxtmp_003494-P1`, we recorded the selected seed orthologue, alignment E-value, bit score, percentage identity, query coverage, subject coverage, annotation level and number of GO terms in the transferred annotation field. The source taxon of the seed sequence was checked in NCBI Taxonomy. The current meaning and constraint of GO:0035070 were checked in the same GO release used for validation.

## Software testing

The unit-test suite contains 14 tests covering the core coral violation and corresponding arthropod-positive case, alternative and obsolete GO identifiers, unknown identifiers, merged NCBI taxids, strict two-column input, eggNOG-mapper and InterProScan conversion, GFF3 mapping and report generation. [Before submission: add explicit tests for multiple simultaneous constraints and GO union classes, a frozen end-to-end reference fixture, operating systems/Python versions tested, and continuous-integration status.] Runtime and peak memory will be measured on declared hardware using both the small fixture and the full coral dataset.

## AI-assisted manuscript preparation

OpenAI Codex was used to assist with initial manuscript organisation and language drafting. The authors reviewed and revised the resulting text, verified the scientific claims, references and numerical results, and take full responsibility for the final manuscript. [Retain and adapt this statement to the selected journal's current policy.]

# Results

## GOaudit separates annotation generation from taxonomic validation

GOaudit introduces a validation step between functional annotation and biological interpretation (Figure 1). It does not compare protein sequences, infer orthology or assign new biological functions. Instead, it applies released ontology constraints to associations already generated by another method. This distinction matters for interpretation. Annotation tools ask which functions a sequence resembles or is predicted to perform; GOaudit asks whether each resulting GO assertion is compatible with the declared lineage. These questions are related, but they are not equivalent.

The default report preserves the original annotation table and exposes all decisions for review. A user can therefore inspect unusual results before choosing to filter them. This is preferable to treating every violation as proof of a biological error: the finding is formally that an association conflicts with the current GO release. In an unusual case the annotation may reveal a problem with the selected taxid, sample contamination, a mixed-organism dataset or a GO constraint that should be revised. The audit provides the information needed to distinguish these possibilities.

## A strong cnidarian hit carried an arthropod-restricted GO term

GO:0035070 was associated with 46 *S. pistillata* proteins in the eggNOG-mapper output. The term is defined as the stage-specific breakdown of larval salivary glands during *Drosophila* metamorphosis and carries an `in_taxon Arthropoda` constraint. All 46 coral associations were consequently reported as taxon violations.

For `egapxtmp_003494-P1`, eggNOG-mapper selected `45351.EDO45841` from the starlet sea anemone *Nematostella vectensis* (NCBI taxid 45351) as the seed orthologue. This was not a marginal match: the alignment had an E-value of 3.2 × 10<sup>−68</sup>, bit score 221, 45.1% identity, 96.6% query coverage and 98.0% subject coverage. The maximum annotation level was Metazoa and the reported description was chromosome 21 open reading frame 2. However, the associated GO field contained 114 terms, including GO:0035070.

This case demonstrates the central problem clearly. The selected seed came from another cnidarian and the sequence relationship was well supported, yet one item in the annotation payload described arthropod-specific development. Taxonomic restriction of an orthology search can reduce inappropriate donor selection, but it does not establish that every term attached to an accepted donor is applicable to the target lineage. GOaudit removed the association between `egapxtmp_003494-P1` and GO:0035070 in `remove` mode; it did not alter the seed hit, alignment, protein identifier or any compatible GO association.

## Taxon violations were distributed across the coral annotation set

Among 1,796,068 eggNOG-mapper protein–GO associations, 90,920 (5.06%) violated at least one taxon constraint for *S. pistillata* (Table 2). The violations represented 2,914 unique terms, or 14.3% of the 20,339 unique GO identifiers assessed, and affected 5,070 of 11,979 annotated proteins (42.3%). Thus, the row-level fraction was modest relative to the complete annotation table, but the associations were sufficiently distributed to affect almost half of the proteins with an eggNOG-derived GO term.

Biological-process terms accounted for most violations in the combined eggNOG-mapper and InterProScan dataset (89,597 of 91,151; 98.3%), compared with 1,375 cellular-component (1.51%) and 179 molecular-function associations (0.20%). This distribution is biologically plausible because lineage-specific organs, tissues and developmental programmes are predominantly represented as biological processes, whereas many core molecular functions are shared more broadly. However, it should not be interpreted as a general estimate across annotation tools or taxa until a balanced benchmark is performed.

The most frequent incompatible terms illustrate how plausible protein-level signals can acquire organism-level interpretations that do not apply to a coral (Table 3). Terms included `circulatory system development`, `central nervous system development`, `brain development`, `heart development`, `leukocyte activation` and `imaginal disc development`, with constraints ranging from Bilateria to Vertebrata, Chordata, Insecta and Arthropoda. Several are broad parents with many descendants, explaining why a single inappropriate annotation chain can contribute numerous association rows.

## Ontology-version problems were common and distinct from taxon violations

GOaudit classified 274,495 eggNOG-derived associations (15.3%) as obsolete relative to the 15 June 2026 ontology, representing 2,166 unique obsolete identifiers. No identifiers were completely unknown. A further 33,954 associations (1.89%) used an alternative identifier that GOaudit resolved to its current primary term; these records are included among valid rows after resolution. The high obsolete count reflects both the age and composition of the annotation source relative to a period of substantial GO refactoring, and should not be treated as a taxonomic failure. It does, however, show why the ontology version needs to be stated when GO tables are reused.

Combining InterProScan and eggNOG-mapper increased the dataset to 1,883,008 associations across 20,746 proteins. GOaudit identified 91,151 constraint violations (4.84%), affecting 5,175 proteins and 2,920 unique terms. It also reported 277,240 obsolete associations and resolved 36,482 alternative-ID records. The combined analysis demonstrates that the same audit can be applied to a heterogeneous table, but it is not a direct comparison of the two annotation methods because duplicate associations and differences in proteome coverage were not partitioned by source in the minimal input format.

## Strict protein-to-gene mapping produced auditable `OrgDb` inputs

The supplied EGAPx/RefSeq-style GFF3 contained 24,657 gene features, 34,508 transcripts, 28,285 protein identifiers and 227,033 CDS rows. After retaining current, taxonomically compatible associations from the combined audit, all 20,630 annotated protein identifiers mapped unambiguously to a gene under the strict schema (100% mapping coverage). Collapsing protein associations generated 1,097,293 unique gene–GO rows for 16,595 genes and 15,614 GO terms. This result shows that the annotation audit can be linked to gene-level enrichment without silently assuming that FASTA and GFF identifiers are interchangeable. The `OrgDb` utility remains ancillary to the central validation workflow and should be presented in full as supplementary documentation.

## Table 2. GOaudit summary for the *S. pistillata* case study

| Metric | eggNOG-mapper | eggNOG-mapper + InterProScan |
|---|---:|---:|
| Annotated proteins | 11,979 | 20,746 |
| Protein–GO associations | 1,796,068 | 1,883,008 |
| Unique GO terms | 20,339 | 20,738 |
| Current, compatible rows (including resolved alternative IDs) | 1,430,653 (79.65%) | 1,514,617 (80.44%) |
| Taxon-constraint violations | 90,920 (5.06%) | 91,151 (4.84%) |
| Unique violating terms | 2,914 | 2,920 |
| Proteins with at least one violation | 5,070 (42.3%) | 5,175 (24.9%) |
| Obsolete associations | 274,495 (15.3%) | 277,240 (14.7%) |
| Unique obsolete terms | 2,166 | 2,204 |
| Alternative-ID associations (subset of compatible rows) | 33,954 (1.89%) | 36,482 (1.94%) |
| Unknown GO identifiers | 0 | 0 |

## Table 3. Ten most frequent taxon-constraint violations in the combined coral annotation table

| GO identifier | Term | Associations | Released `in_taxon` constraint |
|---|---|---:|---|
| GO:0072359 | circulatory system development | 1,540 | Bilateria |
| GO:0007417 | central nervous system development | 1,268 | Bilateria |
| GO:0060322 | head development | 1,039 | Bilateria |
| GO:0007420 | brain development | 984 | Bilateria |
| GO:0043009 | chordate embryonic development | 805 | Chordata |
| GO:0007507 | heart development | 743 | Bilateria |
| GO:0045321 | leukocyte activation | 739 | Vertebrata |
| GO:0007444 | imaginal disc development | 625 | Insecta |
| GO:0002165 | instar larval or pupal development | 621 | Arthropoda |
| GO:0060541 | respiratory system development | 574 | Bilateria |

# Discussion

Automated annotation is indispensable for non-model organism genomics. The problem described here is not that eggNOG-mapper, InterProScan or other functional annotation tools are generally unreliable, nor that orthology is an inappropriate basis for function transfer. Instead, a large annotation payload can contain a small but consequential subset of terms whose taxonomic context has been lost. If those terms are supplied directly to enrichment or comparative analyses, an invalid organism-level interpretation can become one of the most prominent results.

The salivary-gland example is useful because it separates two decisions that are often conflated. The sequence hit to another cnidarian was strong and may be biologically informative. The association with a term explicitly describing *Drosophila* larval salivary-gland breakdown was incompatible with the coral lineage under the current ontology. Rejecting the second statement does not require rejecting the first. This is why GOaudit operates at the level of individual protein–GO associations rather than labelling an entire protein hit as correct or incorrect.

## Implications for using eggNOG-mapper output

eggNOG-mapper provides options to adjust the taxonomic scope used for orthology assignment and annotation transfer. These options are important, particularly for preventing transfer from unwanted donor lineages. However, taxonomic scope and GO taxon constraints answer different questions. The former restricts which orthologues contribute annotations; the latter tests whether each resulting GO term can apply to the target organism. In the present example, the accepted seed itself came from a suitable lineage, so a closer taxonomic scope would not necessarily have removed the problematic term.

A second risk arises when the complete comma-separated `GOs` field is treated as a homogeneous set of equivalent annotations. The field can contain a large number of terms spanning several ontology levels and biological contexts. When expanded for enrichment, every identifier may be counted without the source annotation, donor taxon, evidence code or confidence that originally supported it. This is not an error in file parsing, but it changes what can be checked later. We therefore recommend archiving the original eggNOG-mapper output, command line, software version and database release, even when a simple two-column table is used downstream.

Finally, annotation and ontology releases need to be distinguished. A GO identifier that was current when a source database was assembled may be obsolete by the time a researcher performs enrichment. GO has undergone substantial recent refactoring, including the removal of imprecise or redundant terms (Gene Ontology Consortium, 2026a). GOaudit reports these records rather than silently resolving every obsolete term, since some have no one-to-one replacement. The result is a more honest separation between taxonomic exclusions and ontology maintenance.

## Relationship to existing taxon-aware tools

GOaudit builds on existing standards and does not introduce new taxon constraints. The GO Consortium's own validation is the authoritative quality-control process for annotations submitted to GO. Ontobio and OWLTools are appropriate when a group is producing or validating complete GO association records and needs the wider GO rule and ontology-reasoning infrastructure. OmicsBox provides a convenient taxon filter during or after annotation in its integrated workflow. FunTaxIS-lite addresses constraint coverage itself, combining GO constraints with constraints inferred from annotation distributions and allowing manually defined rules (Bianca *et al.*, 2023). Its Cnidaria prohibited-term list contains GO:0035070, so both systems identify the motivating coral association despite reaching that result through different end-user workflows and constraint policies.

GOaudit differs mainly in its intended point of use and evidential policy. It accepts a minimal association table produced by any annotation method, requires only an NCBI taxid, uses the official released computed constraints without adding absence-derived biological rules, resolves current/alternative/obsolete identifiers, and emits an association-level audit, plots and provenance manifest. This narrower scope is a strength for reproducible command-line workflows, but it is not evidence that GOaudit supersedes richer annotation formats, extended constraint resources or system-level evaluation. Where evidence and provenance are available, GAF or GPAD remains a better archival representation than two columns.

## Table 4. Relationship between GOaudit and existing taxon-aware workflows

| Workflow | Primary input and purpose | Taxon logic | User-facing result | Distinction relevant to GOaudit |
|---|---|---|---|---|
| GOaudit | Two-column protein–GO TSV plus one NCBI taxid; downstream audit of existing predictions | Dated official GO `in_taxon`/`never_in_taxon` constraints, union definitions and complete NCBI lineage | Row-level explanation, optional taxon-only filtering, ontology-ID status, summaries, plots and checksummed manifest | Narrow, open, workflow-independent quality control for flat researcher-generated tables |
| Ontobio with GORULE:0000013 | General parser and validator for GAF, GPAD and related association formats, with Gaferencer inferences supplied for Rule 13 | GO annotation-rule semantics; experimental failures are retained as warnings, non-experimental failures are rejected and negated annotations are exempt | Validation/conversion and Markdown/JSON reports | Comprehensive provider-facing validation with a richer schema and evidence-aware behavior; not a bare two-column constraint lookup |
| OWLTools GAF validation | Complete GO association files and ontology resources | OWL reasoning over GO/GO-Plus and NCBI Taxonomy | Line-level taxon and wider annotation validation findings | Established GO-pipeline infrastructure rather than a small packaged audit for researcher exports |
| OmicsBox/Blast2GO | Integrated annotation environment and project formats | GO-defined restrictions for a supplied taxid | Filters annotations during or after GO annotation, with integrated summaries | Similar end-user outcome inside a larger graphical, licensed annotation workflow |
| FunTaxIS-lite | Web/local generation of taxon-specific prohibited-term sets from GOA, GO-Plus, NCBI Taxonomy and configuration files | Combines GOC constraints with manual and annotation-distribution-derived `never_in` constraints | Taxon-specific prohibited-term lists; its Cnidaria list includes GO:0035070 | Extends the constraint model and already catches the sentinel; GOaudit instead applies the official release directly to supplied rows and records decision provenance |
| GAEF | Protein plus GO-term sets; genome-scale completeness, coherence and consistency assessment | Reasons over constraints implied by the supplied functions without requiring a known target taxon | HTML/JSON evaluation plus taxon-constraint and explanation tables | Broader system-level question; a single target-incompatible term need not be detected without a contradictory function |
| RAR | Large comparative GOA datasets across taxa | Empirical ratios of annotation rates plus statistical and manual review | Candidate taxon-specific misannotations | Can identify problems beyond curated constraints but is not a deterministic official-rule audit of one supplied proteome |
| OAK / QuickGO API | Ontology terms and constraint queries | Inherited ontology constraints or hosted term metadata | Constraint records for supplied GO terms | Useful building blocks; target-lineage and association-table comparison remains to be implemented by the user |
| Argot2.5; PANNZER/PANNZER2 | Protein sequences submitted to each predictor | FunTaxIS or predictor-specific broad taxonomic filters | Suppresses incompatible terms during that predictor's own analysis | Upstream and predictor-specific rather than post-processing arbitrary external annotations |

## Consequences for enrichment and comparative genomics

Taxon-incompatible associations can influence downstream analysis in at least two ways. First, a single lineage-specific term may be assigned to several related proteins and become enriched in a focal gene list. Second, propagation through the GO hierarchy can distribute the same inappropriate biological context across several parent and child terms, giving the impression of a coherent biological programme. The frequent developmental and anatomical violations in the coral data illustrate both possibilities.

The present study establishes the scale of the input problem but does not yet quantify the change in enrichment statistics after filtering. That analysis should be added before making a stronger claim that GOaudit improves biological conclusions. A suitable test would reproduce the original coral enrichment with the unfiltered and taxon-filtered mappings, use the same gene universe and multiple-testing procedure, and compare significant terms, ranks and semantic summaries. The salivary-gland term should be shown as the motivating positive control, while compatible core functions should demonstrate that filtering does not indiscriminately reduce the annotation set.

The same consideration applies to cross-species comparisons. A term absent after filtering may reflect an incompatible annotation rather than a biological loss, but a term that passes GOaudit is not necessarily comparable across all species. Differences in gene-model completeness, annotation method, database release and experimental evidence remain. GOaudit removes one known source of asymmetry; it cannot make heterogeneous annotations equivalent.

## Limitations

Taxon constraints are conservative logical checks, not proof of function. An association that passes may still be wrong because the protein was mispredicted, the donor annotation was incorrect, the orthology assignment was inappropriate, or the relevant GO term has no taxon constraint. Conversely, a reported violation may warrant biological and ontology review. Taxon constraints evolve as knowledge improves, and unusual biology can expose a rule that is too broad or too narrow. High-impact exclusions should therefore be inspected and possible ontology issues reported to the GO Consortium.

The official-only policy is intentionally narrower than FunTaxIS-lite and empirical approaches such as RAR. It reduces the assumptions made from absence in incompletely annotated taxa, but it also lowers potential recall: many biologically implausible associations have no current official constraint and will pass. GOaudit should therefore be interpreted as a high-specificity check for one formal class of inconsistency, not as an exhaustive plausibility filter.

GOaudit currently requires one taxid for the entire input. This is suitable for a single-species proteome but not for metagenomes, contaminated assemblies or host–symbiont mixtures unless sequences have first been assigned to the relevant organism. A wrong taxid will produce a reproducible but wrong audit. Similarly, taxonomic compatibility does not establish that an anatomical process is present in every member of an allowed clade; `in_taxon Bilateria` means that a term is restricted to that lineage, not that all bilaterians possess the process.

The minimal input format also discards annotation provenance. It is intentionally easy to produce, but it cannot support source-specific evidence weighting or distinguish independent support for duplicate associations. The combined case study should therefore be interpreted as a demonstration of heterogeneous input handling, not a benchmark of eggNOG-mapper against InterProScan. A future optional extended format could retain source, evidence and confidence fields without changing the two required columns.

Protein-to-gene conversion is another independent concern. The current `OrgDb` preparation supports a documented EGAPx/RefSeq schema and fails on ambiguous mappings; it is not a universal GFF3 parser. Other annotation systems use different attribute names and transcript hierarchies and should be supported through explicit schemas rather than increasingly permissive identifier guessing.

Finally, the present biological evaluation uses one coral genome. This is sufficient to demonstrate a real failure mode and test the implementation, but it is not sufficient to estimate prevalence across the tree of life. A multi-taxon benchmark is required before concluding that the observed proportions are typical of non-model organisms or that one annotation method is more affected than another.

## Recommended use

We recommend running GOaudit after GO annotation and before constructing a gene-level database, testing enrichment or comparing functions among species. `report` mode should be used first. Researchers should review the most frequent violations, confirm the target taxid and inspect whether the input contains more than one organism. If the findings are consistent with the intended dataset, `remove` mode can create a taxon-filtered table while the audit and reference manifest are retained alongside the analysis. Publications should report the GOaudit version, target NCBI taxid, GO release, reference retrieval date, filtering mode, number of associations assessed and number excluded.

# Conclusions

The number and sophistication of tools that generate GO terms continue to increase, but prediction and validation remain separate problems. GOaudit adds a small validation layer to an otherwise familiar workflow. In the *S. pistillata* example, it identified an arthropod-specific salivary-gland term transferred alongside a strong hit to another cnidarian, then found the same class of inconsistency across thousands of terms in the complete annotation table. The tool does not determine whether every retained annotation is biologically correct. It does, however, expose a formally defined class of taxonomic inconsistency before those annotations become enrichment results, figures and biological conclusions.

# Availability and requirements

- **Project:** GOaudit
- **Source code:** <https://github.com/Andy-B-123/bioinfo-tool> [rename repository to `GOaudit` before submission if practical]
- **Licence:** MIT
- **Programming language:** Python ≥3.10
- **Runtime dependencies:** none
- **Other requirements:** internet access for the initial reference-data update; validation can then run from the local reference cache
- **Operating systems:** [add tested Linux/macOS/Windows support]
- **Archived release:** [create a tagged release and Zenodo DOI]
- **Python package:** [publish to PyPI and add installation URL]
- **Documentation:** README and worked `OrgDb` workflow in the source repository
- **Reference data:** downloaded separately from GO and NCBI; not bundled with the package
- **Case-study data:** [archive the small two-column inputs, commands, manifests, summaries and plotting outputs at Zenodo/figshare; link the public genome and large raw annotation files rather than adding them to Git]
- **Restrictions on use:** none

# List of abbreviations

**CLI:** command-line interface; **GAF:** Gene Association File; **GFF3:** General Feature Format version 3; **GO:** Gene Ontology; **GPAD:** Gene Product Association Data; **NCBI:** National Center for Biotechnology Information; **OrgDb:** organism-level Bioconductor annotation database; **TSV:** tab-separated values.

# Declarations

## Availability of data and materials

The source code, tests and documentation are available under the MIT licence at <https://github.com/Andy-B-123/bioinfo-tool>. The complete GO ontology, computed constraint and grouping files are available from the Gene Ontology Consortium, and NCBI Taxonomy data are available from NCBI. The *S. pistillata* genome and proteome are available from [accession/repository]. The exact GOaudit inputs, original annotation-tool command lines, reference manifest and result summaries used in this article will be archived at [DOI]. Large annotation files will be deposited as compressed research data or regenerated from documented public inputs; they will not be included in the software package.

## Ethics approval and consent to participate

Not applicable.

## Consent for publication

Not applicable.

## Competing interests

The authors declare that they have no competing interests. [Confirm for all authors.]

## Funding

[Add funding sources and grant numbers.]

## Authors' contributions

AB conceived the study, identified the motivating annotation, developed the biological use case, analysed the data and drafted the manuscript. [Add software, supervision, testing and review contributions using CRediT roles after the author list is final.]

## Acknowledgements

[Add acknowledgements, computing facility and data providers.]

# Figure scaffold and draft legends

## Figure 1. GOaudit adds a taxonomic validation step between functional annotation and interpretation

**Panel A:** A non-model proteome is annotated using orthology-, similarity-, signature-, sequence-model- or structure-based tools. Their GO associations are converted to a strict two-column table. **Panel B:** GOaudit resolves the target NCBI lineage, current and alternative GO identifiers, and released `in_taxon` and `never_in_taxon` constraints. Each association is labelled current/compatible, alternative ID, obsolete, unknown or taxon violation. **Panel C:** The audit, summary and plots are reviewed before an optional filtered table or validated gene-level `OrgDb` input is produced. The underlying protein hit is retained when only one associated GO term is incompatible.

## Figure 2. A valid-looking cnidarian hit can carry an arthropod-restricted annotation

eggNOG-mapper selected a *Nematostella vectensis* seed orthologue for the *S. pistillata* protein `egapxtmp_003494-P1` with E-value 3.2 × 10<sup>−68</sup>, 45.1% identity and >96% coverage of both sequences. Its 114-term GO field included GO:0035070, `salivary gland histolysis`. GO restricts this term to Arthropoda. GOaudit removes only the highlighted protein–GO association and retains the seed hit and compatible annotations.

## Figure 3. Distribution of GOaudit outcomes in the *S. pistillata* eggNOG-mapper annotation

**Panel A:** Counts and percentages of current/compatible, taxon-violating and obsolete protein–GO associations; alternative identifiers are shown as a subset of compatible associations. **Panel B:** GO namespace distribution of taxon violations. **Panel C:** Ten most frequent incompatible terms, coloured by the lineage specified by the triggering constraint. **Panel D:** Proportion of annotated proteins carrying at least one taxon violation. Use the existing SVG outputs as a starting point, but combine them into a journal-quality multi-panel figure and retain absolute counts next to percentages.

## Figure 4. Effect of taxon filtering on coral GO enrichment [analysis required]

**Panel A:** Rank and adjusted *P*-value of enriched biological-process terms before and after filtering, using an identical gene universe. **Panel B:** Terms lost, retained and newly exposed after multiple-testing correction. **Panel C:** Semantic summary of the leading terms before and after filtering, highlighting GO:0035070 as the positive control. This figure should only be included once the enrichment workflow is rerun from frozen inputs.

# Work required before submission

The following work would turn this from a strong draft and single-species software demonstration into a much more convincing publication.

1. **Freeze the software release.** Rename the repository if desired, add a citation file, user-facing changelog, tagged release, Zenodo DOI, PyPI package, continuous integration and a small end-to-end example that does not download the coral files.
2. **Complete the implementation tests.** Add explicit union-class and multiple-constraint fixtures, malformed/cyclic taxonomy tests, deterministic snapshot tests of all outputs, and integration tests across supported Python versions and operating systems.
3. **Run controlled comparisons with existing taxon-aware workflows.** Freeze one GO and NCBI Taxonomy release. Convert a representative multi-taxon fixture to GAF and test row-level agreement with Ontobio GORULE:0000013 using the required Gaferencer input; investigate every discordance. Run FunTaxIS-lite first in GOC-only mode with empty manual constraints and then in automatic-only and full modes, applying each result to the identical association rows. Separate release, union, propagation, obsolete-ID and policy differences. Compare OmicsBox and OWLTools where practical, and report setup, required fields, reference provenance and output detail without treating “more terms removed” as proof of accuracy. This comparison is essential for a BMC Bioinformatics Software article.
4. **Benchmark runtime and memory.** Report reference-download size separately from validation time; measure wall-clock time and peak resident memory on declared hardware for the coral eggNOG and combined tables.
5. **Run the enrichment comparison.** Reproduce the motivating analysis with identical gene lists, gene universe, ontology and multiple-testing settings before and after taxon filtering. Archive the exact tables used to produce Figure 4.
6. **Add a multi-taxon benchmark for a higher-impact submission.** A compact design would include at least one cnidarian, arthropod, plant, fungus, vertebrate and bacterium or protist. Run the same annotation sources where possible; include known valid and invalid `in_taxon`, `never_in_taxon` and union-class controls; and report association-, term- and protein-level violation rates without treating taxa as independent biological replicates unless the design supports that inference.
7. **Separate annotation sources.** Add an optional `source` column or analyse eggNOG-mapper and InterProScan outputs independently before concatenation. This will distinguish unique, shared and source-specific violations while preserving the simple two-column default.
8. **Complete case-study metadata.** Add the *S. pistillata* assembly accession and citation, exact InterProScan/InterPro releases and command, annotation dates, hardware, and all software versions.
9. **Validate the `OrgDb` downstream artefact.** Run `AnnotationDbi::checkMAPCOUNTS()`, document the single GO.db version mismatch if it remains, install/check the package in a clean R/Bioconductor environment, and keep this component supplementary unless it becomes a separately maintained R package.
10. **Archive data responsibly.** Put no thesis, genome, full GFF, proteome or multi-gigabyte reference archive in the Python package. Deposit compact case-study inputs and outputs in a data repository; point to public genome accessions and provide scripts/checksums for regenerating larger files.
11. **Manual biological review.** Inspect the most frequent exclusions and a stratified sample across namespaces and constraint types. Record whether each reflects expected lineage biology, a mixed/contaminating sequence, an annotation-source problem or a constraint that should be queried with GO.

# References

Ashburner M, Ball CA, Blake JA, Botstein D, Butler H, Cherry JM, *et al.* Gene Ontology: tool for the unification of biology. *Nature Genetics*. 2000;25:25–29. <https://doi.org/10.1038/75556>

Bachler A, Walsh TK, Rane RV, Pandey G. Chimeric mis-annotations of genes remain pervasive in eukaryotic non-model organisms. *BMC Genomics*. 2025;26:630. <https://doi.org/10.1186/s12864-025-11765-w>

Bianca F, Ispano E, Gazzola E, Lavezzo E, Fontana P, Toppo S. FunTaxIS-lite: a simple and light solution to investigate protein functions in all living organisms. *Bioinformatics*. 2023;39:btad549. <https://doi.org/10.1093/bioinformatics/btad549>

Blum M, Andreeva A, Florentino LC, Chuguransky SR, Grego T, Hobbs E, *et al.* InterPro: the protein sequence classification resource in 2025. *Nucleic Acids Research*. 2025;53:D444–D456. <https://doi.org/10.1093/nar/gkae1082>

Blum M, Hobbs E, Florentino L, Bateman A. InterProScan 6: a modern large-scale protein function annotation pipeline. *Bioinformatics Advances*. 2026;6:vbag141. <https://doi.org/10.1093/bioadv/vbag141>

Burge S, Kelly E, Lonsdale D, Mutowo-Muellenet P, McAnulla C, Mitchell A, *et al.* Manual GO annotation of predictive protein signatures: the InterPro approach to GO curation. *Database*. 2012;2012:bar068. <https://doi.org/10.1093/database/bar068>

Cantalapiedra CP, Hernández-Plaza A, Letunic I, Bork P, Huerta-Cepas J. eggNOG-mapper v2: functional annotation, orthology assignments, and domain prediction at the metagenomic scale. *Molecular Biology and Evolution*. 2021;38:5825–5829. <https://doi.org/10.1093/molbev/msab293>

Cao Y, Shen Y. TALE: Transformer-based protein function annotation with joint sequence–label embedding. *Bioinformatics*. 2021;37:2825–2833. <https://doi.org/10.1093/bioinformatics/btab198>

Conesa A, Götz S, García-Gómez JM, Terol J, Talón M, Robles M. Blast2GO: a universal tool for annotation, visualization and analysis in functional genomics research. *Bioinformatics*. 2005;21:3674–3676. <https://doi.org/10.1093/bioinformatics/bti610>

Deegan JI, Dimmer EC, Mungall CJ. Formalization of taxon-based constraints to detect inconsistencies in annotation and ontology development. *BMC Bioinformatics*. 2010;11:530. <https://doi.org/10.1186/1471-2105-11-530>

Falda M, Lavezzo E, Fontana P, Bianco L, Berselli M, Formentin E, Toppo S. Eliciting the Functional Taxonomy from protein annotations and taxa. *Scientific Reports*. 2016;6:31971. <https://doi.org/10.1038/srep31971>

FunTaxIS-lite. Cnidaria taxonomic-constraint list. Accessed 14 July 2026. <https://www.medcomp.medicina.unipd.it/funtaxis-lite/static/constraints_lists/6073_Cnidaria_constraints.txt>

Gene Ontology Consortium. The Gene Ontology knowledgebase in 2026. *Nucleic Acids Research*. 2026a;54:D1779–D1792. <https://doi.org/10.1093/nar/gkaf1292>

Gene Ontology Consortium. Taxon constraints in the Gene Ontology. 2026b. Accessed 13 July 2026. <https://geneontology.org/docs/taxon-constraints/>

Gene Ontology Consortium. GO Association File (GAF) format 2.2. Accessed 13 July 2026. <https://geneontology.org/docs/go-annotation-file-gaf-format-2.2/>

Gilks WR, Audit B, De Angelis D, Tsoka S, Ouzounis CA. Percolation of annotation errors through hierarchically structured protein sequence databases. *Mathematical Biosciences*. 2005;193:223–234. <https://doi.org/10.1016/j.mbs.2004.08.001>

Gligorijević V, Renfrew PD, Kosciolek T, Leman JK, Berenberg D, Vatanen T, *et al.* Structure-based protein function prediction using graph convolutional networks. *Nature Communications*. 2021;12:3168. <https://doi.org/10.1038/s41467-021-23303-9>

Götz S, García-Gómez JM, Terol J, Williams TD, Nagaraj SH, Nueda MJ, *et al.* High-throughput functional annotation and data mining with the Blast2GO suite. *Nucleic Acids Research*. 2008;36:3420–3435. <https://doi.org/10.1093/nar/gkn176>

Huerta-Cepas J, Forslund K, Coelho LP, Szklarczyk D, Jensen LJ, von Mering C, Bork P. Fast genome-wide functional annotation through orthology assignment by eggNOG-mapper. *Molecular Biology and Evolution*. 2017;34:2115–2122. <https://doi.org/10.1093/molbev/msx148>

Jones P, Binns D, Chang H-Y, Fraser M, Li W, McAnulla C, *et al.* InterProScan 5: genome-scale protein function classification. *Bioinformatics*. 2014;30:1236–1240. <https://doi.org/10.1093/bioinformatics/btu031>

Kulmanov M, Hoehndorf R. DeepGOPlus: improved protein function prediction from sequence. *Bioinformatics*. 2020;36:422–429. <https://doi.org/10.1093/bioinformatics/btz595>

Kulmanov M, Guzmán-Vega FJ, Duek Roggli P, Lane L, Hoehndorf R. Protein function prediction as approximate semantic entailment. *Nature Machine Intelligence*. 2024;6:220–228. <https://doi.org/10.1038/s42256-024-00795-w>

Lavezzo E, Falda M, Fontana P, Bianco L, Toppo S. Enhancing protein function prediction with taxonomic constraints—the Argot2.5 web server. *Methods*. 2016;93:15–23. <https://doi.org/10.1016/j.ymeth.2015.08.021>

MacDougall A, Volynkin V, Saidi R, Poggioli D, Zellner H, Hatton-Ellis E, *et al.* UniRule: a unified rule resource for automatic annotation in the UniProt Knowledgebase. *Bioinformatics*. 2020;36:4643–4648. <https://doi.org/10.1093/bioinformatics/btaa485>

OmicsBox. GO Annotation—OmicsBox User Manual. Accessed 13 July 2026. <https://docs.omicsbox.biobam.com/latest/Gene-Ontology-Annotation/>

Ontobio developers. Ontobio command-line and GO rules documentation. Accessed 14 July 2026. <https://ontobio.readthedocs.io/en/latest/commandline.html>

Ontobio developers. GORULE:0000013 implementation, Ontobio commit 9f46dbc. Accessed 14 July 2026. <https://github.com/biolink/ontobio/blob/9f46dbc9576d1b28b108e3d06e8266963362a2d8/ontobio/io/qc.py#L291-L328>

Ontology Access Kit developers. OAK taxon-constraint command documentation. Accessed 14 July 2026. <https://incatools.github.io/ontology-access-kit/cli.html>

OWLTools developers. OWLTools source repository and GO association validation software. Accessed 14 July 2026. <https://github.com/owlcollab/owltools>

QuickGO. QuickGO REST API documentation. Accessed 14 July 2026. <https://www.ebi.ac.uk/QuickGO/api/index.html>

Radivojac P, Clark WT, Oron TR, Schnoes AM, Wittkop T, Sokolov A, *et al.* A large-scale evaluation of computational protein function prediction. *Nature Methods*. 2013;10:221–227. <https://doi.org/10.1038/nmeth.2340>

Schnoes AM, Brown SD, Dodevski I, Babbitt PC. Annotation error in public databases: misannotation of molecular function in enzyme superfamilies. *PLoS Computational Biology*. 2009;5:e1000605. <https://doi.org/10.1371/journal.pcbi.1000605>

Schoch CL, Ciufo S, Domrachev M, Hotton CL, Kannan S, Khovanskaya R, *et al.* NCBI Taxonomy: a comprehensive update on curation, resources and tools. *Database*. 2020;2020:baaa062. <https://doi.org/10.1093/database/baaa062>

Tang H, Finn RD, Thomas PD. TreeGrafter: phylogenetic tree-based annotation of proteins with Gene Ontology terms and other annotations. *Bioinformatics*. 2019;35:518–520. <https://doi.org/10.1093/bioinformatics/bty625>

Tawfiq R, Kulmanov M, Hoehndorf R. Evaluating completeness, coherence, and consistency of genome-scale function annotations. *Briefings in Bioinformatics*. 2026;27:bbag336. <https://doi.org/10.1093/bib/bbag336>

Törönen P, Medlar A, Holm L. PANNZER2: a rapid functional annotation web server. *Nucleic Acids Research*. 2018;46:W84–W88. <https://doi.org/10.1093/nar/gky350>

Törönen P, Holm L. PANNZER—A practical tool for protein function prediction. *Protein Science*. 2022;31:118–128. <https://doi.org/10.1002/pro.4193>

UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2025. *Nucleic Acids Research*. 2025;53:D609–D617. <https://doi.org/10.1093/nar/gkae1010>

Wang W, Shuai Y, Zeng M, Fan W, Li M. DPFunc: accurately predicting protein function via deep learning with domain-guided structure information. *Nature Communications*. 2025;16:70. <https://doi.org/10.1038/s41467-024-54816-8>

Wang S, You R, Liu Y, Xiong Y, Zhu S. NetGO 3.0: protein language model improves large-scale functional annotations. *Genomics, Proteomics & Bioinformatics*. 2023;21:349–358. <https://doi.org/10.1016/j.gpb.2023.04.001>

Wei X, Zhang C, Freddolino L, Zhang Y. Detecting Gene Ontology misannotations using taxon-specific rate ratio comparisons. *Bioinformatics*. 2020;36:4383–4388. <https://doi.org/10.1093/bioinformatics/btaa548>

Zhou N, Jiang Y, Bergquist TR, Lee AJ, Kacsoh BZ, Crocker AW, *et al.* The CAFA challenge reports improved protein function prediction and new functional annotations for hundreds of genes through experimental screens. *Genome Biology*. 2019;20:244. <https://doi.org/10.1186/s13059-019-1835-8>
