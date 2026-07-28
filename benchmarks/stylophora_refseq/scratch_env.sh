#!/usr/bin/env bash
# Source this file before installing or running benchmark dependencies.

export GOAUDIT_SCRATCH_ROOT="${GOAUDIT_SCRATCH_ROOT:-/scratch3/bac050/2026_bioinfo_tool}"
export GOAUDIT_TOOL_ROOT="${GOAUDIT_SCRATCH_ROOT}/tools"
export MAMBA_EXE="${GOAUDIT_TOOL_ROOT}/bin/micromamba"
export MAMBA_ROOT_PREFIX="${GOAUDIT_TOOL_ROOT}/mamba"
export CONDA_PKGS_DIRS="${GOAUDIT_TOOL_ROOT}/cache/conda-pkgs"
export PIP_CACHE_DIR="${GOAUDIT_TOOL_ROOT}/cache/pip"
export XDG_CACHE_HOME="${GOAUDIT_TOOL_ROOT}/cache/xdg"
export XDG_DATA_HOME="${GOAUDIT_TOOL_ROOT}/cache/xdg-data"
export PYSTOW_HOME="${GOAUDIT_TOOL_ROOT}/cache/pystow"
export MPLCONFIGDIR="${GOAUDIT_TOOL_ROOT}/cache/matplotlib"
export GROOVY_USER_HOME="${GOAUDIT_TOOL_ROOT}/cache/groovy"
export PYTHONPYCACHEPREFIX="${GOAUDIT_TOOL_ROOT}/cache/pycache"
export PYTHONUSERBASE="${GOAUDIT_TOOL_ROOT}/home/.local"
export PYTHONNOUSERSITE=1
export HOME="${GOAUDIT_TOOL_ROOT}/home"
export TMPDIR="/scratch3/bac050/tmp"
