from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
from pathlib import Path


def parseArgsImpl(
    *,
    argv: list[str] | None,
    ac08_regression_set_name: str,
    ac08_regression_variants: tuple[str, ...],
    svg_render_subprocess_timeout_sec: float,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verarbeite einen Bildordner entweder im Analysemodus (Bounding-Boxes/JSON) "
            "oder im Konvertierungsmodus (SVG-/Diff-/Report-Ausgaben)."
        ),
        epilog=(
            "Beispiele:\n"
            "  python -m src.imageCompositeConverter artifacts/images_to_convert "
            "--descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml "
            "--output-dir artifacts/converted_images --start AC0000 --end ZZ9999\n"
            "  python -m src.imageCompositeConverter artifacts/images_to_convert "
            "--mode annotate --output-dir artifacts/annotated --start AC0811 --end AC0814\n"
            "  python -m src.imageCompositeConverter --print-linux-vendor-command --vendor-dir vendor"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=("annotate", "convert"),
        default="convert",
        help="annotate=markiere Kreis/Kellenstiel/Schrift und schreibe Koordinaten; convert=SVG-Konvertierung mit Reports",
    )
    parser.add_argument(
        "folder_path",
        nargs="?",
        default="artifacts/images_to_convert",
        help="Pfad zum Ordner mit den Bildern (Default: artifacts/images_to_convert)",
    )
    parser.add_argument(
        "csv_or_output",
        nargs="?",
        default=None,
        help=(
            "Optional: Pfad zur CSV/TSV/XML-Export-Tabelle ODER Ausgabeverzeichnis für konvertierte Dateien. "
            "(Kompatibilität: bisheriger 2. Positionsparameter)"
        ),
    )
    parser.add_argument(
        "iterations",
        nargs="?",
        type=int,
        default=128,
        help="Anzahl der Iterationen (optional, default: 128)",
    )
    parser.add_argument(
        "--csv-path",
        "--descriptions-path",
        dest="csv_path",
        default=None,
        help="Expliziter Pfad zur CSV/TSV/XML-Export-Tabelle mit den Beschreibungen",
    )
    parser.add_argument("--output-dir", default=None, help="Explizites Ausgabeverzeichnis")
    parser.add_argument(
        "--iterations",
        dest="iterations_override",
        type=int,
        default=None,
        help="Benannter Alias für die Iterationszahl; überschreibt den optionalen Positionswert",
    )
    parser.add_argument("--start", default=None, help="Start-Referenz (inkl.); wenn nicht gesetzt, erfolgt eine Konsolenabfrage")
    parser.add_argument("--end", default=None, help="End-Referenz (inkl.); wenn nicht gesetzt, erfolgt eine Konsolenabfrage")
    parser.add_argument(
        "--interactive-range",
        action="store_true",
        help=(
            "Fragt auf der Konsole 'Namen von' und 'Namen bis' ab und verarbeitet nur diesen Bereich. "
            "Wenn beide Eingaben keine volle Referenz sind, wird nach ihrem gemeinsamen Teilstring gefiltert "
            "(z. B. AC08 und A08 => alle A08*-Dateien)."
        ),
    )
    parser.add_argument(
        "--debug-ac0811-dir",
        default=None,
        help="Optional: Ordner für AC0811 Element-Diff-Dumps pro Runde/Element",
    )
    parser.add_argument(
        "--debug-element-diff-dir",
        default=None,
        help="Optional: Ordner für Element-Diff-Dumps pro Runde/Element für alle Semantic-Badges",
    )
    parser.add_argument(
        "--bootstrap-deps",
        action="store_true",
        help=(
            "Installiert fehlende Bild-Abhängigkeiten (numpy, opencv-python-headless) "
            "automatisch via pip vor der Konvertierung."
        ),
    )
    parser.add_argument(
        "--ac08-regression-set",
        action="store_true",
        help=(
            "Verarbeitet genau das feste AC08-Regression-Set ("
            f"{ac08_regression_set_name}: {', '.join(ac08_regression_variants)})"
        ),
    )
    parser.add_argument(
        "--log-file",
        default=os.environ.get("IMAGE_COMPOSITE_CONVERTER_LOG_FILE", ""),
        help=(
            "Optional: Schreibt den kompletten Konsolen-Output zusätzlich in diese Datei. "
            "Kann alternativ über IMAGE_COMPOSITE_CONVERTER_LOG_FILE gesetzt werden."
        ),
    )
    parser.add_argument(
        "--print-linux-vendor-command",
        action="store_true",
        help=(
            "Gibt einen pip-Aufruf aus, der Linux-kompatible Wheels für numpy/opencv/Pillow/PyMuPDF "
            "in das Vendor-Verzeichnis installiert."
        ),
    )
    parser.add_argument("--vendor-dir", default="vendor", help="Zielordner für vendorte Python-Pakete")
    parser.add_argument(
        "--vendor-platform",
        default="manylinux2014_x86_64",
        help="pip --platform Wert für Linux-Wheels, z. B. manylinux2014_x86_64",
    )
    parser.add_argument(
        "--vendor-python-version",
        default=None,
        help="pip --python-version Wert ohne Punkt, z. B. 311 oder 312",
    )
    parser.add_argument(
        "--isolate-svg-render",
        action="store_true",
        help=(
            "Rendert SVGs in einem isolierten Subprozess, damit native PyMuPDF-"
            "Abstürze den Hauptlauf nicht beenden."
        ),
    )
    parser.add_argument(
        "--isolate-svg-render-timeout-sec",
        type=float,
        default=svg_render_subprocess_timeout_sec,
        help="Timeout pro isoliertem SVG-Render-Aufruf in Sekunden (Default: 20).",
    )
    parser.add_argument(
        "--deterministic-order",
        action="store_true",
        help=(
            "Deaktiviert Shuffle-Schritte bei Dateireihenfolge/Template-Donor-Auswahl "
            "für reproduzierbare Diagnoseläufe."
        ),
    )
    parser.add_argument("--_render-svg-subprocess", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.iterations_override is not None:
        args.iterations = args.iterations_override
    delattr(args, "iterations_override")
    return args


def autoDetectCsvPathImpl(folder_path: str) -> str | None:
    """Best-effort table lookup for CLI compatibility mode."""
    candidates: list[str] = []
    roots = [folder_path, os.path.dirname(folder_path)]
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            lower = name.lower()
            if lower.endswith(".csv") or lower.endswith(".tsv") or lower.endswith(".xml"):
                candidates.append(os.path.join(root, name))
        if candidates:
            break

    if not candidates:
        return None

    preferred = [
        p
        for p in candidates
        if any(tag in os.path.basename(p).lower() for tag in ("reference", "roundtrip", "export", "mapping"))
    ]
    return preferred[0] if preferred else candidates[0]


def resolveCliCsvAndOutputImpl(
    args: argparse.Namespace,
    *,
    auto_detect_csv_path_fn,
    resolve_xml_path_fn,
) -> tuple[str, str | None]:
    """Resolve effective table path and output directory from mixed CLI styles."""
    csv_path = args.csv_path
    output_dir = args.output_dir
    if args.csv_or_output:
        candidate = str(args.csv_or_output)
        looks_like_csv = (
            candidate.lower().endswith(".csv")
            or candidate.lower().endswith(".tsv")
            or candidate.lower().endswith(".xml")
        )
        if csv_path is None and looks_like_csv:
            csv_path = candidate
        elif output_dir is None and not looks_like_csv:
            output_dir = candidate
        elif csv_path is None:
            csv_path = candidate

    if csv_path is None:
        csv_path = auto_detect_csv_path_fn(args.folder_path) or ""
    elif str(csv_path).lower().endswith(".xml"):
        csv_path = resolve_xml_path_fn(csv_path) or csv_path

    return csv_path, output_dir


def formatUserDiagnosticImpl(
    exc: BaseException,
    *,
    description_mapping_error_type,
) -> str:
    """Render structured loader/runtime errors into one compact CLI message."""
    if isinstance(exc, description_mapping_error_type):
        span = getattr(exc, "span", None)
        if span is not None:
            return f"{exc.message} Ort: {span.format()}."
        return str(getattr(exc, "message", str(exc)))
    return str(exc)


def promptInteractiveRangeImpl(
    args: argparse.Namespace,
    *,
    shared_partial_range_token_fn,
    extract_ref_parts_fn,
) -> tuple[str, str]:
    """Prompt the user for start/end filters while preserving existing defaults."""
    current_start = str(args.start or "").strip()
    current_end = str(args.end or "").strip()
    prompt_start = f"Namen von [{current_start}]: " if current_start else "Namen von: "
    prompt_end = f"Namen bis [{current_end}]: " if current_end else "Namen bis: "

    start_value = input(prompt_start).strip() or current_start
    end_value = input(prompt_end).strip() or current_end
    if not end_value:
        end_value = start_value

    shared = shared_partial_range_token_fn(start_value, end_value)
    if shared and extract_ref_parts_fn(start_value) is None and extract_ref_parts_fn(end_value) is None:
        print(f"[INFO] Verwende Teilstring-Filter '{shared}' für die Auswahl der Bilder.")
    else:
        print(f"[INFO] Verwende Bereich von '{start_value or '(Anfang)'}' bis '{end_value or '(Ende)'}'.")
    return start_value, end_value


class TeeTextIO(io.TextIOBase):
    """Mirror text writes to multiple streams."""

    def __init__(self, *streams: io.TextIOBase):
        self._streams = streams

    def write(self, s: str) -> int:
        for stream in self._streams:
            stream.write(s)
        return len(s)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


@contextlib.contextmanager
def optionalLogCaptureImpl(log_path: str):
    """Duplicate stdout/stderr into ``log_path`` if configured."""
    if not log_path:
        yield
        return

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as logfile:
        tee_stdout = TeeTextIO(sys.stdout, logfile)
        tee_stderr = TeeTextIO(sys.stderr, logfile)
        with contextlib.redirect_stdout(tee_stdout), contextlib.redirect_stderr(tee_stderr):
            print(f"[INFO] Schreibe Konsolen-Output nach: {path}")
            yield


def runMainImpl(
    args: argparse.Namespace,
    *,
    run_svg_render_subprocess_entrypoint_fn,
    set_svg_render_subprocess_enabled_fn,
    set_svg_render_subprocess_timeout_fn,
    optional_log_capture_fn,
    build_linux_vendor_install_command_fn,
    prompt_interactive_range_fn,
    resolve_cli_csv_and_output_fn,
    load_description_mapping_fn,
    bootstrap_required_image_dependencies_fn,
    analyze_range_fn,
    convert_range_fn,
    format_user_diagnostic_fn,
    description_mapping_error_type,
    ac08_regression_set_name: str,
    ac08_regression_variants: tuple[str, ...],
) -> int:
    if bool(getattr(args, "_render_svg_subprocess", False)):
        return run_svg_render_subprocess_entrypoint_fn()

    if bool(args.isolate_svg_render):
        set_svg_render_subprocess_enabled_fn(True)
    set_svg_render_subprocess_timeout_fn(max(1.0, float(args.isolate_svg_render_timeout_sec)))

    log_path = str(args.log_file or "").strip()
    with optional_log_capture_fn(log_path):
        try:
            if args.ac08_regression_set:
                args.start = "AC0000"
                args.end = "ZZ9999"

            if args.print_linux_vendor_command:
                print(
                    " ".join(
                        build_linux_vendor_install_command_fn(
                            vendor_dir=args.vendor_dir,
                            platform_tag=args.vendor_platform,
                            python_version=args.vendor_python_version,
                        )
                    )
                )
                return 0

            needs_prompt = bool(args.interactive_range or args.start is None or args.end is None)
            can_prompt = bool(getattr(sys.stdin, "isatty", lambda: False)())
            if needs_prompt and can_prompt:
                args.start, args.end = prompt_interactive_range_fn(args)
            elif needs_prompt:
                args.start = str(args.start or "").strip()
                args.end = str(args.end or "ZZZZZZ").strip() or args.start
                print(
                    "[INFO] Kein interaktives Terminal erkannt; "
                    f"verwende Bereich von '{args.start or '(Anfang)'}' bis '{args.end or '(Ende)'}'."
                )
            else:
                args.start = str(args.start or "").strip()
                args.end = str(args.end or "ZZZZZZ").strip() or args.start

            csv_path, output_dir = resolve_cli_csv_and_output_fn(args)

            if not csv_path:
                print("[WARN] Keine CSV/TSV/XML angegeben oder gefunden. Einige Symbole können ohne Beschreibung übersprungen werden.")
            elif not os.path.exists(csv_path):
                print(f"[WARN] CSV/TSV/XML-Datei nicht gefunden: {csv_path}")
            elif args.mode == "convert":
                load_description_mapping_fn(csv_path)

            if args.bootstrap_deps:
                try:
                    installed = bootstrap_required_image_dependencies_fn()
                except RuntimeError as exc:
                    print(f"[ERROR] {exc}")
                    return 2
                if installed:
                    print(f"[INFO] Installiert: {', '.join(installed)}")

            if args.ac08_regression_set:
                print(
                    "[INFO] Verwende festes AC08-Regression-Set "
                    f"{ac08_regression_set_name}: {', '.join(ac08_regression_variants)}"
                )
            selected_variants = set(ac08_regression_variants) if args.ac08_regression_set else None

            if args.mode == "annotate":
                out_dir = analyze_range_fn(
                    args.folder_path,
                    output_root=output_dir,
                    start_ref=args.start,
                    end_ref=args.end,
                )
            else:
                out_dir = convert_range_fn(
                    args.folder_path,
                    csv_path,
                    args.iterations,
                    args.start,
                    args.end,
                    args.debug_ac0811_dir,
                    args.debug_element_diff_dir,
                    output_dir,
                    selected_variants,
                    bool(args.deterministic_order),
                )
            print(f"\nAbgeschlossen! Ausgaben unter: {out_dir}")
            return 0
        except description_mapping_error_type as exc:
            print(f"[ERROR] {format_user_diagnostic_fn(exc)}")
            return 2
