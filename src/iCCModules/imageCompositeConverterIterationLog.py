from __future__ import annotations

import csv


def optimizationRenderTelemetryImpl(row: dict[str, object]) -> dict[str, int]:
    """Return stable, public render counters for one conversion result."""
    telemetry = row.get("optimization_render_telemetry")
    if not isinstance(telemetry, dict):
        params = row.get("params")
        telemetry = params.get("_optimization_render_telemetry") if isinstance(params, dict) else None
    if not isinstance(telemetry, dict):
        telemetry = {}
    return {
        "render_timeouts": max(0, int(telemetry.get("render_timeouts", telemetry.get("timeouts", 0)) or 0)),
        "render_errors": max(0, int(telemetry.get("render_errors", telemetry.get("errors", 0)) or 0)),
    }


def writeIterationLogAndCollectSemanticImpl(
    *,
    files: list[str],
    result_map: dict[str, dict[str, object]],
    log_path: str,
) -> list[dict[str, object]]:
    semantic_results: list[dict[str, object]] = []
    with open(log_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Dateiname",
            "Gefundene Elemente",
            "Beste Iteration",
            "Diff-Score",
            "FehlerProPixel",
            "Render-Timeouts",
            "Render-Fehler",
        ])
        for filename in files:
            row = result_map.get(filename)
            if row is None:
                continue
            params = dict(row["params"])
            render_telemetry = optimizationRenderTelemetryImpl(row)
            writer.writerow([
                filename,
                " + ".join(params.get("elements", [])),
                int(row["best_iter"]),
                f"{float(row['best_error']):.2f}",
                f"{float(row['error_per_pixel']):.8f}",
                render_telemetry["render_timeouts"],
                render_telemetry["render_errors"],
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
