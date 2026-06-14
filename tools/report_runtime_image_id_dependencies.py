#!/usr/bin/env python3
"""Inventory runtime uses of image-derived names and classify their impact."""
from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = ROOT / "src"
DEFAULT_OUTPUT = ROOT / "artifacts" / "evaluation" / "runtime_image_id_dependencies_v1" / "report.json"
TRACKED_NAMES = frozenset({"base_name", "variant_name", "image_name", "image_stem", "source_stem"})
SEMANTIC_KEYS = frozenset(
    {
        "arm",
        "badge",
        "circle",
        "color",
        "connector",
        "geometry",
        "label",
        "lock",
        "optimizer",
        "profile",
        "radius",
        "renderer",
        "semantic",
        "shape",
        "stem",
        "style",
        "text",
    }
)
OUTPUT_KEYS = frozenset(
    {
        "artifact",
        "audit",
        "csv",
        "debug",
        "diff",
        "filename",
        "log",
        "output",
        "path",
        "report",
        "save",
        "svg_path",
        "write",
    }
)


def _call_name(node: ast.AST | None) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _tracked_names(node: ast.AST) -> list[str]:
    return sorted({item.id for item in ast.walk(node) if isinstance(item, ast.Name) and item.id in TRACKED_NAMES})


def _source_excerpt(lines: list[str], node: ast.AST) -> str:
    start = max(int(getattr(node, "lineno", 1)) - 1, 0)
    end = max(int(getattr(node, "end_lineno", start + 1)), start + 1)
    return " ".join(line.strip() for line in lines[start:end]).strip()


def _contains_keyword(value: str, keywords: Iterable[str]) -> bool:
    lowered = value.lower()
    return any(keyword in lowered for keyword in keywords)


class DependencyVisitor(ast.NodeVisitor):
    """Collect decision-relevant and output-only uses without executing runtime code."""

    def __init__(self, *, path: Path, source: str, source_root: Path) -> None:
        self.relative_path = path.relative_to(source_root.parent).as_posix()
        self.lines = source.splitlines()
        self.function_stack: list[str] = []
        self.records: list[dict[str, object]] = []
        self._recorded_nodes: set[int] = set()

    @property
    def function(self) -> str:
        return ".".join(self.function_stack) if self.function_stack else "<module>"

    def _record(
        self,
        node: ast.AST,
        *,
        decision_type: str,
        classification: str,
        special_logic: str = "",
    ) -> None:
        node_id = id(node)
        if node_id in self._recorded_nodes:
            return
        names = _tracked_names(node)
        if not names:
            return
        self._recorded_nodes.add(node_id)
        self.records.append(
            {
                "file": self.relative_path,
                "function": self.function,
                "line": int(getattr(node, "lineno", 1)),
                "end_line": int(getattr(node, "end_lineno", getattr(node, "lineno", 1))),
                "tracked_names": names,
                "classification": classification,
                "decision_type": decision_type,
                "called_special_logic": special_logic or None,
                "source": _source_excerpt(self.lines, node),
            }
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Compare(self, node: ast.Compare) -> None:
        self._record(node, decision_type="semantic_or_geometric_branch", classification="forbidden_runtime_decision")
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        if _tracked_names(node.test):
            self._record(node.test, decision_type="semantic_or_geometric_branch", classification="forbidden_runtime_decision")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        names = _tracked_names(node)
        if names:
            called = _call_name(node.func)
            if _contains_keyword(called, OUTPUT_KEYS):
                self._record(
                    node,
                    decision_type="output_name_or_reporting",
                    classification="legitimate_output_or_metadata",
                    special_logic=called,
                )
            elif _contains_keyword(called, SEMANTIC_KEYS):
                self._record(
                    node,
                    decision_type="renderer_optimizer_or_geometry_selection",
                    classification="forbidden_runtime_decision",
                    special_logic=called,
                )
            else:
                self._record(
                    node,
                    decision_type="unclassified_runtime_flow",
                    classification="review_required",
                    special_logic=called,
                )
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        if _tracked_names(node):
            self._record(node, decision_type="output_name_or_reporting", classification="legitimate_output_or_metadata")
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        for key, value in zip(node.keys, node.values):
            if not _tracked_names(value):
                continue
            key_value = key.value if isinstance(key, ast.Constant) and isinstance(key.value, str) else ""
            classification = (
                "legitimate_output_or_metadata"
                if _contains_keyword(key_value, OUTPUT_KEYS | TRACKED_NAMES)
                else "review_required"
            )
            decision_type = "output_name_or_reporting" if classification.startswith("legitimate") else "unclassified_runtime_flow"
            self._record(value, decision_type=decision_type, classification=classification)
        self.generic_visit(node)


def scan_source(source_root: Path = DEFAULT_SOURCE_ROOT) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(source_root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        visitor = DependencyVisitor(path=path, source=source, source_root=source_root)
        visitor.visit(ast.parse(source, filename=str(path)))
        records.extend(visitor.records)
    return sorted(records, key=lambda item: (str(item["file"]), int(item["line"]), str(item["decision_type"])))


def build_report(source_root: Path = DEFAULT_SOURCE_ROOT) -> dict[str, object]:
    records = scan_source(source_root)
    classifications = Counter(str(record["classification"]) for record in records)
    decision_types = Counter(str(record["decision_type"]) for record in records)
    resolved_source_root = source_root.resolve()
    try:
        reported_source_root = resolved_source_root.relative_to(ROOT).as_posix()
    except ValueError:
        reported_source_root = resolved_source_root.as_posix()
    return {
        "schema_version": 1,
        "source_root": reported_source_root,
        "tracked_names": sorted(TRACKED_NAMES),
        "summary": {
            "total": len(records),
            "by_classification": dict(sorted(classifications.items())),
            "by_decision_type": dict(sorted(decision_types.items())),
        },
        "dependencies": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_report(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(f"Wrote {summary['total']} runtime image-name dependencies to {args.output}")
    for classification, count in summary["by_classification"].items():
        print(f"- {classification}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
