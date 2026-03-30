from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _latest_failed_conversion_manifest_entry(reports_out_dir: str) -> dict[str, object] | None:
    """Return the most recent failed conversion as a manifest-like row."""
    summary_path = Path(reports_out_dir) / "batch_failure_summary.csv"
    if not summary_path.exists():
        return None

    latest_row: dict[str, str] | None = None
    try:
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                filename = str(row.get("filename", "")).strip()
                status = str(row.get("status", "")).strip().lower()
                if not filename or status not in {"render_failure", "batch_error", "semantic_mismatch"}:
                    continue
                latest_row = row
    except OSError:
        return None

    if latest_row is None:
        return None

    variant = Path(str(latest_row.get("filename", "")).strip()).stem.upper()
    if not variant:
        return None

    return {
        "variant": variant,
        "status": "failed",
        "failure_reason": str(latest_row.get("reason", "")).strip(),
    }
