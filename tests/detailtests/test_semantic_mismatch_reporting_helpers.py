from src.iCCModules import imageCompositeConverterSemanticMismatchReporting as helpers


def test_build_semantic_connector_debug_line_impl_formats_all_fields() -> None:
    line = helpers.buildSemanticConnectorDebugLineImpl(
        structural={
            "connector_orientation": "vertical",
            "circle_detection_source": "family_fallback",
            "horizontal_line_candidates": 1,
            "vertical_line_candidates": 3,
        }
    )
    assert (
        line
        == "semantic_connector_classification=vertical;"
        "circle_source=family_fallback;"
        "horizontal_candidates=1;"
        "vertical_candidates=3"
    )


def test_build_semantic_mismatch_console_lines_impl_lists_issues_in_order() -> None:
    lines = helpers.buildSemanticMismatchConsoleLinesImpl(
        connector_debug_line="semantic_connector_classification=ambiguous",
        semantic_issues=["issue-one", "issue-two"],
    )
    assert lines == [
        "[ERROR] Semantik-Abgleich fehlgeschlagen:",
        "  - semantic_connector_classification=ambiguous",
        "  - issue-one",
        "  - issue-two",
    ]
