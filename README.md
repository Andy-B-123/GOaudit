# GOaudit

GOaudit is a small command-line quality-control layer for automated Gene Ontology (GO) annotations. It asks a deliberately narrow question: **is each GO term compatible with the taxonomy of the organism being annotated?**

Annotation transfer can preserve a real homology while transferring biologically inappropriate metadata. The motivating example is `GO:0035070` (*salivary gland histolysis*) appearing in coral eggNOG-mapper results. GO restricts this term to Arthropoda, so GOaudit reports it as a taxon-constraint violation for *Stylophora pistillata* (NCBI taxid `50429`) without questioning the underlying protein hit.

GOaudit uses the official GO computed taxon constraints and NCBI Taxonomy. It does not invent constraints or infer organism biology from names.

## Install

Python 3.10 or newer is required. There are no runtime dependencies.

Install the current development release directly from GitHub:

```bash
python -m pip install "goaudit @ git+https://github.com/Andy-B-123/GOaudit.git"
```

For a local checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Download the current reference data once. For the supplied project, the requested large-data location is:

```bash
goaudit update --data-dir /scratch3/bac050/2026_bioinfo_tool/goaudit_cache
```

The update contains `go.obo`, GO's computed constraints and taxon groupings, NCBI `nodes.dmp`, `names.dmp`, and `merged.dmp`. A manifest records source URLs, retrieval time, and SHA-256 checksums.

## Input

Input is intentionally strict: a tab-separated file with exactly two columns, one protein–GO association per row.

```text
protein_id	go_id
egapxtmp_003494-P1	GO:0035070
protein_2	GO:0003677
```

The header is optional. GO IDs must have the form `GO:0000000`. Comma-separated terms and additional columns are rejected; use one row per association.
A runnable one-row coral example is provided at
[`examples/stylophora_sentinel.tsv`](examples/stylophora_sentinel.tsv).

## Convert eggNOG-mapper output

The converter finds the `#query` and `GOs` columns, expands comma-separated GO lists, ignores `-`, and writes the strict GOaudit format:

```bash
goaudit convert-eggnog \
  test_data/eggnog_results/complete.proteins.emapper.annotations \
  /scratch3/bac050/2026_bioinfo_tool/stylophora.eggnog.go.tsv
```

By default, pipe-prefixed identifiers such as `gnl|WGS:ZZZZ|egapxtmp_003494-P1` become `egapxtmp_003494-P1`. Use `--id-mode full` to preserve the complete eggNOG query identifier.

InterProScan TSV output can be converted in the same way:

```bash
goaudit convert-interpro interproscan.tsv annotations.interpro.tsv
```

## Validate

The safe default reports problems but does not create a filtered annotation set:

```bash
goaudit validate annotations.tsv \
  --taxid 50429 \
  --data-dir /scratch3/bac050/2026_bioinfo_tool/goaudit_cache \
  --output-dir results \
  --mode report
```

Modes are:

- `report`: write the audit, statistics, and plots.
- `flag`: also write `annotations_flagged.tsv`, with status and reason columns.
- `remove`: also write `annotations_filtered.tsv`, excluding taxon-constraint violations only.

Obsolete and unknown GO IDs are reported independently and are retained in `remove` mode. This keeps taxonomic filtering distinct from ontology-version cleanup. Alternate GO IDs are resolved to their current primary IDs. Add `--fail-on-violation` when a pipeline should return exit status 2 if violations are detected. Existing output directories are protected unless `--force` is supplied.

## Output

Each run creates:

- `audit.tsv`: one row per input association, including term name, namespace, status, constraint, and explanation.
- `summary.tsv` and `summary.json`: annotated proteins, annotation rows, unique terms, valid rows, taxon violations, affected proteins, obsolete terms, unknown terms, and alternate IDs.
- `status_counts.svg`: valid, violating, obsolete, and unknown annotation counts.
- `namespace_counts.svg`: biological process, molecular function, and cellular component counts.
- `top_taxon_violations.svg`: the ten most frequent incompatible terms.
- `reference_manifest.json`: exact reference-data provenance when the data were obtained with `goaudit update`.

`mode=remove` additionally produces the original two-column format, ready for enrichment or downstream database construction.

## Constraint semantics

GOaudit reads `in_taxon` (`RO:0002162`) and `never_in_taxon` (`RO:0002161`) from GO's released computed constraint file. Constraints are checked against the target taxon's complete NCBI lineage. GO union taxon classes are expanded using the official grouping file. Since GO now materializes inherited constraints on each affected term, GOaudit does not need to approximate propagation over `is_a` or `part_of` relationships.

The statuses are quality-control findings, not claims that a homology or protein annotation method is wrong. A violation means that the GO association is inconsistent with the current GO taxon-constraint release and should be reviewed or excluded from taxon-specific interpretation.

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The test suite includes the expected coral failure for `GO:0035070` and the corresponding valid arthropod case.

## Build a non-model-organism OrgDb

`goaudit prepare-orgdb` validates an EGAPx/RefSeq GFF3 protein-to-gene hierarchy and writes clean `AnnotationForge` input tables plus complete mapping QC. See the [validated OrgDb workflow](docs/orgdb-workflow.md) for conversion, combined-source validation, R package construction, review of the supplied Rmd, and the route toward Bioconductor submission.

## Benchmarks

- [`benchmarks/stylophora_refseq/`](benchmarks/stylophora_refseq/) compares
  GOaudit with FunTaxIS-lite, Ontobio, OAK and GAEF on the RefSeq coral
  annotation set.
- [`benchmarks/stylophora_deepgoplus/`](benchmarks/stylophora_deepgoplus/)
  runs a pretrained machine-learning GO predictor on the complete
  *Stylophora pistillata* proteome and audits its predictions.

## Reproducibility and citation

Retain `reference_manifest.json` with every analysis and report the GO release, NCBI taxid, GOaudit version, and selected mode. GO ontology and constraint data are provided by the Gene Ontology Consortium; taxonomy data are provided by NCBI.

The repository deliberately does not contain genome assemblies, protein FASTA
files, annotation GFF3 files, GAF files, InterProScan output, eggNOG-mapper
output, or downloaded GO/NCBI reference files. See
[`docs/data.md`](docs/data.md) for the public sources and reproducible download
workflow. This keeps installation small and prevents a benchmark dataset from
being mistaken for package data.

Please cite the software metadata in [`CITATION.cff`](CITATION.cff). A paper
citation can be added there once the manuscript is published.

GOaudit is an early research release. Constraint findings can expose ontology or taxonomy edge cases, so high-impact exclusions should be reviewed and possible GO constraint errors reported to the GO Consortium.

## Contributing and releasing

Bug reports and focused contributions are welcome; see
[`CONTRIBUTING.md`](CONTRIBUTING.md). Maintainer instructions for creating the
GitHub repository, checking the package and making a tagged release are in
[`PUBLISHING.md`](PUBLISHING.md).
