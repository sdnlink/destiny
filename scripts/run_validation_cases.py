#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def resolve_target_python():
    if os.environ.get("PYTHON_BIN"):
        custom = Path(os.environ["PYTHON_BIN"])
        if custom.is_file() and os.access(custom, os.X_OK):
            return custom.resolve()

    if os.environ.get("CONDA_PREFIX"):
        conda_py = Path(os.environ["CONDA_PREFIX"]) / "bin" / "python"
        if conda_py.is_file() and os.access(conda_py, os.X_OK):
            return conda_py.resolve()

    anaconda_py = Path("/home/skn/anaconda3/bin/python")
    if anaconda_py.is_file() and os.access(anaconda_py, os.X_OK):
        return anaconda_py.resolve()

    venv_py = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_py.is_file() and os.access(venv_py, os.X_OK):
        return venv_py.resolve()

    return Path(sys.executable).resolve()


target_python = resolve_target_python()
if target_python.exists() and Path(sys.executable).resolve() != target_python:
    os.execv(str(target_python), [str(target_python)] + sys.argv)

sys.path.insert(0, str(BACKEND_ROOT))

from app.core.validation import run_validation_cases


def main():
    report = run_validation_cases()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
