import ast
from pathlib import Path
import subprocess
import sys

import pytest


APP_ROOT = Path(__file__).resolve().parents[1] / "app"
SYSTEM_FILES = {
    "zhouyi": APP_ROOT / "core" / "iching.py",
    "liuyao": APP_ROOT / "core" / "liuyao.py",
    "meihua": APP_ROOT / "core" / "meihua.py",
    "daliuren": APP_ROOT / "daliuren" / "engine.py",
    "fengshui": APP_ROOT / "fengshui" / "engine.py",
}


@pytest.mark.parametrize("package", ("calendar", "common", "zhouyi", "liuyao", "meihua", "daliuren", "fengshui"))
def test_required_domain_package_exists(package):
    assert (APP_ROOT / package / "__init__.py").is_file()


def test_system_engines_do_not_import_other_system_engines():
    forbidden = {"iching", "liuyao", "meihua", "liuren"}
    for system, path in SYSTEM_FILES.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_core_modules = {
            alias.name.split(".")[-1]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
            for alias in node.names
            if node.module in ("app.core", "core")
        }
        relative_modules = {
            node.module.split(".")[-1]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level and node.module
        }
        assert not ((imported_core_modules | relative_modules) & (forbidden - {path.stem})), system


def test_corpus_api_module_does_not_shadow_standard_library_calendar():
    completed = subprocess.run(
        [sys.executable, "-c", "import app.corpus_api, calendar; assert hasattr(calendar, 'monthrange')"],
        cwd=str(APP_ROOT.parent),
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0


def test_calendar_domain_does_not_import_legacy_core_modules():
    for path in (APP_ROOT / "calendar").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(module == "app.core" or module.startswith("app.core.") for module in modules), path.name


def test_zhouyi_domain_does_not_import_other_divination_systems():
    forbidden = ("app.meihua", "app.liuyao", "app.daliuren")
    for path in (APP_ROOT / "zhouyi").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(module == prefix or module.startswith(prefix + ".") for module in modules for prefix in forbidden), path.name


def test_meihua_domain_only_depends_on_calendar_and_common_domains():
    forbidden = ("app.zhouyi", "app.liuyao", "app.daliuren", "app.core")
    for path in (APP_ROOT / "meihua").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not any(module == prefix or module.startswith(prefix + ".") for module in modules for prefix in forbidden), path.name


def test_liuyao_domain_only_depends_on_calendar_and_common_domains():
    forbidden = ("app.zhouyi", "app.meihua", "app.daliuren", "app.core")
    for path in (APP_ROOT / "liuyao").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not any(module == prefix or module.startswith(prefix + ".") for module in modules for prefix in forbidden), path.name


def test_daliuren_domain_only_depends_on_calendar_and_common_domains():
    forbidden = ("app.zhouyi", "app.meihua", "app.liuyao", "app.core")
    for path in (APP_ROOT / "daliuren").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not any(module == prefix or module.startswith(prefix + ".") for module in modules for prefix in forbidden), path.name


def test_fengshui_domain_does_not_depend_on_other_domains():
    forbidden = ("app.calendar", "app.zhouyi", "app.meihua", "app.liuyao", "app.daliuren", "app.core")
    for path in (APP_ROOT / "fengshui").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not any(module == prefix or module.startswith(prefix + ".") for module in modules for prefix in forbidden), path.name
