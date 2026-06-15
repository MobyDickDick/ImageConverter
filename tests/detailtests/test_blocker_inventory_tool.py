from __future__ import annotations

from pathlib import Path

from tools.run_blocker_inventory import (
    END_MARKER,
    START_MARKER,
    parse_inventory,
    render_section,
    update_document,
)


def test_parse_inventory_orders_durations_and_collects_failures() -> None:
    durations, failures = parse_inventory(
        "1.20s call tests/test_slow.py::test_slow\n"
        "3.40s setup tests/test_setup.py::test_setup\n"
        "FAILED tests/test_slow.py::test_slow - AssertionError\n"
        "0.20s teardown tests/test_fast.py::test_fast\n",
        limit=2,
    )

    assert durations == [
        (3.4, "setup", "tests/test_setup.py::test_setup"),
        (1.2, "call", "tests/test_slow.py::test_slow"),
    ]
    assert failures == ["tests/test_slow.py::test_slow"]


def test_update_document_replaces_previous_inventory_section(tmp_path: Path) -> None:
    document = tmp_path / "open_tasks.md"
    document.write_text(
        f"# Aufgaben\n\n{START_MARKER}\nalt\n{END_MARKER}\n\n## Ende\n",
        encoding="utf-8",
    )
    section = render_section(
        run_id="run-test",
        log_path=Path("artifacts/test.log"),
        exit_code=0,
        command=["python", "-m", "pytest"],
        durations=[(1.25, "call", "tests/test_demo.py::test_demo")],
        failures=[],
    )

    update_document(document, section)

    updated = document.read_text(encoding="utf-8")
    assert updated.count(START_MARKER) == 1
    assert updated.count(END_MARKER) == 1
    assert "alt" not in updated
    assert "`run-test`" in updated
    assert "| 1 | 1.25s | `call` | `tests/test_demo.py::test_demo` |" in updated
    assert "## Ende" in updated
