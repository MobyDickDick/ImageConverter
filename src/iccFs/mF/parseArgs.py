def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
            f"{AC08_REGRESSION_SET_NAME}: {', '.join(AC08_REGRESSION_VARIANTS)})"
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
    parser.add_argument(
        "--export-call-tree-csv",
        nargs="?",
        const=DEFAULT_CALL_TREE_CSV_PATH,
        default=None,
        help=(
            "Erstellt einen moduleigenen Aufrufbaum aus imageCompositeConverter.py und schreibt ihn als CSV. "
            "Optional kann ein Zielpfad angegeben werden "
            f"(Default: {DEFAULT_CALL_TREE_CSV_PATH})."
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
        default=SVG_RENDER_SUBPROCESS_TIMEOUT_SEC,
        help="Timeout pro isoliertem SVG-Render-Aufruf in Sekunden (Default: 20).",
    )
    parser.add_argument("--_render-svg-subprocess", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.iterations_override is not None:
        args.iterations = args.iterations_override
    delattr(args, "iterations_override")
    return args
