#!/usr/bin/env bash
#SBATCH --time=24:00:00
#SBATCH --mem=128GB
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=24
#SBATCH --job-name=goaudit_interpro
#SBATCH --account=OD-234804
#SBATCH --output=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/interproscan-%j.out
#SBATCH --error=/scratch3/bac050/2026_bioinfo_tool/logs/comparator_benchmark/interproscan-%j.err

set -euo pipefail

input="/scratch3/bac050/2026_bioinfo_tool/results/ml_benchmark/deepgoplus/stylophora_refseq.protein.faa"
result_dir="/scratch3/bac050/2026_bioinfo_tool/results/comparator_benchmark/interproscan"
reference_dir="/scratch3/bac050/2026_bioinfo_tool/goaudit_cache"
project_dir="/home/bac050/bioinfo-tool"
temp_dir="$MEMDIR/interproscan"

module load interproscan/5.72-103.0
mkdir -p "$result_dir" "$temp_dir"

interproscan.sh --version > "$result_dir/version.txt" 2>&1
sha256sum "$input" > "$result_dir/input.sha256"

/usr/bin/time -v -o "$result_dir/resource_use.interproscan.txt" \
  interproscan.sh \
    --input "$input" \
    --seqtype p \
    --formats TSV \
    --output-file-base "$result_dir/stylophora.interproscan" \
    --tempdir "$temp_dir" \
    --cpu "${SLURM_CPUS_PER_TASK:-24}" \
    --iprlookup \
    --goterms \
    --disable-precalc

PYTHONPATH="$project_dir/src" python -m goaudit.cli convert-interpro \
  "$result_dir/stylophora.interproscan.tsv" \
  "$result_dir/stylophora.interproscan.goaudit.tsv" \
  --id-mode full

/usr/bin/time -v -o "$result_dir/resource_use.goaudit.txt" \
  env PYTHONPATH="$project_dir/src" python -m goaudit.cli validate \
    "$result_dir/stylophora.interproscan.goaudit.tsv" \
    --taxid 50429 \
    --data-dir "$reference_dir" \
    --output-dir "$result_dir/goaudit" \
    --mode report \
    --force
