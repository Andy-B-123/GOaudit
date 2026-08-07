# Matched annotation-workflow controls for GOaudit

Status: full-proteome runs completed 29 July 2026 (Australia/Sydney).

## Purpose

This benchmark tests whether GOaudit can consume Gene Ontology (GO)
associations generated from the same non-model-organism proteome by three
different evidence strategies:

1. DeepGOPlus hybrid machine-learning and sequence-similarity prediction;
2. eggNOG-mapper orthology transfer with explicit taxonomic controls; and
3. InterProScan protein-signature matching with GO cross-references reported
   by InterProScan.

It is a workflow and taxon-compatibility comparison, not an estimate of the
biological precision or recall of the annotation tools. Counts cannot be used
as an accuracy ranking because the tools differ in databases, evidence
filters, ontology releases and ancestor-propagation policies.

eggNOG-mapper and InterProScan were selected because they are established,
complementary routes used to annotate proteins from organisms without a
well-developed organism-specific GO resource. eggNOG-mapper exposes explicit
annotation-donor controls through `--target_taxa` and `--excluded_taxa`.
The GO Consortium documentation recommends InterProScan as one route for
assigning GO terms to novel protein sequences. InterProScan's `--goterms`
output retains source labels for mappings supplied by InterPro and PANTHER.

## Shared input and audit references

| Item | Value |
|---|---|
| Organism | *Stylophora pistillata* |
| NCBI taxid | `50429` |
| RefSeq assembly | `GCF_002571385.2` |
| Protein records | 32,879 |
| Unique protein sequences | 29,198 |
| Compressed RefSeq protein FASTA SHA-256 | `bfbb681b97609d4828705da786fd3a1e223a918f584ef0dbf0f9ca117241ac82` |
| Uncompressed analysis FASTA SHA-256 | `6cfedca33052f84d807d0658d64b8af3748117eb3186b9c2459d7951caac7fd4` |
| GOaudit | 0.1.0 |
| GO release used for audit | 15 June 2026 |

The exact same uncompressed FASTA used for the DeepGOPlus benchmark was
supplied to both control annotators. Both control outputs were converted to
the strict GOaudit representation without changing the protein identifier.

## eggNOG-mapper

eggNOG-mapper 2.1.12 was run with eggNOG 5.0.2 and DIAMOND 2.0.15. The main
annotation used a Metazoa scope with `inner_narrowest` selection and all
available GO evidence. Donors were restricted to Metazoa
(`--target_taxa 33208`) while Bilateria were excluded
(`--excluded_taxa 33213`). Search hits required bit score ≥40 and query and
subject coverage ≥20%.

Two sensitivity runs restricted donors to Cnidaria (`--target_taxa 6073`).
One used all GO evidence and the other retained only non-electronic evidence.

This is intentionally different from an earlier exploratory eggNOG-mapper run
that did not configure donor taxa. Only the matched non-bilaterian-donor run
is used in the main manuscript comparison; the Cnidaria-only runs are
sensitivity analyses.

Run scripts: `run_eggnog_cnidaria.slurm` (search and non-electronic
sensitivity run), `run_eggnog_cnidaria_all.slurm` (all-evidence Cnidaria
sensitivity run) and `run_eggnog_nonbilaterian.slurm` (main comparison).

## InterProScan

InterProScan 5.72-103.0 was run locally against all 22 signature libraries
enabled by that release. The precalculated-match service was disabled, and GO
cross-references were requested with `--goterms`. The native TSV labels these
cross-references `(InterPro)` or `(PANTHER)`; GOaudit's converter deliberately
standardizes both to GO identifiers. The run therefore depends only on the
archived local software/data release and input sequences.

Version 5.72-103.0 was the complete cluster installation available for this
benchmark, not the latest InterProScan release at the time of writing. It is
identified explicitly so that these results are not presented as a benchmark
of a newer release.

Run script: `run_interproscan.slurm`.

## eggNOG-mapper option matrix

The runs described above reused a seed-ortholog search that already applied
`--score 40 --query_cover 20 --subject_cover 20`, so they could not separate
hit stringency from donor policy. `scripts/run_eggnog_option_matrix.slurm`
repeats the comparison as a matched matrix on the identical RefSeq FASTA:
two DIAMOND searches (eggNOG-mapper defaults, and a stringent filter of
E-value ≤1e-10, bit score ≥60, identity ≥40%, query and subject coverage
≥50%) feed eight annotation passes through `-m no_search`. Completed 7 August
2026 in 53 min 17 s on 16 CPUs. Collate with
`scripts/summarise_eggnog_matrix.py`.

