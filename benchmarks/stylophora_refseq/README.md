# Stylophora RefSeq taxon-constraint benchmark

Status: preliminary reproducible benchmark, 14 July 2026 (Australia/Sydney).

This benchmark evaluates what currently available open tools actually do with
the *Stylophora pistillata* RefSeq annotations. It is deliberately not framed
as an accuracy competition: the tools answer different biological questions,
and several use different GO releases.

## Bottom line

- The supplied RefSeq files map cleanly: every one of the 32,879 FASTA protein
  accessions occurs in the GFF3, and all 17,064 GO-annotated GeneIDs map to at
  least one protein.
- GOaudit reports 203 taxon-constraint violations among 59,306 unique gene-GO
  associations, together with 1,871 associations to 305 terms that have become
  obsolete since the GAF's declared 2023 GO release.
- The deployed 2024 FunTaxIS-lite Cnidaria catalogue flags 583 RefSeq
  associations. Of the 57,435 current, non-obsolete RefSeq associations, 101
  are flagged by both tools, 102 only by GOaudit, and 424 only by FunTaxIS-lite.
  This difference is expected because FunTaxIS-lite adds empirical and manual
  restrictions and the releases are not matched.
- A locally regenerated 2026 FunTaxIS-lite `goc` list contains only 83 terms
  and flags three RefSeq associations. It misses `GO:0035070` because the
  current GO-plus OWL represents that constraint as `in taxon Arthropoda`, and
  the FunTaxIS-lite GOC code path explicitly skips normalized `in taxon`
  relations before propagation.
- Ontobio accepts all 66,933 original GAF rows and reports zero Rule 13 messages
  when no external Gaferencer inference JSON is supplied. This is expected from
  its implementation, rather than evidence that the annotations are valid.
- OAK correctly retrieves the current constraints for the sentinel, but is a
  term-level constraint service rather than a GAF-plus-taxid validator.
- GAEF declares the full annotation set taxonomically inconsistent, but accepts
  a one-association `GO:0035070` positive control because it tests whether the
  annotations imply mutually satisfiable taxa and does not compare them with
  taxid 50429.

The clearest remaining niche for GOaudit is therefore a small post-annotation
workflow with the explicit contract:

> association table + declared target taxid -> one transparent decision per
> association, ontology-ID maintenance, reproducible reference provenance and
> optional cleaned output.

## Contained installation layout

All downloaded software, environments, package caches, temporary homes and
large outputs are under:

```text
/scratch3/bac050/2026_bioinfo_tool/
├── data/stylophora_refseq_v1.1/
├── tools/bin/
├── tools/cache/
├── tools/envs/
├── tools/home/
├── tools/mamba/
├── tools/src/
├── logs/tool_benchmark/
└── results/tool_benchmark/
```

Micromamba 2.8.1 is installed at `tools/bin/micromamba`. The install/run
environment variables are recorded in `scratch_env.sh`. The pre-existing
`/home/bac050/.cache` and `/home/bac050/.conda` directory modification times
predate this benchmark.

The completed GAEF command used a scratch-local HOME. Runtime inspection
confirmed Plotly 6.9.0, pandas 3.0.3, NumPy 2.4.6, Requests 2.34.2 and Flask
3.1.3 were imported from `tools/envs/gaef`; the diagnostic appearance of older
packages in the normal shell did not affect the benchmark. Ontobio, OAK and
FunTaxIS-lite likewise used redirected homes and scratch-local dependencies.

## Input data and mapping QC

The three files came from NCBI assembly `GCF_002571385.2` and match NCBI's
published MD5 manifest.

| Input | SHA-256 |
|---|---|
| Protein FASTA | `bfbb681b97609d4828705da786fd3a1e223a918f584ef0dbf0f9ca117241ac82` |
| GO GAF | `e72dfee4245cb78d1653420547ea506926f2b24e84fe6e5a5bdc50f127a902a5` |
| Genomic GFF3 | `edd8ce70914927552608f0857df1c187c22076ec22694e49e61f09a7b441319e` |

The GAF declares:

```text
GAF version        2.2
Generated          2023-12-02
GO version         2023-07-27
InterProScan       5.64-96.0
PANTHER            17.0
Taxon              50429
Evidence           66,933 / 66,933 IEA
```

The file is not solely an InterProScan annotation set. The `With/From` fields
contain InterPro, PANTHER and UniProtKB sources. Source counts can overlap when
a row names more than one source.

| Mapping/QC measure | Result |
|---|---:|
| FASTA proteins | 32,879 |
| FASTA proteins represented in GFF3 | 32,879 (100%) |
| Original GAF rows | 66,933 |
| Unique gene-GO associations | 59,306 |
| Annotated GeneIDs | 17,064 |
| Annotated GeneIDs mapped through GFF3 | 17,064 (100%) |
| Unique GO identifiers | 5,219 |
| Protein-expanded associations | 84,250 across 23,489 proteins |
| Genes with multiple protein products | 4,669 |
| `GO:0035070` in RefSeq GAF | absent |

