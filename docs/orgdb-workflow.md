# Validated OrgDb workflow

The supplied EGAPx files support a reliable mapping chain:

```text
annotation protein_id
  -> GFF CDS protein_id
  -> CDS Parent transcript
  -> transcript Parent gene
  -> gene locus_tag (OrgDb GID)
```

GOaudit deliberately supports this explicit EGAPx/RefSeq-style GFF3 schema rather than guessing arbitrary identifiers. Every `gene` needs `ID` and `locus_tag`, every protein-coding `mRNA`/`transcript` needs `ID` and `Parent`, and every `CDS` needs `protein_id` and `Parent`. Repeated CDS rows for a multi-exon protein are expected. A protein must resolve to exactly one transcript and one gene.

The only automatic identifier normalization is documented and collision-checked: `gnl|WGS:ZZZZ|example_003494-P1` may match `example_003494-P1` by taking the text after the final pipe. GOaudit refuses the GFF if that normalization is ambiguous.

## 1. Convert annotation sources

```bash
goaudit convert-interpro \
  interproscan.results.tsv \
  annotations.interpro.tsv

goaudit convert-eggnog \
  proteins.emapper.annotations \
  annotations.eggnog.tsv
```

## 2. Validate the selected sources

Pass one or more two-column files. Keeping InterProScan separate from the combined sensitivity analysis makes their results reproducible.

```bash
goaudit validate \
  annotations.interpro.tsv \
  annotations.eggnog.tsv \
  --taxid 50429 \
  --output-dir results/combined_goaudit \
  --mode report
```

## 3. Prepare AnnotationForge inputs

Use `audit.tsv`, not `annotations_filtered.tsv`. The audit allows GOaudit to include only current valid terms and resolved alternate IDs; obsolete, unknown, and taxon-violating terms are excluded.

```bash
goaudit prepare-orgdb \
  results/combined_goaudit/audit.tsv \
  --gff genomic.gff \
  --output-dir results/orgdb_inputs
```

The default requires 100% of retained annotation proteins to map. A lower threshold can be selected explicitly with `--min-mapping-coverage`, but the unmapped identifiers must be reviewed.

Outputs are:

- `gene_info.tsv`: `GID`, `SYMBOL`, and `GENENAME`.
- `chromosome.tsv`: `GID` and `CHROMOSOME`.
- `go.tsv`: deduplicated `GID`, `GO`, and `EVIDENCE` rows.
- `protein_to_gene.tsv`: the complete, inspectable identifier chain and match method.
- `unmapped_proteins.tsv`: retained annotation proteins that could not be mapped.
- `mapping_summary.tsv/json`: coverage and table statistics.

## 4. Build the OrgDb in R

Install `AnnotationForge` using the Bioconductor release appropriate for the installed R version, then run:

```bash
Rscript scripts/build_orgdb.R \
  results/orgdb_inputs \
  . \
  50429 \
  Stylophora \
  pistillata \
  0.1.0 \
  "Andreas Bachler <Andy.Bachler@csiro.au>"
```

`AnnotationForge::makeOrgPackage()` requires the first column of every annotation table to be the common `GID`; the preparation stage enforces that contract. The generated source package can be installed with `R CMD INSTALL <package-directory>` and queried using `AnnotationDbi::keys()`, `columns()`, and `select()`.

The builder also compares every term with the installed `GO.db`. A current GO release can occasionally contain terms that have not yet reached the Bioconductor release's `GO.db`; those rows are explicitly written to `go_not_in_GO_db.tsv`, excluded before AnnotationForge runs, and counted in `orgdb_build_manifest.tsv`. Keeping this report is essential for a reproducible build.

## Review of the original Rmd

The supplied Rmd is scientifically thoughtful and its mapping happens to be exact for these files, but the following parts should not become the public reusable interface:

- It silently keeps the first protein mapping after sorting, which can hide ambiguity.
- Its regex fallback derives a gene ID from a protein string without proving that the transformation is collision-free.
- Unmapped annotations are counted and then discarded rather than causing a configurable failure.
- The manually listed lineage omits current intermediate taxa (`Vacatina`, `Pocilloporidae`, and `Stylophora`), which could incorrectly reject terms constrained at those levels.
- It independently downloads and interprets taxon constraints, potentially using a different release from GO.db and from the Python QC.
- The full 184 MB GFF is imported more than once, increasing R memory use.

The enrichment and plotting sections can continue to consume the resulting OrgDb. The reusable package-building portion is safer as the small validated pipeline above.

## Path to Bioconductor

There are two distinct distributable products:

1. **GOaudit software package:** reusable validation and OrgDb-input preparation functions, tests, documentation, and a vignette.
2. **Organism annotation package:** a versioned `org.Spistillata.eg.db` database built from a declared genome annotation and GO release.

Before submission, the R-facing software should become a conventional package with `DESCRIPTION`, `NAMESPACE`, documented functions under `R/`, `testthat` tests, at least one executable vignette, `NEWS`, and `CITATION`. Development should use Bioconductor devel and pass `R CMD build`, `R CMD check`, `BiocCheck::BiocCheckGitClone()`, and `BiocCheck::BiocCheck(..., new-package=TRUE)` without errors or warnings. The software package is submitted through the Bioconductor contributions review process. Maintaining it includes responding to build failures and updating it across Bioconductor releases.

The generated Stylophora SQLite is hundreds of megabytes and must **not** be committed inside an ordinary software-package repository: current Bioconductor guidance limits built source packages to roughly 10 MB and individual software-package files to 5 MB. A public organism annotation resource should therefore be proposed as an annotation package backed by `AnnotationHub`. New annotation packages follow a separate route: contact the Bioconductor annotation/hub team (`packages@bioconductor.org` or `hubs@bioconductor.org`) with the proposal and use their current hub-package guidance. The small GOaudit software package and the large versioned OrgDb resource should remain separate submissions.
