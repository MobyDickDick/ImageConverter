    allowed_error_pp = successful_threshold
    cfg_value = cfg.get("allowed_error_per_pixel")
    if cfg_value is not None:
        try:
            allowed_error_pp = max(0.0, float(cfg_value))
            threshold_source = "manual-config"
        except (TypeError, ValueError):
            allowed_error_pp = successful_threshold

    # Global policy: do not freeze individual variants. Every quality pass keeps
    # all variants eligible so each run can re-evaluate with stochastic search
    # while still converging by only accepting strict improvements.
    skip_variants: set[str] = set()

    _write_quality_config(
        reports_out_dir,
        allowed_error_per_pixel=allowed_error_pp,
        skipped_variants=sorted(v for v in skip_variants if v),
        source=threshold_source,
    )

    # Iteratively refine unresolved quality cases while preserving all already
    # successful outputs (replace only when strictly better).
    strategy_logs: list[dict[str, object]] = []
    for pass_idx in range(1, max_quality_passes + 1):
        if stop_after_failure:
            break
        Action.STOCHASTIC_SEED_OFFSET = pass_idx
        current_rows = [
            row
            for row in result_map.values()
            if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
        ]
        candidates = _select_open_quality_cases(
            current_rows,
            allowed_error_per_pixel=allowed_error_pp,
            skip_variants=skip_variants,
        )
        # Fallback to the historical selection when no explicit open set exists
        # (e.g. without threshold config).
        if not candidates:
            candidates = _select_middle_lower_tercile(current_rows)
        if not candidates:
            break

        improved_in_pass = False
        iteration_budget, badge_rounds = _iteration_strategy_for_pass(pass_idx, base_iterations)
        if len(candidates) > 1:
            rng.shuffle(candidates)
        for row in candidates:
            filename = str(row["filename"])
            adaptive_iteration_budget = _adaptive_iteration_budget_for_quality_row(row, iteration_budget)
            new_row, failed = _convert_one(filename, iteration_budget=adaptive_iteration_budget, badge_rounds=badge_rounds)
            if failed:
                stop_after_failure = True
                break
            if new_row is None:
                continue

            improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2 = _evaluate_quality_pass_candidate(
                row,
                new_row,
            )
            if improved:
                result_map[filename] = new_row
                improved_in_pass = True

            quality_logs.append(
                {
                    "pass": pass_idx,
                    "filename": filename,
                    "old_error_per_pixel": prev_error_pp,
                    "new_error_per_pixel": new_error_pp,
                    "old_mean_delta2": prev_mean_delta2,
                    "new_mean_delta2": new_mean_delta2,
                    "improved": improved,
                    "decision": decision,
                    "iteration_budget": adaptive_iteration_budget,
                    "badge_validation_rounds": badge_rounds,
                }
            )

        # Stop as soon as a full pass yields no strict improvement.
        if stop_after_failure or not improved_in_pass:
            break

    _write_quality_pass_report(reports_out_dir, quality_logs)
    _write_batch_failure_summary(reports_out_dir, batch_failures)
    if strategy_logs:
        strategy_path = os.path.join(reports_out_dir, "strategy_switch_template_transfers.csv")
        with open(strategy_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "filename",
                "donor_variant",
                "rotation_deg",
                "scale",
                "old_error_per_pixel",
                "new_error_per_pixel",
            ])