The gene-level table is the primary comparison input because the NCBI GAF is
gene-centred. Expanding every gene annotation to every encoded isoform is useful
for protein-oriented workflows, but would inflate association counts and make
comparison with the original GAF less direct.

## Results

### GOaudit

GOaudit 0.1.0 was run against taxid 50429 using GO release
`releases/2026-06-15` and the GO/NCBI reference manifest updated on 13 July
2026 UTC.

| Measure | Result |
|---|---:|
| Assessed associations | 59,306 |
| Valid/current | 57,232 |
| Taxon violations | 203 (0.342%) |
| Unique violating terms | 70 |
| Genes with a violation | 186 |
| Obsolete associations | 1,871 (3.155%) |
| Unique obsolete terms | 305 |
| Unknown identifiers | 0 |
| Wall time | 4.35 s |
| Peak RSS | 103,412 kB |

The most frequent flags are `syntaxin binding` (26), `central nervous system
development` (24), `inflammatory response` (17), `lipopolysaccharide
biosynthetic process` (14), and `actin cortical patch` (11). The source GAF
rows contributing violations name PANTHER 116 times, UniProtKB 74 times and
InterPro 30 times; some rows name more than one database.

Outputs:

```text
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/goaudit_refseq/
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/goaudit_refseq_source/
/scratch3/bac050/2026_bioinfo_tool/logs/tool_benchmark/goaudit_refseq.time.txt
```

### FunTaxIS-lite

The source checkout is commit
`472c31e57e2493923f133d7f6bb4edcad760d6a0`; its Python 3.9 environment is at
`tools/mamba/envs/funtaxis-lite`.

Two policies were evaluated:

1. The deployed Cnidaria catalogue from the public service, dated 19 January
   2024. It contains 14,745 identifiers, of which 1,584 are obsolete in current
   GO, and combines GOC, manual and empirical restrictions.
2. A local `type: goc` regeneration using GO-plus build 19 June 2026 and the
   same NCBI taxonomy snapshot as GOaudit. This produces 83 terms.

| Dataset | Rows | Public 2024 flagged | Local 2026 GOC flagged |
|---|---:|---:|---:|
| RefSeq gene-GO | 59,306 | 583 (0.983%) | 3 (0.005%) |
| Existing eggNOG protein-GO | 1,796,068 | 128,242 (7.140%) | 179 (0.010%) |
| One-row `GO:0035070` control | 1 | 1 | 0 |

The public catalogue catches all 46 eggNOG occurrences of `GO:0035070` plus
the one-row sentinel. It does not expose per-term rule provenance, so the catch
cannot be assigned confidently to a GOC, manual or empirical rule. The local
GOC miss was traced to
`src/taxonConstraintsGOconsortium.py`: current GO-plus supplies the term as
`RO:0002162` / `in taxon Arthropoda`, and lines 51-54 skip that relation.

The two local FunTaxIS stages took 72.38 s and 98.91 s and peaked at 9.71 GB and
12.22 GB RSS. A new full empirical build was not attempted because the current
all-UniProt GAF alone is 11.66 GB compressed and would construct a different
2026 empirical resource rather than reproduce the public 2024 database.

Detailed report:

```text
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/funtaxis/README.md
```

### Ontobio GO Rules Engine

Ontobio 2.9.12 is installed in `tools/envs/ontobio`. Running Rule 13 against
the original GAF without a Gaferencer inference file:

| Measure | Result |
|---|---:|
| GAF associations accepted | 66,933 / 66,933 |
| Rule 13 messages | 0 |
| Wall time | 18.35 s |
| Peak RSS | 141,228 kB |

This is not a contradictory biological result. The current Rule 13
implementation returns pass when `annotation_inferences` is absent. The CLI's
`-T NCBITaxon:50429` option checks whether row taxa are allowed; it does not
evaluate each GO class against taxon 50429. Consequently, an external
Gaferencer JSON is required for an operational taxon-constraint comparison.

Outputs:

```text
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/ontobio/
```

### Ontology Access Kit

OAK/oaklib 0.7.2 is installed in `tools/envs/oak`. Its live GO SQLite resource
is cached under `tools/cache/pystow/oaklib/` rather than in home. The install
required pinning `pronto==2.7.3`: the unconstrained freshly resolved pronto
0.12.2 failed on Python 3.12, and the resulting environment retains a
non-blocking PyShExC/chardet dependency warning.

OAK reports:

- `GO:0035070`: only in Arthropoda;
- `GO:0019905`: only in Bacteria.

This independently confirms the current constraint data, but OAK does not take
the association table and one target taxid or emit a cleaned table. The first
download plus sentinel lookup took 75.22 s and 518 MB RSS; a cached two-term
lookup took 63.56 s and 517 MB RSS on the shared filesystem.

