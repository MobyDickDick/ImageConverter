from __future__ import annotations

import argparse
import contextlib
import io
import sys
from pathlib import Path

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
