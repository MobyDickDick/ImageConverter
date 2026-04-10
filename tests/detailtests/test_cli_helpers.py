from __future__ import annotations

import argparse
import contextlib
import io
import sys
from pathlib import Path
from unittest import mock

from src.iCCModules import imageCompositeConverterCli as cli_helpers


def test_parse_args_impl_applies_named_iterations_override() -> None:
    args = cli_helpers.parseArgsImpl(
        argv=["images", "--iterations", "17"],
        ac08_regression_set_name="ac08-regression",
        ac08_regression_variants=("AC0800_L",),
        svg_render_subprocess_timeout_sec=5.0,
    )

    assert args.folder_path == "images"
    assert args.iterations == 17


def test_auto_detect_csv_path_prefers_reference_like_names(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "table.csv").write_text("x", encoding="utf-8")
    (images_dir / "reference_roundtrip.csv").write_text("x", encoding="utf-8")

    detected = cli_helpers.autoDetectCsvPathImpl(str(images_dir))
    assert detected is not None
    assert detected.endswith("reference_roundtrip.csv")




def test_auto_detect_csv_path_finds_descriptions_sibling_folder(tmp_path: Path) -> None:
    images_dir = tmp_path / "images_to_convert"
    images_dir.mkdir()
    descriptions_dir = tmp_path / "descriptions"
    descriptions_dir.mkdir()
    expected = descriptions_dir / "Finale_Wurzelformen_V3.xml"
    expected.write_text("<root/>", encoding="utf-8")

    detected = cli_helpers.autoDetectCsvPathImpl(str(images_dir))
    assert detected == str(expected)

def test_resolve_cli_csv_and_output_impl_resolves_xml_paths() -> None:
    args = argparse.Namespace(
        csv_path="descriptions.xml",
        output_dir=None,
        csv_or_output=None,
        folder_path="images",
    )

    resolved_csv, resolved_output = cli_helpers.resolveCliCsvAndOutputImpl(
        args,
        auto_detect_csv_path_fn=lambda _folder: "auto.csv",
        resolve_xml_path_fn=lambda path: f"resolved::{path}",
    )

    assert resolved_csv == "resolved::descriptions.xml"
    assert resolved_output is None


