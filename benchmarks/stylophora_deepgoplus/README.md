# DeepGOPlus–GOaudit benchmark on Stylophora

Status: complete, 28 July 2026 (Australia/Sydney).

## Purpose

This is a deliberately simple test of the GOaudit use case:

> protein FASTA → machine-learning GO predictions → taxon-constraint audit

[DeepGOPlus](https://github.com/bio-ontology-research-group/deepgoplus) was
chosen because it accepts protein FASTA directly, provides a downloadable
pretrained model and emits confidence-scored GO identifiers for all three GO
namespaces. It is a hybrid predictor: a convolutional neural network is
combined with annotation transfer from DIAMOND sequence matches. It should not
be described as a sequence-only or homology-free model.

## Input and releases

| Item | Value |
|---|---|
| Organism | *Stylophora pistillata* |
| NCBI taxid | 50429 |
| RefSeq assembly | `GCF_002571385.2` |
| Proteins | 32,879 |
| Protein FASTA SHA-256 | `bfbb681b97609d4828705da786fd3a1e223a918f584ef0dbf0f9ca117241ac82` |
| DeepGOPlus package | 1.0.2 |
| DeepGOPlus model bundle | 1.0.28, 14 June 2026 |
| Model GO release | 19 May 2026 |
| Model Swiss-Prot release | 2026_02 |
| Modelled GO terms | 5,692 |
| GOaudit | 0.1.0 |
| GOaudit GO release | 15 June 2026 |

The model archive was downloaded from:

```text
https://deepgo.cbrc.kaust.edu.sa/data/data-1.0.28.tar.gz
```

Its verified size is 832,977,007 bytes and its SHA-256 is:

```text
949943db085b123e5c238dd9819f2184e9d0636ade506438df3c5d5da3104e93
```

## Contained installation

Everything is under `/scratch3/bac050/2026_bioinfo_tool/`:

```text
tools/envs/deepgoplus/           Python 3.7, DeepGOPlus and TensorFlow
data/deepgoplus/1.0.28/         extracted pretrained bundle
results/ml_benchmark/deepgoplus/ inputs, predictions and GOaudit reports
logs/ml_benchmark/               Slurm logs
```

The environment contains DeepGOPlus 1.0.2, TensorFlow 2.3.4, DIAMOND 2.2.4,
NumPy 1.18.5, pandas 1.3.5 and scikit-learn 1.0.2. `pip check` reports no broken
requirements.

The official package requires Python 3.7 and invokes DIAMOND with a hard-coded
`/tmp`. The small supplied patch makes DIAMOND respect `TMPDIR` and an explicit
thread count; it does not change prediction logic. See
[`deepgoplus-scratch.patch`](deepgoplus-scratch.patch).

## Prediction policy

The run uses a confidence threshold of 0.3, matching the value shown in the
DeepGOWeb API example, rather than the permissive CLI default of 0.1. Scores
from the CNN and sequence-similarity components are combined by DeepGOPlus and
propagated to GO ancestors before thresholding.

The exact batch command is in
[`run_deepgoplus.slurm`](run_deepgoplus.slurm). Conversion retains a
three-column scored table and separately creates the strict two-column GOaudit
input:

```bash
python convert_deepgoplus.py \
  stylophora.deepgoplus.raw.tsv \
  stylophora.deepgoplus.scored.tsv \
  stylophora.deepgoplus.goaudit.tsv

goaudit validate stylophora.deepgoplus.goaudit.tsv \
  --taxid 50429 \
  --data-dir /scratch3/bac050/2026_bioinfo_tool/goaudit_cache \
  --output-dir stylophora_goaudit \
  --mode report
```

## Smoke test

A 100-protein smoke test completed successfully in 77.18 seconds with 2.35 GB
peak resident memory.

| Measure | Result |
|---|---:|
| Input proteins | 100 |
| Proteins with a prediction ≥0.3 | 86 |
| Protein–GO associations | 2,221 |
| Unique GO terms | 494 |
| GOaudit taxon violations | 5 associations; 3 terms; 4 proteins |
| Obsolete or unknown GO IDs | 0 |

GOaudit flagged:

| GO term | Description | Rows | Score | Constraint |
|---|---|---:|---:|---|
| `GO:0007417` | central nervous system development | 3 | 0.326 | in Bilateria |
| `GO:0006954` | inflammatory response | 1 | 0.442 | in Vertebrata |
| `GO:0050727` | regulation of inflammatory response | 1 | 0.442 | in Vertebrata |

This is already a useful positive case: valid-looking predictions from a
current ML annotation model include taxon-incompatible terms for a coral, and
GOaudit identifies them without rejecting the underlying protein prediction.

## Full-proteome result

Slurm job `29161218` completed successfully in 28 minutes and 2 seconds using
16 allocated CPUs. `/usr/bin/time` recorded 27:59.81 wall time, 1,119% mean CPU
use and 4,021,668 kB maximum resident memory. DIAMOND took 13.36 seconds and
found matches for 23,900 proteins.

| Measure | Result |
|---|---:|
| Input proteins | 32,879 |
| Proteins with a prediction ≥0.3 | 31,035 (94.392%) |
| Proteins without a prediction ≥0.3 | 1,844 |
| Protein–GO associations | 1,095,349 |
| Unique GO terms | 10,799 |
| Valid/current associations | 1,087,006 |
| Taxon violations | 8,316 (0.759%) |
| Unique violating GO terms | 1,202 |
| Proteins with a violation | 1,285 (4.140% of annotated proteins) |
| Obsolete associations | 27 across 6 terms |
| Unknown GO identifiers | 0 |
| Associations retained by `mode=remove` | 1,087,033 |

Most violations are biological-process terms (8,121), followed by cellular
component (178) and molecular function (17).

| GO term | Description | Violating rows | Maximum score | Constraint |
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

The largest constraint categories are Vertebrata (4,554 rows), Bilateria
(1,383), Chordata (394), Gnathostomata (325), Viridiplantae (271), Craniata
(197), Arthropoda (171) and Insecta (168). A further 85 associations violate a
`never_in_taxon Metazoa` constraint.

Confidence does not remove the need for the audit:

| Minimum DeepGOPlus score | All associations | Taxon violations | Violation rate |
|---:|---:|---:|---:|
| 0.30 | 1,095,349 | 8,316 | 0.759% |
| 0.40 | 712,875 | 3,225 | 0.452% |
| 0.50 | 497,214 | 2,620 | 0.527% |
| 0.60 | 331,926 | 2,361 | 0.711% |
| 0.65 | 270,955 | 2,306 | 0.851% |
| 0.70 | 157,093 | 0 | 0% |

The motivating salivary-gland term `GO:0035070` was not predicted for this
RefSeq proteome, but the run produced many analogous transfers of
vertebrate-, bilaterian-, plant-, arthropod- and bacterial-restricted terms.

The six obsolete terms were all recognised; no prediction used a GO identifier
unknown to the GOaudit release. Obsolete associations are reported but retained
by taxon-removal mode, preserving the distinction between taxonomy filtering
and ontology-version maintenance.

## Outputs

The complete outputs are under:

```text
/scratch3/bac050/2026_bioinfo_tool/results/ml_benchmark/deepgoplus/
```

Important files are:

- `stylophora.deepgoplus.raw.tsv`: original confidence-scored output;
- `stylophora.deepgoplus.scored.tsv`: long three-column scored table;
- `stylophora.deepgoplus.goaudit.tsv`: strict two-column GOaudit input;
- `stylophora.deepgoplus.violations_scored.tsv`: violations with scores;
- `stylophora_goaudit/audit.tsv`: complete association-level audit;
- `stylophora_goaudit/annotations_filtered.tsv`: two-column taxon-filtered set;
- `stylophora_goaudit/summary.tsv`: final GOaudit statistics and reference
  provenance; and
- `python_environment.freeze.txt`: exact Python dependency versions.

## Interpretation

Counts are associations after GO ancestor propagation, not independent
experimental function calls. Threshold-dependent output should be reported
with its DeepGOPlus model release, and GOaudit findings should be interpreted
against the recorded GO constraint release. This benchmark tests workflow
compatibility and the prevalence of constraint violations; it does not estimate
biological precision or recall.
