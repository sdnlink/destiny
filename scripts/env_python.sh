#!/usr/bin/env bash
# Common Python environment resolver prioritizing Conda base environment

resolve_project_python() {
  if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN:-}" ]]; then
    echo "$PYTHON_BIN"
    return 0
  fi

  if [[ -n "${CONDA_PREFIX:-}" && -x "${CONDA_PREFIX}/bin/python" ]]; then
    echo "${CONDA_PREFIX}/bin/python"
    return 0
  fi

  local conda_base=""
  if command -v conda >/dev/null 2>&1; then
    conda_base="$(conda info --base 2>/dev/null || true)"
    if [[ -n "$conda_base" && -x "$conda_base/bin/python" ]]; then
      echo "$conda_base/bin/python"
      return 0
    fi
  fi

  if [[ -x "/home/skn/anaconda3/bin/python" ]]; then
    echo "/home/skn/anaconda3/bin/python"
    return 0
  fi

  if [[ -x "${project_dir:-.}/.venv/bin/python" ]]; then
    echo "${project_dir:-.}/.venv/bin/python"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    echo "$(command -v python3)"
    return 0
  fi

  echo "python"
}

export PYTHON_BIN="$(resolve_project_python)"
