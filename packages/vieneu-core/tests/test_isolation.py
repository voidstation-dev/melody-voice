import ast
import os
from pathlib import Path

import pytest

FORBIDDEN_IMPORTS = {
    "fastapi",
    "starlette",
    "sqlalchemy",
    "alembic",
    "app",
    "src",
    "voidmelody",
}


def get_python_files(directory: Path) -> list[Path]:
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".py"):
                files.append(Path(root) / filename)
    return files


def test_no_forbidden_imports():
    """
    Ensure the vieneu_core package is strictly decoupled from the main VoidMelody application.
    It should not import FastAPI, SQLAlchemy, or internal app modules.
    """
    src_dir = Path(__file__).parent.parent / "src" / "vieneu_core"
    python_files = get_python_files(src_dir)

    violations = []

    for filepath in python_files:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_module = alias.name.split(".")[0]
                    if base_module in FORBIDDEN_IMPORTS:
                        violations.append(f"{filepath.name}: import {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base_module = node.module.split(".")[0]
                    if base_module in FORBIDDEN_IMPORTS:
                        violations.append(f"{filepath.name}: from {node.module} import ...")

    if violations:
        pytest.fail(
            "Found forbidden imports that violate the portable core isolation contract:\\n"
            + "\\n".join(violations)
        )
