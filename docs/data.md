# Reference and benchmark data

GOaudit keeps data out of the Python package and Git repository. Installation
contains code only.

## GO and NCBI reference data

Download the current reference bundle with:

```bash
goaudit update --data-dir /path/to/goaudit_cache
```

This retrieves the official GO ontology, computed taxon constraints and taxon
groupings, plus the required NCBI Taxonomy dump files. GOaudit writes
`manifest.json` with source URLs, retrieval time and SHA-256 checksums. Keep a
copy of that manifest with every analysis.

The default cache is user-local (`~/.cache/goaudit`). On a shared or HPC system,
keep the downloaded data off the home filesystem by pointing `--data-dir` at a
larger volume:

```bash
goaudit update \
  --data-dir /path/to/goaudit_cache
```

## Stylophora benchmark inputs

The comparative benchmark uses NCBI RefSeq assembly
`GCF_002571385.2_Stylophora_pistillata_v1.1`. Download its compressed files
from NCBI rather than copying them into this repository:

- [protein FASTA](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/002/571/385/GCF_002571385.2_Stylophora_pistillata_v1.1/GCF_002571385.2_Stylophora_pistillata_v1.1_protein.faa.gz)
- [Gene Ontology GAF](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/002/571/385/GCF_002571385.2_Stylophora_pistillata_v1.1/GCF_002571385.2_Stylophora_pistillata_v1.1_gene_ontology.gaf.gz)
- [genomic GFF3](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/002/571/385/GCF_002571385.2_Stylophora_pistillata_v1.1/GCF_002571385.2_Stylophora_pistillata_v1.1_genomic.gff.gz)

Checksums, mapping QC, exact tool environments and result locations are
recorded in
[`benchmarks/stylophora_refseq/README.md`](../benchmarks/stylophora_refseq/README.md).
The NCBI source files are stable public inputs, so a second project-specific
archive is unnecessary. If a derived frozen dataset is needed for peer review,
deposit it in Zenodo or an institutional repository and record its DOI here.

## Tiny test data

Small synthetic inputs belong in `tests/`; the runnable motivating example is
in `examples/`. The ignored local `test_data/` directory may be used for
unpublished or genome-scale working data, but it must not be committed.
