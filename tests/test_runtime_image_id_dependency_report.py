from __future__ import annotations

import json
from pathlib import Path

from tools.report_runtime_image_id_dependencies import build_report, main


def _write_source(root: Path) -> None:
    package = root / "src"
    package.mkdir()
    (package / "runtime.py").write_text(
        """
def convert(base_name, variant_name, params, output_dir):
    if base_name.upper() == "CATALOG_FAMILY":
        params = select_geometry_renderer(base_name, params)
    save_svg(output_dir / f"{variant_name}.svg", params)
    audit = {"base_name": base_name}
    return passthrough(variant_name), audit
""".lstrip(),
        encoding="utf-8",
    )


def test_report_distinguishes_decisions_output_names_and_review_items(tmp_path: Path) -> None:
    _write_source(tmp_path)

    report = build_report(tmp_path / "src")
    dependencies = report["dependencies"]

    assert any(
        item["classification"] == "forbidden_runtime_decision"
        and item["decision_type"] == "semantic_or_geometric_branch"
        and item["function"] == "convert"
        for item in dependencies
    )
    assert any(
        item["classification"] == "forbidden_runtime_decision"
        and item["called_special_logic"] == "select_geometry_renderer"
        for item in dependencies
    )
    assert any(
        item["classification"] == "legitimate_output_or_metadata"
        and item["decision_type"] == "output_name_or_reporting"
        for item in dependencies
    )
    assert any(
        item["classification"] == "review_required"
        and item["called_special_logic"] == "passthrough"
        for item in dependencies
    )
    assert all({"file", "function", "decision_type", "called_special_logic"} <= item.keys() for item in dependencies)


def test_cli_writes_machine_readable_report(tmp_path: Path, monkeypatch) -> None:
    _write_source(tmp_path)
    output = tmp_path / "report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "report_runtime_image_id_dependencies.py",
            "--source-root",
            str(tmp_path / "src"),
            "--output",
            str(output),
        ],
    )

    assert main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["summary"]["total"] == len(payload["dependencies"])
    assert payload["summary"]["by_classification"]["forbidden_runtime_decision"] >= 2