| Search | Annotation options | Proteins | Coverage | Associations | Unique terms | Taxon violations | Obsolete |
|---|---|---:|---:|---:|---:|---:|---:|
| Defaults | emapper defaults | 14,571 | 44.32% | 2,160,345 | 20,541 | 110,903 (5.134%) | 328,694 |
| Defaults | `--go_evidence all` | 15,893 | 48.34% | 2,353,479 | 21,022 | 113,013 (4.802%) | 368,014 |
| Defaults | `--tax_scope Metazoa`, donors unrestricted | 14,606 | 44.42% | 2,235,546 | 20,522 | 109,490 (4.898%) | 347,677 |
| Defaults | Donors Metazoa minus Bilateria | 164 | 0.50% | 8,155 | 1,062 | 0 (0%) | 1,990 |
| Defaults | Donors Cnidaria, all evidence | 156 | 0.47% | 7,705 | 1,008 | 0 (0%) | 1,866 |
| Defaults | Donors Cnidaria, non-electronic | 112 | 0.34% | 3,633 | 764 | 0 (0%) | 926 |
| Stringent | emapper default annotation | 9,595 | 29.18% | 1,432,157 | 19,344 | 66,570 (4.648%) | 226,354 |
| Stringent | Donors Metazoa minus Bilateria | 137 | 0.42% | 6,852 | 1,029 | 0 (0%) | 1,807 |

Seed-ortholog counts: defaults 28,670, stringent 15,848 (−44.7%). For
reference, the earlier `--score 40 --query_cover 20 --subject_cover 20`
search returned 28,252, within 1.5% of no filtering at all — that filter was
doing almost nothing.

Neither `--tax_scope Metazoa` nor stringent filtering changed the violation
rate, which stayed between 4.6% and 5.1% in every configuration that did not
restrict donors, despite stringent filtering discarding nearly half the seed
orthologs and a third of the annotated proteins. Only
`--target_taxa`/`--excluded_taxa` removed violations, reducing annotated
proteins from 14,571 to 164.

## Information contributed beyond InterProScan

`scripts/compare_eggnog_interproscan.py` compares usable associations
(GOaudit status `valid` or `alternate_id`) from an eggNOG-mapper run against
InterProScan on the same proteins. Because eggNOG-mapper propagates GO
ancestors and InterProScan reports signature-level mappings, exact pair
matching understates agreement, so overlap is also computed under ancestor
closure over `is_a` and `part_of`.

| Measure | Restricted donors | Defaults |
|---|---:|---:|
| Usable associations | 6,048 | 1,683,713 |
| Proteins annotated | 164 | 14,571 |
| Proteins also annotated by InterProScan | 135 (82.3%) | 12,874 (88.4%) |
| Exact pair overlap | 385 (6.4%) | 42,028 (2.5%) |
| Already implied under ancestor closure | 3,347 (55.3%) | 363,687 (21.6%) |
| eggNOG-mapper-only | 2,701 (44.7%) | 1,320,026 (78.4%) |
| eggNOG-mapper-only and specific (depth ≥5) | 583 (9.6%) | 455,913 (27.1%) |

The donor-restricted configuration is formally clean but adds little: most of
its proteins and associations are already covered by InterProScan, and the
remainder is dominated by near-root terms. The default configuration adds
substantial specific coverage, including 1,697 proteins InterProScan does not
annotate, but carries the 5.134% taxon-incompatible fraction.

## Results (original runs, score 40 / coverage 20 search)

| Workflow | Proteins with GO terms | Protein–GO associations | Unique GO terms | Taxon violations | Obsolete associations |
|---|---:|---:|---:|---:|---:|
| eggNOG-mapper 2.1.12, non-bilaterian donors | 162 | 8,074 | 1,062 | 0 (0%) | 1,974 |
| eggNOG-mapper 2.1.12, Cnidaria donors and all evidence | 154 | 7,624 | 1,008 | 0 (0%) | 1,850 |
| eggNOG-mapper 2.1.12, non-electronic sensitivity run | 112 | 3,633 | 764 | 0 (0%) | 926 |
| InterProScan 5.72-103.0 | 23,338 | 95,381 | 5,375 | 248 (0.260%) | 2,414 |

