# GOaudit related-software assessment

> Landscape checked 14 July 2026. This is a focused software comparison, not a formal systematic review. It separates tools that can validate supplied annotations from resources that generate constraints or apply taxonomic logic inside their own prediction workflow.

## Bottom line

There is still a publishable role for GOaudit, but the defensible novelty is narrower than “taxon-aware GO filtering”. That idea is established: GO itself uses taxon constraints, Ontobio and OWLTools have applied them during annotation validation, OmicsBox exposes a taxon filter, and FunTaxIS/FunTaxIS-lite generate substantially expanded constraint sets. A newly published framework, GAEF, also evaluates taxonomic consistency as one component of genome-scale annotation quality.

GOaudit's distinct contribution is an **independent, conservative and reproducible audit of already-generated, flat protein–GO tables**. Its strongest combination of features is:

- exactly two input columns plus an arbitrary NCBI taxid;
- input adapters for common non-model-organism annotation outputs;
- current official computed GO constraints, including union taxa, without inferring extra biological prohibitions from missing annotations;
- explicit handling of alternative, obsolete and unknown GO identifiers;
- one status, triggering rule and explanation for every supplied association;
- report, flag and remove modes, summary tables, plots and machine-readable output;
- a copied reference manifest containing URLs, retrieval time and checksums; and
- no runtime Python dependencies after reference data have been downloaded.

That is an interoperability and auditability contribution, not a new ontology method. The paper should say so plainly.

## Closest software and resources

| System | Primary job and input | Taxonomic basis | User-facing result | Would it directly answer “is GO:0035070 valid for this coral?” | Principal distinction from GOaudit |
|---|---|---|---|---|---|
| **GOaudit** | Audit an existing two-column protein–GO TSV using a supplied NCBI taxid | Dated official GO computed `in_taxon`/`never_in_taxon` assertions, GO union taxa and the full NCBI lineage | Per-association audit and reason; optional flagged/filtered TSV; obsolete/alternative/unknown-ID status; summaries, plots and checksummed manifest | **Yes** | The proposed tool: deliberately narrow, source-independent and conservative |
| **Ontobio + GORULE:0000013** | Validate GAF/GPAD association records containing their own taxon, evidence, references and provenance | GO's annotation rule engine; Rule 13 consumes a Gaferencer inference resource rather than acting as a bare two-column constraint lookup | Line-level validation in Markdown/JSON and converted/filtered association files; behavior can depend on evidence class | **Yes, after constructing a valid rich association record, supplying the inference resource and enabling the rule** | Authoritative provider-oriented validation and many other GO rules; materially richer schema and setup |
| **OWLTools GAF validation** | Legacy GO-pipeline validation of complete GAF records | OWL reasoning over GO/GO-Plus and NCBI Taxonomy | Line-numbered taxon-compatibility violations as part of broader association checks | **Yes, after GAF construction and ontology setup** | General ontology/GO pipeline infrastructure rather than a packaged researcher-facing table audit |
| **OmicsBox/Blast2GO** | Annotate sequences or work with annotations inside an OmicsBox Functional Annotation Project | GO restrictions for a user-supplied NCBI taxid | Removes invalid annotations during GO annotation or through “Filter GO Annotations by Taxon”; integrated charts and exports | **Yes, within an OmicsBox project** | Closest end-user outcome, but embedded in a larger graphical, licensed annotation environment rather than an independent CLI audit |
| **FunTaxIS-lite** | Generate and browse prohibited GO-term sets for selected taxa from GOA, GO-Plus, NCBI Taxonomy and configuration files | Official GO constraints plus manual rules and additional `never_in` constraints inferred from annotation frequencies and absences; official constraints take precedence over automatic ones | Taxon-specific prohibited-term lists; web browsing/download or a locally regenerated constraint resource | **Yes at term-list level. Its server maps taxid 50429 to Cnidaria and the downloadable Cnidaria list explicitly contains GO:0035070; the list must then be joined to the protein associations** | Closest conceptual neighbour. It expands the constraint knowledge base; GOaudit applies only the official release directly to a user's rows and records each decision |
| **GAEF** | Evaluate a proteome-wide annotation set for completeness, coherence and consistency; input is a protein followed by one or more GO terms | GO, GO-Plus, MetaCyc, NCBI Taxonomy and GO constraints with OWL reasoning | HTML/JSON genome-scale report plus taxon-constraint and explanation TSVs | **Not necessarily. It deliberately does not compare the annotations with a declared target taxid; it asks whether the functions imply mutually compatible taxa** | Broader systems-level evaluation and a much heavier reasoning stack; complementary rather than a substitute for target-taxon validation |
| **RAR method/web workflow** | Detect taxon-specific misannotations statistically by comparing GO annotation rates across taxa in large GOA datasets | Empirical annotation-rate ratios, significance testing and manual review, not formal GO `in_taxon`/`never_in_taxon` rules | Candidate rare-in-taxon terms and associations | **Not from the coral table alone; the result depends on comparative annotation distributions** | Can find suspicious associations beyond curated constraints, but is data-intensive and vulnerable to annotation/knowledge imbalance without review |
| **Ontology Access Kit (OAK)** | Query or evaluate ontology-level taxon constraints for supplied terms/candidate constraints | Inferred ancestors and descendants in an ontology containing both taxon relations and NCBI Taxonomy | Structured constraint records from `taxon-constraints` and related commands | **It can expose the term's constraint, but the user must implement the target-lineage association audit** | A general ontology programming toolkit and useful building block, not an end-to-end protein–GO validator |
| **QuickGO REST API** | Retrieve GO term metadata and constraints online for a CSV list of GO IDs | Current QuickGO term records, including constraint and blacklist metadata | JSON term/constraint information | **It exposes the Arthropoda restriction, but does not perform the coral-lineage comparison or table audit** | Hosted information service rather than reproducible, release-frozen analysis software |

