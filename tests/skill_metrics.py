#!/usr/bin/env python3
"""Print deterministic context, discovery-budget, and test-suite metrics."""

from __future__ import annotations

import ast
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "capelry" / "SKILL.md"
BOOTSTRAP = ROOT / "skills" / "capelry" / "BOOTSTRAP.md"
CLI = ROOT / "skills" / "capelry" / "scripts" / "capelry.py"


def load_cli():
    spec = importlib.util.spec_from_file_location("capelry_metrics_cli", CLI)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {CLI}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text_metrics(path: Path) -> dict[str, int | str]:
    text = path.read_text(encoding="utf-8")
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": len(text.encode("utf-8")),
        "lines": len(text.splitlines()),
        "words": len(text.split()),
        "estimatedTokens": math.ceil(len(text) / 4),
    }


def python_metrics(path: Path) -> dict[str, int | str]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
    branch_types = (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp, ast.IfExp, ast.comprehension)
    if hasattr(ast, "Match"):
        branch_types += (ast.Match,)
    branches = sum(isinstance(node, branch_types) for node in ast.walk(tree))
    return {**text_metrics(path), "functions": functions, "branchNodes": branches}


def test_count() -> int:
    count = 0
    for path in (ROOT / "tests").glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        count += sum(isinstance(node, ast.FunctionDef) and node.name.startswith("test_") for node in ast.walk(tree))
    return count


def collect_metrics() -> dict[str, object]:
    cli = load_cli()
    examples = {}
    for query in ("feature planning skills", "production readiness skills", "pdf skill"):
        queries = cli.discover_queries(query, None, True, cli.DEFAULT_QUERY_BUDGET)
        examples[query] = {
            "queries": queries,
            "requestCount": len(queries),
            "candidateEnvelope": len(queries) * cli.DEFAULT_DISCOVERY_SEARCH_LIMIT,
        }
    return {
        "promptContext": text_metrics(SKILL),
        "bootstrapContext": text_metrics(BOOTSTRAP),
        "discoveryDefaults": {
            "top": cli.DEFAULT_DISCOVERY_TOP,
            "maxQueries": cli.DEFAULT_QUERY_BUDGET,
            "perRequestLimit": cli.DEFAULT_DISCOVERY_SEARCH_LIMIT,
            "candidateEnvelope": cli.DEFAULT_QUERY_BUDGET * cli.DEFAULT_DISCOVERY_SEARCH_LIMIT,
            "hardMaxQueries": cli.MAX_QUERY_BUDGET,
        },
        "discoveryExamples": examples,
        "cli": python_metrics(CLI),
        "testMethods": test_count(),
    }


def main() -> int:
    print(json.dumps(collect_metrics(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
