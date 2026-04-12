from __future__ import annotations


def buildSemanticConnectorDebugLineImpl(*, structural: dict[str, object]) -> str:
    connector_orientation = str(structural.get("connector_orientation", "unknown"))
    circle_source = str(structural.get("circle_detection_source", "unknown"))
    horizontal_candidates = int(structural.get("horizontal_line_candidates", 0) or 0)
    vertical_candidates = int(structural.get("vertical_line_candidates", 0) or 0)
    return (
        "semantic_connector_classification="
        f"{connector_orientation};"
        f"circle_source={circle_source};"
        f"horizontal_candidates={horizontal_candidates};"
        f"vertical_candidates={vertical_candidates}"
    )


def buildSemanticMismatchConsoleLinesImpl(*, connector_debug_line: str, semantic_issues: list[str]) -> list[str]:
    return [
        "[ERROR] Semantik-Abgleich fehlgeschlagen:",
        f"  - {connector_debug_line}",
        *[f"  - {issue}" for issue in semantic_issues],
    ]