### Important Ontobio setup caveat

The current Ontobio Rule 13 implementation is not activated meaningfully by `-l 13` or `-l all` alone. Its CLI accepts a separate `--gaferencer-file`; the rule automatically passes annotations when those annotation inferences are absent. With the inference resource present, negated annotations pass, non-experimental violations are errors and experimental violations are warnings. This is consistent with the official GO rule, which retains experimental annotations for review rather than automatically deleting them. A fair parity benchmark must therefore generate/supply the Gaferencer JSON and must compare evidence-aware rule outcomes with GOaudit's evidence-free compatibility status rather than assuming identical deletion behavior.

Primary implementation evidence is available in the pinned Ontobio [CLI argument and loading code](https://github.com/biolink/ontobio/blob/9f46dbc9576d1b28b108e3d06e8266963362a2d8/bin/ontobio-parse-assocs.py#L67-L74), [Rule 13 implementation](https://github.com/biolink/ontobio/blob/9f46dbc9576d1b28b108e3d06e8266963362a2d8/ontobio/io/qc.py#L291-L328), [tests](https://github.com/biolink/ontobio/blob/9f46dbc9576d1b28b108e3d06e8266963362a2d8/tests/test_qc.py#L220-L244) and the [official rule definition](https://github.com/geneontology/go-site/blob/bda0da1a19b4f14db430be9e7ddfad29be2be0b3/metadata/rules/gorule-0000013.md#L13-L18).

## Taxon-aware systems that are not direct alternatives

| System | How taxonomic information is used | Why it is relevant, but not a substitute |
|---|---|---|
| **FunTaxIS (original)** | Infers positive and negative functional taxonomies from annotation distributions and projects them across GO and NCBI Taxonomy | Intellectual predecessor to FunTaxIS-lite and important prior art for constraint inference, not a flat-table audit |
| **Argot2.5** | Applies FunTaxIS-extended constraints while generating its own GO predictions | Demonstrates that taxon filtering can improve prediction, but cannot audit eggNOG-mapper, InterProScan or arbitrary external output |
| **PANNZER/PANNZER2** | Offers predictor-specific branch filters derived from non-IEA GOA annotations for a limited set of broad taxonomic groups | Useful upstream safeguard, but not arbitrary-taxid, source-independent post-processing |
| **LLM Agent Based Protein Function Prediction** | A prediction-refinement agent queries GO computed taxon constraints alongside sequence, InterPro, UniProt and literature evidence | Recent evidence that taxon checks are becoming part of predictors; it refines prediction scores and explanations rather than validating a user's table |
| **GOTaxon** | Represents evolutionary gain and loss events for GO functions and broadens evolutionary taxon coverage | A research resource for evolutionary constraints, not an association-audit interface |
| **[GOATOOLS](https://doi.org/10.1038/s41598-018-28948-z) and [ROBOT](https://doi.org/10.1186/s12859-019-3002-3)** | GOATOOLS parses GO/GAF and handles obsolete terms; ROBOT can reason over and query OWL ontologies | Both could be used to build a validator, but neither currently exposes a ready protein–GO-versus-target-taxid workflow |

Other apparently related results were checked but are not functional competitors. [TaxaGO](https://pmc.ncbi.nlm.nih.gov/articles/PMC12581831/) uses phylogeny in cross-taxon enrichment rather than validating annotations. [NoisyGOA](https://doi.org/10.1016/j.compbiolchem.2016.09.005) detects anomalous GO associations, but its “taxonomic similarity” concerns the GO hierarchy rather than organism taxonomy. Neither should be presented as an alternative implementation of GO taxon constraints.

## Why FunTaxIS-lite does not remove the case for GOaudit

The tools begin with different questions.

| Question | FunTaxIS-lite | GOaudit |
|---|---|---|
| What is the main object being produced? | A taxon-specific constraint resource | An audit of a supplied association table |
| What are the heavy inputs? | Global GOA GAF, GO-Plus OWL, NCBI Taxonomy, taxon/species lists and optional manual constraints | Released GO ontology/constraints/groupings and NCBI Taxonomy; the user's two-column table |
| Does it infer new constraints? | Yes. A sufficiently frequent GO term absent from a reference taxon can generate a propagated `never_in` rule, subject to its reference-node and priority scheme | No. A term is excluded only when it violates the selected official GO release |
| Main strength | Much broader constraint coverage; the paper reports an average 300% extension over GOC constraints | Conservative interpretation, simple deployment, row-level traceability and exact reference provenance |
| Main trade-off | Additional power depends on annotation completeness and the chosen closed-world assumptions, which are particularly consequential for under-studied taxa | Official constraints are incomplete, so many biologically implausible terms will pass |
| Direct handling of the researcher's protein–GO rows | Not its primary interface; users obtain/generate prohibited-term lists and apply them downstream | Core interface and output |
| Ontology-version hygiene | Constraints depend on the GO/GOA/taxonomy releases used to regenerate them | Alternative, obsolete and unknown identifiers are reported separately on every run |

These are complementary design choices. GOaudit should not claim greater biological coverage. It must also acknowledge explicitly that FunTaxIS-lite already catches the motivating salivary-gland term for *S. pistillata*. Conversely, FunTaxIS-lite's greater coverage and downloadable taxon lists do not provide the same conservative, release-frozen association-row audit trail for a heterogeneous researcher-generated table.

For version 1, retaining the official-only policy is strategically sensible. Importing inferred FunTaxIS-lite rules by default would blur the clearest distinction and make the tool data-heavy. Interoperability with an explicitly labelled external constraint set could be a later optional feature, provided official and inferred findings remain separable.

### Preliminary, unmatched-release overlap check

A diagnostic comparison confirms both substantial overlap and substantial policy/release differences. The public FunTaxIS-lite list used for *S. pistillata* is the Cnidaria reference-node list. It contains 14,745 GO terms, including GO:0035070. When compared with the current GOaudit reference snapshot:

| Term-set comparison | Count |
|---|---:|
| FunTaxIS-lite entries still current in the GOaudit ontology | 13,161 |
| FunTaxIS-lite entries now obsolete | 1,584 |
| Current GOaudit official-only forbidden terms for *S. pistillata* | 6,278 |
| Current terms in both sets | 5,000 |
| GOaudit only | 1,278 |
| FunTaxIS-lite only | 8,161 |
| Jaccard similarity | 0.346 |

Applying those unmatched-release term sets to the current, non-obsolete coral eggNOG-mapper associations gave:

| Association classification | Count |
|---|---:|
| Flagged by both | 55,347 |
| GOaudit only | 35,573 |
| FunTaxIS-lite only | 67,906 |
| Neither | 1,362,747 |

These numbers are **diagnostic, not manuscript-ready performance results**. The web list reports a 19 January 2024 data update, whereas GOaudit used a 2026 GO snapshot; FunTaxIS-lite also combines inferred/manual and GOC constraints. The comparison therefore mixes release drift with policy differences. Its value is to show why a controlled same-release, GOC-only and full-policy comparison is essential. The exact diagnostic logic and input checksums can be regenerated with [`analysis/compare_funtaxis_goaudit.py`](analysis/compare_funtaxis_goaudit.py).

## Suitability for a BMC Bioinformatics Software article

**Suitable in principle, but the current software and single-coral demonstration are not yet sufficient.** BMC Bioinformatics states that a Software article should be broadly useful and a significant advance over published software, usually shown by direct comparison. The conceptual algorithm here is existing GO constraint logic, and the closest published tool already detects the sentinel coral term. The claimed advance must therefore be demonstrated as a usable and reproducible research workflow.

The strongest paper is not “we invented taxon filtering”. It is:

> Taxon-incompatible GO associations persist in contemporary non-model-organism annotation exports, and GOaudit provides a conservative, source-independent and auditable bridge between the official GO constraint release and the flat association tables used for downstream analysis.

This becomes persuasive if the manuscript demonstrates all four parts:

1. **Need:** violations persist in real outputs, including after a taxonomically credible orthology hit.
2. **Conformance:** GOaudit agrees with an authoritative implementation on a frozen official-rule test set, with every discordance explained.
3. **Distinct workflow value:** users can audit ordinary exports without fabricating evidence/reference fields, rerunning annotation, using a licensed GUI or regenerating a global constraint database.
4. **Biological consequence:** filtering changes at least one downstream result in a controlled and interpretable way, while compatible annotations are retained.

Without direct comparisons and a multi-taxon validation set, a reviewer could reasonably describe GOaudit as a convenient wrapper around an existing rule. With them, it can be presented as a focused interoperability/QC contribution of broad utility.

## Minimum comparison study for submission

### 1. Frozen conformance benchmark

Create a public set spanning at least cnidarian, arthropod, plant, fungus, bacterium, vertebrate and one difficult non-model lineage. Include:

- known valid and invalid `in_taxon` cases;
- known valid and invalid `never_in_taxon` cases;
- GO union-taxon constraints;
- multiple constraints on one term;
- primary, alternative, obsolete and unknown GO IDs; and
- current, merged and deleted NCBI taxids.

Freeze one GO and one NCBI Taxonomy snapshot. Convert the same records to valid GAF/GPAD and compare GOaudit with Ontobio Rule 13 and, if practical, OWLTools. Report exact agreement, not merely total counts, and adjudicate every disagreement. Because the official constraint release is the specification, this is a conformance test rather than a claim of biological ground truth.

### 2. FunTaxIS-lite comparison

For the same taxa, compare:

- the overlap between GOaudit official violations and the GOC-derived portion of FunTaxIS-lite;
- additional FunTaxIS-lite-only prohibitions;
- conflicts or absences caused by different release dates; and
- a blinded biological review of a stratified sample of additional inferred findings.

Report set overlap and per-association effects, but do not equate “more terms filtered” with greater accuracy.

### 3. Workflow and resource benchmark

Record install commands, required input fields, downloads, wall time, peak memory, output types, offline reproducibility and how each tool records reference versions. Include OmicsBox as a documented feature/workflow comparison; if a licence is available, run the same imported annotations and compare exported decisions.

### 4. Real-data and downstream benchmark

Use the coral data plus several public proteomes annotated through at least eggNOG-mapper and InterProScan. Report association-, term- and protein-level findings by source and namespace. Re-run the motivating enrichment with an identical gene universe and statistical method before and after filtering. Manually inspect leading violations and a compatible negative-control set.

GAEF is worth running on the same proteomes, but it should be presented as answering a complementary system-level question rather than as a head-to-head target-taxon classifier.

## Claims to use and avoid

### Defensible

- “GOaudit fills an interoperability gap between official GO taxon-constraint releases and flat association tables produced in non-model-genome workflows.”
- “The methodological contribution is operational and reproducibility-focused rather than a new taxon-constraint formalism.”
- “GOaudit applies a conservative official-only policy; passing associations are not thereby proven correct.”
- “The underlying protein hit can remain credible even when one transferred GO association is taxonomically incompatible.”

### Avoid

- “The first tool to filter GO annotations by taxon.”
- “No other software checks GO taxon constraints.”
- “GOaudit is more accurate than FunTaxIS-lite” without a biological benchmark.
- “All implausible GO terms are removed.”
- “A constraint violation proves the protein prediction or homology is wrong.”

## Recommended paper title

**GOaudit: reproducible taxon-constraint auditing of flat Gene Ontology association tables**

This title makes the distinctive object and contribution explicit. “For non-model organisms” can remain in the abstract and case study without implying that the logic is limited to those taxa.

## Key primary sources

- Gene Ontology Consortium. [Taxon constraints in the Gene Ontology](https://geneontology.org/docs/taxon-constraints/).
- Deegan JI, Dimmer EC, Mungall CJ. [Formalization of taxon-based constraints to detect inconsistencies in annotation and ontology development](https://doi.org/10.1186/1471-2105-11-530). *BMC Bioinformatics*. 2010.
- Bianca F, Ispano E, Gazzola E, Lavezzo E, Fontana P, Toppo S. [FunTaxIS-lite: a simple and light solution to investigate protein functions in all living organisms](https://doi.org/10.1093/bioinformatics/btad549). *Bioinformatics*. 2023.
- FunTaxIS-lite. [Public Cnidaria prohibited-term list](https://www.medcomp.medicina.unipd.it/funtaxis-lite/static/constraints_lists/6073_Cnidaria_constraints.txt) (contains GO:0035070; checked 14 July 2026).
- Ontobio developers. [Command-line GO Rules documentation](https://ontobio.readthedocs.io/en/latest/commandline.html).
- OmicsBox. [GO Annotation user manual](https://docs.omicsbox.biobam.com/latest/Gene-Ontology-Annotation/).
- Tawfiq R, Kulmanov M, Hoehndorf R. [Evaluating completeness, coherence, and consistency of genome-scale function annotations](https://doi.org/10.1093/bib/bbag336). *Briefings in Bioinformatics*. 2026.
- Wei X, Zhang C, Freddolino L, Zhang Y. [Detecting Gene Ontology misannotations using taxon-specific rate ratio comparisons](https://doi.org/10.1093/bioinformatics/btaa548). *Bioinformatics*. 2020.
- Ontology Access Kit. [Taxon-constraint command documentation](https://incatools.github.io/ontology-access-kit/cli.html).
- QuickGO. [REST API documentation](https://www.ebi.ac.uk/QuickGO/api/index.html).
- Lavezzo E, Falda M, Fontana P, Bianco L, Toppo S. [Enhancing protein function prediction with taxonomic constraints—the Argot2.5 web server](https://doi.org/10.1016/j.ymeth.2015.08.021). *Methods*. 2016.
- Törönen P, Holm L. [PANNZER—a practical tool for protein function prediction](https://doi.org/10.1002/pro.4193). *Protein Science*. 2022.
- Zhapa-Camacho F, Mashkova O, Hoehndorf R, Kulmanov M. [LLM Agent Based Protein Function Prediction](https://psb.stanford.edu/psb-online/proceedings/psb26/zhapa-camacho.pdf). *Pacific Symposium on Biocomputing*. 2026.
- BMC Bioinformatics. [Software article criteria and manuscript requirements](https://link.springer.com/journal/12859/submission-guidelines/software-article/).
