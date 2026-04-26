from __future__ import annotations

import csv
from pathlib import Path

from tools.generate_form_code_inventory import collect_form_code_hits, write_inventory_csv


def test_collect_form_code_hits_detects_runtime_string_literals(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    runtime_file = src_dir / "runtime.py"
    runtime_file.write_text(
        "def run():\n"
        "    family = 'AC0811_S'\n"
        "    return family, 'GE1234', 'AR9999_X'\n",
        encoding="utf-8",
    )

    hits = collect_form_code_hits(src_dir)

    assert [hit.code for hit in hits] == ["AC0811_S", "GE1234", "AR9999_X"]
    assert all(hit.file.endswith("runtime.py") for hit in hits)


def test_collect_form_code_hits_excludes_comments_docstrings_and_help_text(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    runtime_file = src_dir / "runtime.py"
    runtime_file.write_text(
        '"""Module docs AC0001 should not count."""\n'
        "# Comment AC0002 should not count\n"
        "import argparse\n\n"
        "def run() -> str:\n"
        '    """Function docs AC0003 should not count."""\n'
        "    parser = argparse.ArgumentParser(description='Description AC0004 should not count')\n"
        "    parser.add_argument('--start', help='Help AC0005 should not count')\n"
        "    variant = 'AC0800_L'\n"
        "    return variant\n",
        encoding="utf-8",
    )

    hits = collect_form_code_hits(src_dir)

    assert [hit.code for hit in hits] == ["AC0800_L"]


def test_write_inventory_csv_writes_semicolon_delimited_rows(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "runtime.py").write_text("value = 'AC0800_L'\n", encoding="utf-8")

    hits = collect_form_code_hits(src_dir)
    output_path = tmp_path / "reports" / "inventory.csv"
    write_inventory_csv(hits, output_path)

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    assert rows == [
        {
            "code": "AC0800_L",
            "file": (src_dir / "runtime.py").as_posix(),
            "line": "1",
            "column": "9",
            "line_text": "value = 'AC0800_L'",
        }
    ]
