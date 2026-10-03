from pathlib import Path
import re


TASKBOARD = Path("docs/open_tasks.md")


def _target_alignment_sections(document: str) -> dict[str, str]:
    matches = list(re.finditer(r"^- \[[ x]\] \*\*(ZG\d+) \(P\d\):", document, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(document)
        sections[match.group(1)] = document[match.start() : end]
    return sections


def test_target_alignment_tasks_have_acceptance_and_exit_conditions() -> None:
    sections = _target_alignment_sections(TASKBOARD.read_text(encoding="utf-8"))

    assert set(sections) == {f"ZG{number}" for number in range(1, 10)}
    for task_id, section in sections.items():
        assert "Akzeptanz:" in section, f"{task_id} has no acceptance criterion"
        assert "Exit-Bedingung:" in section, f"{task_id} has no exit condition"


def test_taskboard_anchoring_closes_only_after_predecessors() -> None:
    document = TASKBOARD.read_text(encoding="utf-8")
    sections = _target_alignment_sections(document)

    for number in range(1, 9):
        assert sections[f"ZG{number}"].startswith("- [x]")
    assert sections["ZG9"].startswith("- [x]")
    assert "Definition of Done" in sections["ZG9"]
