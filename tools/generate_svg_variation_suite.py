from __future__ import annotations

import argparse
import csv
from pathlib import Path

SVG_TEMPLATE = """<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>\n  <rect width='100%' height='100%' fill='white'/>\n  {content}\n</svg>\n"""


def _svg_circle_letter(cx: int, cy: int, r: int, letter: str = "A") -> str:
    return (
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='black' stroke-width='4'/>"
        f"<text x='{cx}' y='{cy + r // 3}' font-size='{int(r * 0.9)}' text-anchor='middle' fill='black'>{letter}</text>"
    )


def _svg_cross(center_x: int, center_y: int, half: int, stroke_w: int) -> str:
    return (
        f"<line x1='{center_x-half}' y1='{center_y}' x2='{center_x+half}' y2='{center_y}' stroke='black' stroke-width='{stroke_w}'/>"
        f"<line x1='{center_x}' y1='{center_y-half}' x2='{center_x}' y2='{center_y+half}' stroke='black' stroke-width='{stroke_w}'/>"
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a deterministic SVG variation suite for N6.")
    p.add_argument("--out-dir", type=Path, default=Path("artifacts/images_to_convert/n6_variations"))
    p.add_argument("--catalog-csv", type=Path, default=Path("artifacts/converted_images/reports/n6_variation_catalog.csv"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.catalog_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str | int]] = []

    # Teil A: Parameterfächer für Kreis + Buchstabe
    for idx, (cx, cy, r) in enumerate([(128, 128, 42), (132, 124, 48), (120, 136, 54)], start=1):
        variant = f"N6A_CIRCLE_{idx:02d}"
        content = _svg_circle_letter(cx, cy, r)
        svg = SVG_TEMPLATE.format(w=256, h=256, content=content)
        (args.out_dir / f"{variant}.svg").write_text(svg, encoding="utf-8")
        rows.append({"variant": variant, "group": "N6A", "shape": "circle_letter", "cx": cx, "cy": cy, "r": r})

    # Teil B: Verknüpfungen (zentriertes Kreuz mit gleicher Länge)
    for idx, (half, stroke_w) in enumerate([(40, 6), (52, 6), (64, 8)], start=1):
        variant = f"N6B_CROSS_{idx:02d}"
        content = _svg_cross(128, 128, half, stroke_w)
        svg = SVG_TEMPLATE.format(w=256, h=256, content=content)
        (args.out_dir / f"{variant}.svg").write_text(svg, encoding="utf-8")
        rows.append({"variant": variant, "group": "N6B", "shape": "centered_cross", "half_len": half, "stroke_w": stroke_w})

    with args.catalog_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = sorted({k for r in rows for k in r.keys()})
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"generated_svg={len(rows)}")
    print(f"out_dir={args.out_dir}")
    print(f"catalog_csv={args.catalog_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
