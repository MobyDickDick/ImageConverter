def _writePixelDelta2Ranking(folder_path: str, svg_out_dir: str, reports_out_dir: str, threshold: float = 18.0) -> None:
    ranking: list[dict[str, float | str]] = []
    for svg_name in sorted(f for f in os.listdir(svg_out_dir) if f.lower().endswith(".svg")):
        stem = os.path.splitext(svg_name)[0]
        orig_path = None
        for ext in (".jpg", ".png", ".bmp"):
            candidate = os.path.join(folder_path, f"{stem}{ext}")
            if os.path.exists(candidate):
                orig_path = candidate
                break
        if orig_path is None:
            continue

        img_orig = cv2.imread(orig_path)
        if img_orig is None:
            continue

        with open(os.path.join(svg_out_dir, svg_name), "r", encoding="utf-8") as f:
            svg_content = f.read()

        h, w = img_orig.shape[:2]
        rendered = Action.renderSvgToNumpy(svg_content, w, h)
        if rendered is None:
            continue

        mean_delta2, std_delta2 = Action.calculateDelta2Stats(img_orig, rendered)
        ranking.append(
            {
                "image": os.path.basename(orig_path),
                "mean_delta2": float(mean_delta2),
                "std_delta2": float(std_delta2),
            }
        )

    ranking.sort(key=lambda row: float(row["mean_delta2"]), reverse=True)
    csv_path = os.path.join(reports_out_dir, "pixel_delta2_ranking.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["image", "mean_delta2", "std_delta2"])
        for row in ranking:
            writer.writerow([row["image"], f"{float(row['mean_delta2']):.6f}", f"{float(row['std_delta2']):.6f}"])

    valid = [row for row in ranking if math.isfinite(float(row["mean_delta2"]))]
    count_ok = sum(1 for row in valid if float(row["mean_delta2"]) <= threshold)
    summary_lines = [
        f"images_total={len(valid)}",
        f"threshold_mean_delta2={threshold:.3f}",
        f"images_with_mean_delta2_le_threshold={count_ok}",
    ]
    with open(os.path.join(reports_out_dir, "pixel_delta2_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")
