# Changelog

This project follows [Semantic Versioning](https://semver.org/).

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
