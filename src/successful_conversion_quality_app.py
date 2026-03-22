"""CLI helper to record quality metrics for marked-good conversions."""

from __future__ import annotations

import argparse
from pathlib import Path

from src import image_composite_converter as converter


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aktualisiert `successful_conversions.txt` mit Qualitätskennzahlen für alle dort markierten Bildvarianten."
        )
    )
    parser.add_argument(
        "--folder-path",
        default="artifacts/images_to_convert",
        help="Ordner mit den Originalbildern",
    )
    parser.add_argument(
        "--svg-dir",
        default="artifacts/converted_images/svg",
        help="Ordner mit den konvertierten SVG-Dateien",
    )
    parser.add_argument(
        "--reports-dir",
        default="artifacts/converted_images/reports",
        help="Ordner für vorhandene Logs und den neuen Qualitätsreport",
    )
    parser.add_argument(
        "--output-name",
        default="successful_conversion_quality",
        help="Basisname der erzeugten CSV/TXT-Dateien",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    csv_path, txt_path, metrics = converter.write_successful_conversion_quality_report(
        folder_path=args.folder_path,
        svg_out_dir=args.svg_dir,
        reports_out_dir=args.reports_dir,
        output_name=args.output_name,
    )
    manifest_path = Path(args.reports_dir) / "successful_conversions.txt"
    print(f"[INFO] Manifest aktualisiert: {manifest_path}")
    print(f"[INFO] Qualitätsreport geschrieben: {Path(csv_path)}")
    print(f"[INFO] Zusammenfassung geschrieben: {Path(txt_path)}")
    print(f"[INFO] Erfasste Varianten: {len(metrics)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