Outputs:

```text
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/oak/
```

### GAEF

GAEF was installed from commit
`4dcde53819bdd205918f154865ab232db0046fba`
(`v1.0.0-7-g4dcde53`) in `tools/src/GAEF`, with its environment in
`tools/envs/gaef`.

Its broader report for the coral annotations gives:

| GAEF measure | Result |
|---|---:|
| Essential-function completeness | 100.0% |
| Process (`has_part`) coherence | 45.96% |
| Complex coherence | 80.48% |
| MetaCyc pathway coherence | 50.48% (53/105 pathways) |
| Taxonomic satisfiability | false |

The full set is unsatisfiable because its annotations jointly imply mutually
disjoint taxa. In contrast, the one-association `GO:0035070` test is reported
`IsSatisfiable=true`: Arthropoda is internally consistent when no declared
coral taxid is supplied.

GAEF documents essential-function completeness as a bacterial-genome metric,
so its 100% coral value is not interpreted here as validated cnidarian genome
completeness. Its official GAF converter groups column 2 (GeneID in this file)
despite describing it as a protein accession; repeated entity rows must be
grouped first because GAEF's loader replaces rather than merges them.

| Stage | Wall time | Peak RSS |
|---|---:|---:|
| Python report | 42.60 s | 4.31 GB |
| Full-set Groovy taxon reasoning | 4 min 7.69 s | 14.29 GB |
| One-term Groovy control | 2 min 45.73 s | 13.99 GB |

These timings are operational observations, not fair performance comparisons:
GAEF produces a much broader report than GOaudit. Current large outputs remain
in scratch under `tools/src/GAEF`, including a 1.07 GB HTML
report and a 506 MB JSON report. Concise taxon outputs and timing files are in:

```text
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/gaef/
```

### QuickGO API

A live API query independently returned `only_in_taxon Arthropoda` for
`GO:0035070` and `only_in_taxon Bacteria` for `GO:0019905`. The response and
HTTP headers are archived in:

```text
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/quickgo/
```

QuickGO is an API lookup rather than installable association-cleaning software.

## A current upstream GO constraint problem

Current GO, QuickGO and OAK all expose `GO:0019905 syntaxin binding` as only in
Bacteria. GOaudit therefore flags 26 unique coral gene-GO associations (29 GAF
source rows). However, the linked GO ontology issue ends with the curator
stating that **never in Bacteria** had been added. The live GO source instead
contains `is_a: onlyin:2`, which produces the opposite restriction.

This appears to be an upstream ontology-source error, not a GOaudit parsing
error. It should be reported to the Gene Ontology maintainers before these 26
associations are removed. It also demonstrates why GOaudit should remain
report-first and retain the exact constraint behind every decision.

Issue: <https://github.com/geneontology/go-ontology/issues/31404>

## Reproduction helpers

- `prepare_inputs.py` validates the GAF, GFF3 and FASTA, writes matched
  gene-level and protein-expanded tables, and records source hashes and mapping
  coverage.
- `annotate_gaf_sources.py` links GOaudit decisions back to GAF evidence,
  reference and `With/From` fields.
- `scratch_env.sh` redirects package managers, caches, temporary files and home
  directories into scratch.
- `../../manuscript/analysis/compare_funtaxis_goaudit.py` calculates the
  current-term and association-level FunTaxIS/GOaudit overlaps and can save JSON
  with `--output`.

The machine-readable input summary is:

```text
/scratch3/bac050/2026_bioinfo_tool/results/tool_benchmark/prepared/input_summary.json
```

## What is ready for publication, and what is not

Ready as evidence:

- exact RefSeq/GFF/FASTA identifier mapping and input statistics;
- GOaudit's transparent current-reference audit;
- the deployed FunTaxIS-lite user experience and its sentinel outcome;
- Ontobio's documented external-inference requirement;
- OAK's role as a term-level building block;
- GAEF's different no-target-taxon consistency question.

Still required before manuscript submission:

1. Archive explicit environment locks for every comparator.
2. Report the syntaxin constraint error upstream and rerun after resolution.
3. Ask the FunTaxIS-lite authors whether current `in taxon` constraints are
   intentionally excluded or whether their parser needs updating.
4. Build a small multi-taxon gold-standard conformance suite using a single
   pinned GO/taxonomy release.
5. Keep deployed-policy comparisons separate from same-release semantic
   conformance comparisons.

## Primary software sources

- FunTaxIS-lite: <https://github.com/MedCompUnipd/FunTaxIS-lite>
- Ontobio: <https://github.com/biolink/ontobio>
- OAK: <https://incatools.github.io/ontology-access-kit/cli.html>
- GAEF: <https://github.com/bio-ontology-research-group/GAEF>
- QuickGO API: <https://www.ebi.ac.uk/QuickGO/api/index.html>
- GO taxon constraints: <https://geneontology.org/docs/taxon-constraints/>
