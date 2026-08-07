#!/usr/bin/env bash
#SBATCH --time=01:00:00
#SBATCH --mem=64GB
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --job-name=goaudit_eggall
#SBATCH --account=OD-234804
#SBATCH --output=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/eggnog_cnidaria_all-%j.out
#SBATCH --error=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/eggnog_cnidaria_all-%j.err

set -euo pipefail

seed_table="/scratch3/bac050/2026_bioinfo_tool/results/comparator_benchmark/eggnog_cnidaria/stylophora.eggnog_cnidaria.emapper.seed_orthologs"
input="/scratch3/bac050/2026_bioinfo_tool/results/ml_benchmark/deepgoplus/stylophora_refseq.protein.faa"
result_dir="/scratch3/bac050/2026_bioinfo_tool/results/comparator_benchmark/eggnog_cnidaria_all"
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
sha256sum "$seed_table" > "$result_dir/seed_orthologs.sha256"

/usr/bin/time -v -o "$result_dir/resource_use.annotation.txt" \
  emapper.py \
    -m no_search \
    --annotate_hits_table "$seed_table" \
    -o stylophora.eggnog_cnidaria_all \
    --output_dir "$result_dir" \
    --data_dir "$database_dir" \
    --scratch_dir "$MEMDIR" \
    --tax_scope Metazoa \
    --tax_scope_mode inner_narrowest \
    --target_taxa 6073 \
    --go_evidence all \
    --cpu "${SLURM_CPUS_PER_TASK:-16}"

PYTHONPATH="$project_dir/src" python -m goaudit.cli convert-eggnog \
  "$result_dir/stylophora.eggnog_cnidaria_all.emapper.annotations" \
  "$result_dir/stylophora.eggnog_cnidaria_all.goaudit.tsv" \
  --id-mode full

/usr/bin/time -v -o "$result_dir/resource_use.goaudit.txt" \
  env PYTHONPATH="$project_dir/src" python -m goaudit.cli validate \
    "$result_dir/stylophora.eggnog_cnidaria_all.goaudit.tsv" \
    --taxid 50429 \
    --data-dir "$reference_dir" \
    --output-dir "$result_dir/goaudit" \
    --mode report \
    --force