The main eggNOG-mapper policy eliminated formal violations but annotated only
162 proteins, showing the coverage cost of a deliberately close donor pool.
InterProScan covered 23,338 proteins and produced 248 formal review flags
across 212 proteins and 72 GO terms. Source tracing against the native TSV
showed that 212 flagged protein–GO pairs carried only a PANTHER-labelled
mapping, 35 only an InterPro-labelled mapping and one both labels. The
constraint groups included Vertebrata (118 associations), Bilateria (48) and
Bacteria (37).

These counts are review flags, not measured annotation errors. In particular,
16 `syntaxin binding` associations and two descendant `syntaxin-1 binding`
associations inherited an `in_taxon Bacteria` constraint in the frozen GO
release, despite the use of these terms in eukaryotic annotations; the parent
term contains an active GO ontology tracker link. This systematic case should
be reviewed with the GO Consortium rather than removed automatically. It
illustrates why GOaudit defaults to a complete report and why reference-data
edge cases must not be counted as successes for either GOaudit or the
upstream annotator.

## Resource use

| Step | Allocated CPUs | Wall time | Peak resident memory |
|---|---:|---:|---:|
| eggNOG-mapper search plus non-electronic sensitivity annotation | 16 | 8 min 44.51 s | 8,323,136 kB |
| eggNOG-mapper non-bilaterian annotation pass | 16 | 12 min 2.86 s | 158,576 kB |
| GOaudit on eggNOG-mapper output | 1 | 6.45 s | 86,104 kB |
| InterProScan | 24 | 4 h 22 min 11 s | 8,347,448 kB |
| GOaudit on InterProScan output | 1 | 6.57 s | 113,600 kB |
| GOaudit on 1,095,349-row DeepGOPlus output | 1 | 19.46 s | 479,812 kB |

The eggNOG figures above are from `/usr/bin/time` around the annotation
commands. The scheduler recorded a higher job-level peak of 58,244,448 kB
while the compressed shared database archive was staged into node-local
memory; database staging is therefore reported separately from annotation
memory. For InterProScan, `/usr/bin/time` recorded 8,347,448 kB for the parent
command, while the scheduler recorded 60,858,160 kB for the complete batch
step including concurrent signature-library worker processes.

## Output checksums

| File | SHA-256 |
|---|---|
| Native InterProScan TSV | `9838f477d6c33a6a6594784cd5b3cfad5c1623cf55e2836db50a6acc8c6ffb37` |
| Converted InterProScan GOaudit input | `84355230b85994e0a46efdd72014fc4bd17185012f3a7da52654a8a91f6db8a9` |
| InterProScan association audit | `0a7c836855742125d152f4eabd666000d0797943e021d8f0fd1beb42a662c709` |
| InterProScan GOaudit summary | `6fcf4436c0707d1614d836d6326d6a6bd8ad718e33466c1c1e25f63603189150` |

## Archived provenance in this repository

`results/` holds the compact, publishable record for every run: GOaudit
summaries, input and seed-ortholog checksums, tool version strings, resource
use and reference manifests. `results/eggnog_matrix/` additionally holds the
collated `option_matrix_summary.tsv` and the eggNOG-versus-InterProScan
overlap tables. Native annotation outputs are deliberately excluded; they live
in the scratch paths below and should be deposited in a data archive if
required.

## Important files

The full working outputs are under:

```text
/scratch3/bac050/2026_bioinfo_tool/results/comparator_benchmark/
```

Each workflow directory contains:

- the native annotation output;
- the strict two-column GOaudit input;
- the complete association-level audit and summary;
- exact software and input checksums; and
- separate resource-use records for annotation and GOaudit.

Only compact commands, summaries, manifests and derived tables should be
archived with the manuscript. Large native outputs should be deposited in the
project data archive if required for submission.

## Primary documentation

- [eggNOG-mapper usage and taxonomic controls](https://github.com/eggnogdb/eggnog-mapper/blob/main/USAGE.md)
- [GO Consortium: obtaining GO annotations](https://geneontology.org/docs/download-go-annotations/)
- [InterProScan command-line documentation](https://github.com/ebi-pf-team/interproscan-docs/blob/v5/docs/HowToRun.rst)
- [Archived InterProScan releases](https://github.com/ebi-pf-team/interproscan/releases)
