#!/usr/bin/env bash
#SBATCH --time=04:00:00
#SBATCH --mem=64GB
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --job-name=goaudit_eggnog
#SBATCH --account=OD-234804
#SBATCH --output=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/eggnog_cnidaria-%j.out
#SBATCH --error=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/eggnog_cnidaria-%j.err

set -euo pipefail

input="/scratch3/bac050/2026_bioinfo_tool/results/ml_benchmark/deepgoplus/stylophora_refseq.protein.faa"
result_dir="/scratch3/bac050/2026_bioinfo_tool/results/comparator_benchmark/eggnog_cnidaria"
reference_dir="/scratch3/bac050/2026_bioinfo_tool/goaudit_cache"
project_dir="/home/bac050/bioinfo-tool"

module load eggnogmapper/2.1.12 bioref
mkdir -p "$result_dir"

archive="$BIOREF/eggnog/data_2025-03-31.tar.zst"
tar -xf "$archive" -C "$MEMDIR"
database_file="$(find "$MEMDIR" -type f -name eggnog_proteins.dmnd -print -quit)"
database_dir="$(dirname "$database_file")"

emapper.py --version > "$result_dir/version.txt"
sha256sum "$input" > "$result_dir/input.sha256"

/usr/bin/time -v -o "$result_dir/resource_use.emapper.txt" \
  emapper.py \
    -i "$input" \
    --itype proteins \
    -o stylophora.eggnog_cnidaria \
    --output_dir "$result_dir" \
    --data_dir "$database_dir" \
    --scratch_dir "$MEMDIR" \
    -m diamond \
    --score 40 \
    --query_cover 20 \
    --subject_cover 20 \
    --dmnd_ignore_warnings \
    --tax_scope Metazoa \
    --tax_scope_mode inner_narrowest \
    --target_taxa 6073 \
    --go_evidence non-electronic \
    --cpu "${SLURM_CPUS_PER_TASK:-16}"

PYTHONPATH="$project_dir/src" python -m goaudit.cli convert-eggnog \
  "$result_dir/stylophora.eggnog_cnidaria.emapper.annotations" \
  "$result_dir/stylophora.eggnog_cnidaria.goaudit.tsv" \
  --id-mode full

/usr/bin/time -v -o "$result_dir/resource_use.goaudit.txt" \
  env PYTHONPATH="$project_dir/src" python -m goaudit.cli validate \
    "$result_dir/stylophora.eggnog_cnidaria.goaudit.tsv" \
    --taxid 50429 \
    --data-dir "$reference_dir" \
    --output-dir "$result_dir/goaudit" \
    --mode report \
    --force
