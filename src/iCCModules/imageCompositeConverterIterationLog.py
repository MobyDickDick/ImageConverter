from __future__ import annotations

import csv


def writeIterationLogAndCollectSemanticImpl(
    *,
    files: list[str],
    result_map: dict[str, dict[str, object]],
    log_path: str,
) -> list[dict[str, object]]:
    semantic_results: list[dict[str, object]] = []
    with open(log_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Dateiname", "Gefundene Elemente", "Beste Iteration", "Diff-Score", "FehlerProPixel"])
        for filename in files:
            row = result_map.get(filename)
            if row is None:
                continue
            params = dict(row["params"])
            writer.writerow([
                filename,
                " + ".join(params.get("elements", [])),
                int(row["best_iter"]),
                f"{float(row['best_error']):.2f}",
                f"{float(row['error_per_pixel']):.8f}",
            ])

            if params.get("mode") == "semantic_badge":
                semantic_results.append(
                    {
                        "filename": filename,
                        "base": row["base"],
                        "variant": row["variant"],
                        "w": int(row.get("w", 0)),
                        "h": int(row.get("h", 0)),
                        "error": float(row["best_error"]),
                    }
                )
    return semantic_results
