"""Fallback conversion helpers for environments without numpy/opencv."""

from __future__ import annotations

import csv
import os


def runEmbeddedRasterFallbackImpl(
    *,
    files: list[str],
    folder_path: str,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str,
    render_embedded_raster_svg_fn,
    create_diff_image_without_cv2_fn,
    generate_conversion_overviews_fn,
    fitz_module,
) -> None:
    log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    with open(log_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Dateiname", "Gefundene Elemente", "Beste Iteration", "Diff-Score", "FehlerProPixel"])
        for filename in files:
            stem = os.path.splitext(filename)[0]
            image_path = os.path.join(folder_path, filename)
            svg_content = render_embedded_raster_svg_fn(image_path)
            svg_path = os.path.join(svg_out_dir, f"{stem}.svg")
            with open(svg_path, "w", encoding="utf-8") as svg_file:
                svg_file.write(svg_content)
            if fitz_module is not None:
                diff = create_diff_image_without_cv2_fn(image_path, svg_content)
                diff.save(os.path.join(diff_out_dir, f"{stem}_diff.png"))
            writer.writerow([filename, "embedded-raster", 0, "0.00", "0.00000000"])

    with open(os.path.join(reports_out_dir, "fallback_mode.txt"), "w", encoding="utf-8") as f:
        f.write(
            "Fallback-Modus aktiv: fehlende numpy/opencv-Abhängigkeiten; "
            "SVG-Dateien wurden als eingebettete Rasterbilder erzeugt"
            + (" und Differenzbilder via Pillow/PyMuPDF geschrieben.\n" if fitz_module is not None else ".\n")
        )

    generate_conversion_overviews_fn(diff_out_dir, svg_out_dir, reports_out_dir)