def test_optional_log_capture_impl_writes_stdout_and_stderr(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "capture.log"
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
        with cli_helpers.optionalLogCaptureImpl(str(log_path)):
            print("hello-out")
            print("hello-err", file=sys.stderr)

    log_content = log_path.read_text(encoding="utf-8")
    assert "hello-out" in log_content
    assert "hello-err" in log_content
    assert "capture.log" in log_content


def test_format_user_diagnostic_impl_formats_mapping_span() -> None:
    class FakeSpan:
        def format(self) -> str:
            return "input.csv:4:2"

    class FakeMappingError(Exception):
        def __init__(self) -> None:
            super().__init__("failed")
            self.message = "Ungültige Zeile"
            self.span = FakeSpan()

    rendered = cli_helpers.formatUserDiagnosticImpl(
        FakeMappingError(),
        description_mapping_error_type=FakeMappingError,
    )
    assert rendered == "Ungültige Zeile Ort: input.csv:4:2."


def test_prompt_interactive_range_impl_uses_substring_filter_message(capsys) -> None:
    args = argparse.Namespace(start="", end="")
    with mock.patch("builtins.input", side_effect=["AC08", "A08"]):
        start_value, end_value = cli_helpers.promptInteractiveRangeImpl(
            args,
            shared_partial_range_token_fn=lambda _start, _end: "A08",
            extract_ref_parts_fn=lambda _value: None,
        )

    assert (start_value, end_value) == ("AC08", "A08")
    captured = capsys.readouterr()
    assert "Teilstring-Filter 'A08'" in captured.out


def test_run_main_impl_prints_vendor_command_and_exits() -> None:
    args = argparse.Namespace(
        _render_svg_subprocess=False,
        isolate_svg_render=False,
        isolate_svg_render_timeout_sec=7.0,
        log_file="",
        ac08_regression_set=False,
        print_linux_vendor_command=True,
        vendor_dir="vendor",
        vendor_platform="manylinux",
        vendor_python_version="310",
        interactive_range=False,
        start="AC0001",
        end="AC0002",
        mode="convert",
        bootstrap_deps=False,
        folder_path="images",
        iterations=1,
        debug_ac0811_dir=None,
        debug_element_diff_dir=None,
        deterministic_order=False,
    )
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        rc = cli_helpers.runMainImpl(
            args,
            run_svg_render_subprocess_entrypoint_fn=lambda: 11,
            set_svg_render_subprocess_enabled_fn=lambda _enabled: None,
            set_svg_render_subprocess_timeout_fn=lambda _timeout: None,
            optional_log_capture_fn=contextlib.nullcontext,
            build_linux_vendor_install_command_fn=lambda **_kwargs: ["pip", "install", "x"],
            prompt_interactive_range_fn=lambda _args: ("AC0001", "AC0002"),
            resolve_cli_csv_and_output_fn=lambda _args: ("", None),
            load_description_mapping_fn=lambda _path: None,
            bootstrap_required_image_dependencies_fn=lambda: [],
            analyze_range_fn=lambda *_args, **_kwargs: "annotated",
            convert_range_fn=lambda *_args, **_kwargs: "converted",
            format_user_diagnostic_fn=lambda exc: str(exc),
            description_mapping_error_type=RuntimeError,
            ac08_regression_set_name="set",
            ac08_regression_variants=("AC0800_L",),
        )

    assert rc == 0
    assert "pip install x" in stdout.getvalue()


def test_run_main_impl_convert_mode_invokes_convert_with_selected_variants() -> None:
    args = argparse.Namespace(
        _render_svg_subprocess=False,
        isolate_svg_render=True,
        isolate_svg_render_timeout_sec=3.0,
        log_file="",
        ac08_regression_set=True,
        print_linux_vendor_command=False,
        vendor_dir="vendor",
        vendor_platform="manylinux",
        vendor_python_version="310",
        interactive_range=False,
        start=None,
        end=None,
        mode="convert",
        bootstrap_deps=False,
        folder_path="images",
        iterations=5,
        debug_ac0811_dir="dbg0811",
        debug_element_diff_dir="dbg-elem",
        deterministic_order=True,
    )
    calls: dict[str, object] = {}

    with mock.patch("os.path.exists", return_value=True):
        rc = cli_helpers.runMainImpl(
            args,
            run_svg_render_subprocess_entrypoint_fn=lambda: 11,
            set_svg_render_subprocess_enabled_fn=lambda enabled: calls.__setitem__("enabled", enabled),
            set_svg_render_subprocess_timeout_fn=lambda timeout: calls.__setitem__("timeout", timeout),
            optional_log_capture_fn=contextlib.nullcontext,
            build_linux_vendor_install_command_fn=lambda **_kwargs: ["pip"],
            prompt_interactive_range_fn=lambda _args: ("AC0800", "AC0899"),
            resolve_cli_csv_and_output_fn=lambda _args: ("descriptions.csv", "out"),
            load_description_mapping_fn=lambda path: calls.__setitem__("csv", path),
            bootstrap_required_image_dependencies_fn=lambda: [],
            analyze_range_fn=lambda *_args, **_kwargs: "annotated",
            convert_range_fn=lambda *fn_args, **_kwargs: calls.__setitem__("convert_args", fn_args) or "converted",
            format_user_diagnostic_fn=lambda exc: str(exc),
            description_mapping_error_type=RuntimeError,
            ac08_regression_set_name="ac08-set",
            ac08_regression_variants=("AC0800_L", "AC0811_L"),
        )

    assert rc == 0
    assert calls["enabled"] is True
    assert calls["timeout"] == 3.0
    assert calls["csv"] == "descriptions.csv"
    convert_args = calls["convert_args"]
    assert convert_args[0] == "images"
    assert convert_args[1] == "descriptions.csv"
    assert convert_args[8] == {"AC0800_L", "AC0811_L"}
    assert convert_args[9] is True
