# BMC Bioinformatics Software article launch pack

This directory is a self-contained starting point for the GOaudit paper. It
does not replace the older exploratory manuscript; it narrows that material to
the intended BMC Bioinformatics story and the completed DeepGOPlus benchmark.

## Start here

1. Read `NEXT_SESSION_BRIEF.md` for the agreed argument, author material to
   collect and analyses still needed.
2. Edit `GOaudit_BMC_software_article_launch_draft.md` as the working
   manuscript.
3. Treat the TSV files under `tables/` as the numerical source of truth for
   the manuscript tables and figures.
4. Regenerate the vector figures after changing a table:

   ```bash
   python manuscript/bmc/figures/generate_figures.py
   ```

The generator uses only the Python standard library and writes SVG. The
`.preview.png` files are convenient rendered copies for review. Publication
exports should be produced from the SVG masters at the journal's requested
dimensions and resolution.

## Current journal-requirement mapping

Checked against the BMC Bioinformatics Software article instructions on
28 July 2026:

| Requirement | Where it is handled |
|---|---|
| Broad utility and significant advance, usually demonstrated by direct comparison | Background, Table 1, Discussion and the outstanding same-release comparison |
| Software accessible to anonymous reviewers | Public repository; immutable release and supplementary source archive still required |
| Structured abstract, no citations, no more than 350 words | Background, Results and Conclusions abstract subsections |
| Background | Present |
| Implementation, including architecture and critical issues | Present |
| Results, with statistics in text/tables/figures | Present |
| Discussion of interface, uses, benefits and comparison | Present |
| Conclusions | Present |
| Availability and requirements block | All six requested fields present |
| List of abbreviations | Present |
| Declarations with every required subheading | Present; author-specific entries remain bracketed |
| Web resources represented as numbered references | Partly complete; raw project/data URLs must be converted during final reference editing |
| Software archive attached as an additional file | Planned for the tagged submission release |
| LLM assistance documented, not credited as authorship | Flagged for an author-approved Implementation/Methods statement before submission |

Official instructions:
https://link.springer.com/journal/12859/submission-guidelines/software-article

## Figure set

- Figure 1: source-independent GOaudit workflow.
- Figure 2: frequent incompatible DeepGOPlus terms and constraint taxa.
- Figure 3: score-threshold sensitivity and the 2,306 associations remaining
  at score ≥0.65.

The existing GOaudit-generated status/namespace plots can be supplied as
supplementary diagnostic outputs. A before/after enrichment figure should be
added only if a frozen analysis with an identical gene universe produces a
clear result that improves the paper.

## Editorial guardrails

- Say that GOaudit applies official constraints; it does not invent them.
- Describe DeepGOPlus as a hybrid CNN and DIAMOND similarity predictor.
- Describe score ≥0.65 associations as high-scoring, not as independently
  validated or calibrated probabilities.
- Report associations, unique GO terms and affected proteins together because
  DeepGOPlus propagates scores to GO ancestors.
- Present eggNOG-mapper as a strong method with taxonomic controls. Use the
  matched Metazoa-donor run excluding Bilateria in the main comparison and
  retain the Cnidaria-only runs as sensitivity analyses.
- Motivate the paper with the frozen full-proteome DeepGOPlus benchmark rather
  than an individual term from an earlier exploratory annotation.
- Compare different constraint policies by agreement and provenance, not by
  assuming that the largest number of exclusions is best.
- State plainly that OAK can compute the inherited constraints needed for this
  analysis. GOaudit's distinction is the packaged protein–GO-table-to-report
  workflow, not a novel taxon-constraint algorithm.
