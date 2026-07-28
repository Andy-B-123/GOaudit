#!/usr/bin/env bash
#SBATCH --partition=h2
#SBATCH --time=02:00:00
#SBATCH --mem=32GB
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --job-name=deepgoplus_stylophora
#SBATCH --account=OD-234804
#SBATCH --output=/scratch3/bac050/2026_bioinfo_tool/logs/ml_benchmark/%x-%j.out
#SBATCH --error=/scratch3/bac050/2026_bioinfo_tool/logs/ml_benchmark/%x-%j.err

set -euo pipefail

ROOT=/scratch3/bac050/2026_bioinfo_tool
ENV="${ROOT}/tools/envs/deepgoplus"
DATA="${ROOT}/data/deepgoplus/1.0.28/data"
RESULTS="${ROOT}/results/ml_benchmark/deepgoplus"
INPUT="${RESULTS}/stylophora_refseq.protein.faa"
CPUS="${SLURM_CPUS_PER_TASK:-1}"

export HOME="${ROOT}/tools/home"
export TMPDIR=/scratch3/bac050/tmp
export PATH="${ENV}/bin:${PATH}"
export CUDA_VISIBLE_DEVICES=""
export TF_CPP_MIN_LOG_LEVEL=2
export OMP_NUM_THREADS="${CPUS}"
export TF_NUM_INTRAOP_THREADS="${CPUS}"
export TF_NUM_INTEROP_THREADS=2
export DEEPGOPLUS_DIAMOND_THREADS="${CPUS}"

echo "started_at=$(date --iso-8601=seconds)"
echo "host=$(hostname)"
echo "slurm_job_id=${SLURM_JOB_ID:-none}"
echo "cpus=${CPUS}"
echo "input=${INPUT}"
echo "deepgoplus_version=$("${ENV}/bin/python" -m pip show deepgoplus | awk '/^Version:/{print $2}')"
echo "diamond_version=$("${ENV}/bin/diamond" version)"

/usr/bin/time -v "${ENV}/bin/deepgoplus" \
  --data-root "${DATA}" \
  --in-file "${INPUT}" \
  --out-file "${RESULTS}/stylophora.deepgoplus.raw.tsv" \
  --diamond-file "${RESULTS}/stylophora.deepgoplus.diamond.tsv" \
  --threshold 0.3 \
  --chunk-size 512 \
  --batch-size 64

echo "finished_at=$(date --iso-8601=seconds)"
