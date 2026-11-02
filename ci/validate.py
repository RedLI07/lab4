"""Компиляция Python-файлов проекта и проверка main через AST."""

import ast
import py_compile
from pathlib import Path


def main():
    excluded = {".git", ".venv", "venv", "__pycache__", "dist", "deploy"}
    paths = [path for path in Path(".").rglob("*.py") if not excluded.intersection(path.parts)]
    if not paths:
        raise SystemExit("ERROR: Python-файлы отсутствуют")
    for path in sorted(paths):
        py_compile.compile(str(path), doraise=True)
        print(f"Compiled: {path}")
    tree = ast.parse(Path("disk_check.py").read_text(encoding="utf-8"))
    if not any(isinstance(node, ast.FunctionDef) and node.name == "main" for node in tree.body):
        raise SystemExit("ERROR: disk_check.py не содержит функцию main")
    print("PASS: disk_check.py содержит функцию main")


if __name__ == "__main__":
    main()
