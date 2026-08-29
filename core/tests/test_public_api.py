"""Compare exports imported by Python package initializers with Rust."""

from __future__ import annotations

import ast
import importlib
import importlib.machinery
import inspect
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

CORE_DIRECTORY = Path(__file__).resolve().parent.parent
PYTHON_PACKAGE_DIRECTORY = CORE_DIRECTORY / "compone"
RUST_IMPLEMENTATION_NAME = "compone"
WORKER_IMPLEMENTATION_VARIABLE = "COMPONE_PUBLIC_API_IMPLEMENTATION"

ApiManifest = dict[str, list[str]]


def package_initializers() -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for initializer in PYTHON_PACKAGE_DIRECTORY.rglob("__init__.py"):
        relative_package = initializer.parent.relative_to(PYTHON_PACKAGE_DIRECTORY)
        module_parts = (RUST_IMPLEMENTATION_NAME, *relative_package.parts)
        modules[".".join(module_parts)] = initializer
    return dict(sorted(modules.items()))


def bound_import_names(
    statement: ast.stmt,
    initializer: Path,
) -> tuple[str, ...]:
    if isinstance(statement, ast.ImportFrom):
        if any(alias.name == "*" for alias in statement.names):
            raise ValueError(f"star import is not supported in {initializer}")
        return tuple(alias.asname or alias.name for alias in statement.names)
    if isinstance(statement, ast.Import):
        return tuple(
            alias.asname or alias.name.partition(".")[0] for alias in statement.names
        )
    return ()


def imported_names(initializer: Path) -> tuple[str, ...]:
    syntax_tree = ast.parse(initializer.read_text(), filename=str(initializer))
    names = {
        name
        for statement in syntax_tree.body
        for name in bound_import_names(statement, initializer)
        if not name.startswith("_")
    }
    return tuple(sorted(names))


def is_extension_module(module: ModuleType) -> bool:
    module_file = module.__file__
    return module_file is not None and any(
        module_file.endswith(suffix)
        for suffix in importlib.machinery.EXTENSION_SUFFIXES
    )


def export_kind(value: object) -> str:
    if inspect.isclass(value):
        return "class"
    if isinstance(value, ModuleType):
        return "module"
    if callable(value):
        return "callable"
    return type(value).__name__


def export_name(value: object, fallback: str) -> str:
    name = getattr(value, "__name__", fallback)
    return name if isinstance(name, str) else fallback


def export_descriptor(module: ModuleType, name: str) -> list[str]:
    if name not in vars(module):
        return ["missing", name]
    value = cast(object, vars(module)[name])
    return [export_kind(value), export_name(value, name)]


def public_api_manifest() -> ApiManifest:
    manifest: ApiManifest = {}
    for module_name, initializer in package_initializers().items():
        module = importlib.import_module(module_name)
        for name in imported_names(initializer):
            manifest[f"{module_name}.{name}"] = export_descriptor(module, name)
    return manifest


def worker_main():
    expected_implementation = os.environ.get(WORKER_IMPLEMENTATION_VARIABLE)
    if expected_implementation not in {"python", "rust"}:
        raise RuntimeError(f"invalid implementation: {expected_implementation!r}")

    root = importlib.import_module(RUST_IMPLEMENTATION_NAME)
    actual_implementation = "rust" if is_extension_module(root) else "python"
    if actual_implementation != expected_implementation:
        raise RuntimeError(
            f"expected {expected_implementation}, imported {actual_implementation}"
        )

    print(json.dumps(public_api_manifest(), sort_keys=True))


def run_manifest(
    implementation: str,
    python_path: Path | None,
) -> ApiManifest:
    environment = os.environ.copy()
    environment[WORKER_IMPLEMENTATION_VARIABLE] = implementation
    if python_path is None:
        _ = environment.pop("PYTHONPATH", None)
    else:
        environment["PYTHONPATH"] = str(python_path)

    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        cwd=CORE_DIRECTORY,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = (
            f"{implementation} API worker failed with exit code "
            + f"{completed.returncode}:\n{completed.stderr}"
        )
        raise RuntimeError(message)

    return cast(ApiManifest, json.loads(completed.stdout))


def test_python_and_rust_package_initializer_exports_match(tmp_path: Path):
    current_implementation = importlib.import_module(RUST_IMPLEMENTATION_NAME)
    if not is_extension_module(current_implementation):
        pytest.skip("requires the released Rust package")

    python_import_root = tmp_path / "python-implementation"
    _ = shutil.copytree(
        PYTHON_PACKAGE_DIRECTORY,
        python_import_root / RUST_IMPLEMENTATION_NAME,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.so", "*.pyd"),
    )

    python_manifest = run_manifest("python", python_import_root)
    rust_manifest = run_manifest("rust", None)

    assert rust_manifest == python_manifest


if __name__ == "__main__":
    worker_main()
