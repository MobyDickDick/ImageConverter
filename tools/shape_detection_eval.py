from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools.shape_detection import classify_contour_shape, detect_vertical_lines


def _require_cv2_np():
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    return cv2, np


def make_synthetic_image(primitive: str, variant: str):
    cv2, np = _require_cv2_np()
    img = np.full((256, 256, 3), 255, dtype=np.uint8)
    if primitive == "line":
        cv2.line(img, (128, 30), (128, 226), (0, 0, 0), 8)
    elif primitive == "minus":
        cv2.line(img, (98, 48), (158, 48), (0, 0, 0), 8)
    elif primitive == "triangle":
        pts = np.array([[128, 30], [40, 220], [216, 220]], dtype=np.int32)
        cv2.fillPoly(img, [pts], (0, 0, 0))
    elif primitive == "rectangle":
        cv2.rectangle(img, (56, 56), (200, 200), (0, 0, 0), -1)
    elif primitive == "arrow":
        pts = np.array([[40, 120], [150, 120], [150, 90], [220, 128], [150, 166], [150, 136], [40, 136]], dtype=np.int32)
        cv2.fillPoly(img, [pts], (0, 0, 0))
    elif primitive == "circle":
        cv2.circle(img, (128, 128), 78, (0, 0, 0), -1)

    if variant == "real":
        noise = np.random.default_rng(42).normal(0, 9, img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img = cv2.GaussianBlur(img, (5, 5), 0)
    return img


def detect_primitive_label(img) -> str:
    cv2, _ = _require_cv2_np()
    lines = detect_vertical_lines(img)
    if lines and lines[0].length_px > 120:
        return "line"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "unknown"
    contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    circularity = 4 * 3.141592653589793 * area / (perimeter * perimeter + 1e-9)
    if circularity > 0.82:
        return "circle"
    cls = classify_contour_shape(contour)
    return cls.primitive


def run_eval(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    primitives = ["circle", "triangle", "arrow", "rectangle", "line"]
    rows = []
    for primitive in primitives:
        for variant in ["synthetic", "real"]:
            img = make_synthetic_image(primitive, variant)
            pred = detect_primitive_label(img)
            rows.append({"sample_id": f"{primitive}_{variant}", "expected": primitive, "predicted": pred, "match": int(pred == primitive)})

    csv_path = output_dir / "shape_detection_eval_report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "expected", "predicted", "match"])
        writer.writeheader()
        writer.writerows(rows)

    acc = sum(r["match"] for r in rows) / len(rows)
    summary = {"samples": len(rows), "accuracy": round(acc, 4), "csv_report": str(csv_path)}
    json_path = output_dir / "shape_detection_eval_summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/converted_images/reports")
    args = parser.parse_args()
    summary = run_eval(Path(args.output_dir))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
