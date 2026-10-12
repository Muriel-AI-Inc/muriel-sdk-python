"""Every name the package uses is defined or imported.

A missing import inside a function body only fails when that line runs -- an
error path such as "out of credits" can ship broken and pass every test that
never reaches it. This reads the source instead of running it.

    python -m pytest tests/test_static.py
"""
import ast
import builtins
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "muriel"


def _undefined(path: Path):
    tree = ast.parse(path.read_text())
    defined = set(dir(builtins))
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            defined.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            defined.add(n.id)
        elif isinstance(n, ast.arg):
            defined.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            defined.add(n.name)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return sorted(used - defined)


def test_no_undefined_names():
    bad = {str(p.relative_to(PKG.parent)): _undefined(p) for p in PKG.rglob("*.py")}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, f"undefined names: {bad}"


if __name__ == "__main__":
    test_no_undefined_names()
    print("ok  test_no_undefined_names")
