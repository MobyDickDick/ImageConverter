def _summarizePreviousGoodAc08Variants(reports_out_dir: str) -> dict[str, object]:
    """Summarize whether previously good AC08 variants stayed semantic_ok in the latest run."""
    preserved: list[str] = []
    regressed: list[str] = []
    missing: list[str] = []

    for variant in AC08_PREVIOUSLY_GOOD_VARIANTS:
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        if not os.path.exists(log_path):
            missing.append(variant)
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            log_text = f.read()
        if "status=semantic_ok" in log_text and "status=semantic_mismatch" not in log_text:
            preserved.append(variant)
        else:
            regressed.append(variant)

    return {
        "expected": list(AC08_PREVIOUSLY_GOOD_VARIANTS),
        "preserved": preserved,
        "regressed": regressed,
        "missing": missing,
    }
