# Changelog

This project follows [Semantic Versioning](https://semver.org/).

## 0.2.2 - 2026-08-07

- Remove local HPC scratch paths from the README and `docs/`; `--data-dir` is
  optional and defaults to `~/.cache/goaudit`.
- Replace `test_data/` paths and the EGAPx identifier in worked examples with
  neutral placeholders, so documented commands work in a fresh clone.
- Align the declared package version with the release tag. Versions 0.2.0 and
  0.2.1 both reported `0.2.0` from `goaudit --version`.

## 0.2.0 - 2026-08-07

- Add the matched eggNOG-mapper option matrix benchmark
  (`benchmarks/stylophora_annotation_controls/`), separating alignment
  stringency, annotation scope and donor restriction on one RefSeq proteome.
- Add `summarise_eggnog_matrix.py` and `compare_eggnog_interproscan.py` for
  collating the matrix and quantifying information overlap between annotation
  workflows under GO ancestor closure.
- Track benchmark provenance (checksums, tool versions, resource use, GOaudit
  summaries) that a `results/` ignore rule had previously excluded.
- Replace the EGAPx-derived example with `examples/stylophora_example.tsv`,
  built from public RefSeq identifiers.
- Add the preprint under `manuscript/preprint/`.

## 0.1.0 - 2026-07-28

Initial research-software release.

- Audit strict two-column protein–GO annotation tables against current GO
  computed taxon constraints and NCBI Taxonomy.
- Report valid, taxon-incompatible, obsolete, unknown and alternate GO IDs.
- Produce summary tables and dependency-free SVG plots.
- Convert eggNOG-mapper and InterProScan output to the strict input schema.
- Prepare validated EGAPx/RefSeq mappings for an optional `AnnotationForge`
  `OrgDb` package workflow.
- Include the *Stylophora pistillata* `GO:0035070` sentinel test and comparative
  benchmark documentation.
