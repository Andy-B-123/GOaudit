#!/usr/bin/env bash
#SBATCH --time=08:00:00
#SBATCH --mem=64GB
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --job-name=goaudit_eggmatrix
#SBATCH --account=OD-234804
#SBATCH --output=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/eggnog_matrix-%j.out
#SBATCH --error=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/eggnog_matrix-%j.err

# Matched eggNOG-mapper option matrix on the RefSeq Stylophora pistillata
# proteome (GCF_002571385.2, 32,879 proteins) - the identical FASTA used for
# the DeepGOPlus and InterProScan benchmarks.
#
# Every cell below differs ONLY in eggNOG-mapper options. Two DIAMOND searches
# are performed (permissive defaults and a stringent filter); all annotation
# passes reuse those seed-ortholog tables through -m no_search, so search
# stringency and annotation-donor policy are separated cleanly.
#
# emapper 2.1.12 defaults, for reference:
#   --tax_scope auto  --tax_scope_mode inner_narrowest
#   --go_evidence non-electronic  --sensmode sensitive
#   no --target_taxa, no --excluded_taxa, no --score/--query_cover/--subject_cover

set -euo pipefail

input="/scratch3/bac050/2026_bioinfo_tool/results/ml_benchmark/deepgoplus/stylophora_refseq.protein.faa"
base="/scratch3/bac050/2026_bioinfo_tool/results/comparator_benchmark/eggnog_matrix"
reference_dir="/scratch3/bac050/2026_bioinfo_tool/goaudit_cache"
project_dir="/home/bac050/bioinfo-tool"
cpus="${SLURM_CPUS_PER_TASK:-16}"

module load eggnogmapper/2.1.12 bioref
mkdir -p "$base"

archive="$BIOREF/eggnog/data_2025-03-31.tar.zst"
tar -xf "$archive" -C "$MEMDIR"
database_file="$(find "$MEMDIR" -type f -name eggnog_proteins.dmnd -print -quit)"
database_dir="$(dirname "$database_file")"

emapper.py --version > "$base/version.txt"
sha256sum "$input" > "$base/input.sha256"

# ---------------------------------------------------------------------------
# Search stage
# ---------------------------------------------------------------------------

run_search() {
  local tag="$1"; shift
  local dir="$base/search_${tag}"
  mkdir -p "$dir"
  echo "[search] $tag"
  /usr/bin/time -v -o "$dir/resource_use.search.txt" \
    emapper.py \
      -i "$input" \
      --itype proteins \
      -m diamond \
      --dmnd_ignore_warnings \
      -o "search_${tag}" \
      --output_dir "$dir" \
      --data_dir "$database_dir" \
      --scratch_dir "$MEMDIR" \
      --no_annot \
      --cpu "$cpus" \
      "$@"
  sha256sum "$dir/search_${tag}.emapper.seed_orthologs" \
    > "$dir/seed_orthologs.sha256"
}

# A: true eggNOG-mapper defaults - no score or coverage filtering at all.
run_search defaults

# B: stringent hit filtering.
run_search stringent \
  --evalue 1e-10 \
  --score 60 \
  --pident 40 \
  --query_cover 50 \
  --subject_cover 50

# ---------------------------------------------------------------------------
# Annotation stage - every cell reuses a seed table, so only options vary
# ---------------------------------------------------------------------------

run_annotation() {
  local tag="$1"; local search="$2"; shift 2
  local dir="$base/$tag"
  local seeds="$base/search_${search}/search_${search}.emapper.seed_orthologs"
  mkdir -p "$dir"
  echo "[annotate] $tag (seeds: $search)"

  /usr/bin/time -v -o "$dir/resource_use.annotation.txt" \
    emapper.py \
      -m no_search \
      --annotate_hits_table "$seeds" \
      -o "$tag" \
      --output_dir "$dir" \
      --data_dir "$database_dir" \
      --scratch_dir "$MEMDIR" \
      --cpu "$cpus" \
      "$@"

  PYTHONPATH="$project_dir/src" python -m goaudit.cli convert-eggnog \
    "$dir/$tag.emapper.annotations" \
    "$dir/$tag.goaudit.tsv" \
    --id-mode full

  /usr/bin/time -v -o "$dir/resource_use.goaudit.txt" \
    env PYTHONPATH="$project_dir/src" python -m goaudit.cli validate \
      "$dir/$tag.goaudit.tsv" \
      --taxid 50429 \
      --data-dir "$reference_dir" \
      --output-dir "$dir/goaudit" \
      --mode report \
      --force
}

# --- permissive default search -------------------------------------------

# 1. Absolute defaults: point emapper at the proteins and nothing else.
run_annotation default_search_default_annot defaults

# 2. Defaults but admitting electronically inferred GO terms.
run_annotation default_search_all_evidence defaults \
  --go_evidence all

# 3. Correct clade scope, but donors still unrestricted.
run_annotation metazoa_scope defaults \
  --tax_scope Metazoa --tax_scope_mode inner_narrowest \
  --go_evidence all

# 4. Donors restricted to non-bilaterian Metazoa (the "run it properly" cell,
#    matched to the existing main manuscript run).
run_annotation nonbilaterian_donors defaults \
  --tax_scope Metazoa --tax_scope_mode inner_narrowest \
  --target_taxa 33208 --excluded_taxa 33213 \
  --go_evidence all

# 5/6. Cnidaria-only donors, all versus non-electronic evidence.
run_annotation cnidaria_donors_all defaults \
  --tax_scope Metazoa --tax_scope_mode inner_narrowest \
  --target_taxa 6073 \
  --go_evidence all

run_annotation cnidaria_donors_nonelectronic defaults \
  --tax_scope Metazoa --tax_scope_mode inner_narrowest \
  --target_taxa 6073 \
  --go_evidence non-electronic

# --- stringent search -----------------------------------------------------

# 7. Stringent hits, default annotation policy.
run_annotation stringent_search_default_annot stringent

# 8. Stringent hits plus non-bilaterian donors: both controls at once.
run_annotation stringent_search_nonbilaterian stringent \
  --tax_scope Metazoa --tax_scope_mode inner_narrowest \
  --target_taxa 33208 --excluded_taxa 33213 \
  --go_evidence all

echo "matrix complete"
