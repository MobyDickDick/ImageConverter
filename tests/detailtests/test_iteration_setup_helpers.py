from src.iCCModules import imageCompositeConverterIterationSetup as iteration_setup_helpers


def test_ensure_iteration_output_dirs_impl_creates_all_expected_dirs() -> None:
    calls: list[tuple[str, bool]] = []

    def _fake_makedirs(path: str, exist_ok: bool) -> None:
        calls.append((path, exist_ok))

    iteration_setup_helpers.ensureIterationOutputDirsImpl(
        svg_out_dir="/tmp/svg",
        diff_out_dir="/tmp/diff",
        reports_out_dir="/tmp/reports",
        makedirs_fn=_fake_makedirs,
    )

    assert calls == [
        ("/tmp/svg", True),
        ("/tmp/diff", True),
        ("/tmp/reports", True),
    ]


def test_build_iteration_base_and_log_path_impl_formats_log_name() -> None:
    base, log_path = iteration_setup_helpers.buildIterationBaseAndLogPathImpl(
        filename="AC0811_S.jpg",
        reports_out_dir="reports",
    )

    assert base == "AC0811_S"
    assert log_path == "reports/AC0811_S_element_validation.log"


def test_emit_iteration_description_header_impl_prints_description_and_fallback_elements() -> None:
    lines: list[str] = []

    iteration_setup_helpers.emitIterationDescriptionHeaderImpl(
        filename="AC0800_S.jpg",
        params={
            "description_fragments": [{"text": "SEMANTIC:"}, {"text": "Kreis ohne Buchstabe"}],
            "elements": [],
        },
        print_fn=lines.append,
    )

    assert lines == [
        "\n--- Verarbeite AC0800_S.jpg ---",
        "Bildbeschreibung: SEMANTIC: Kreis ohne Buchstabe",
        "Befehl erkannt: Kein Compositing-Befehl gefunden",
    ]
