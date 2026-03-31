def _isSuccessfulConversionCandidateBetter(
    previous_metrics: dict[str, object] | None,
    candidate_metrics: dict[str, object],
) -> bool:
    """Accept a new best-list candidate only when it improves quality."""
    if not _successfulConversionMetricsAvailable(candidate_metrics):
        return False
    if not previous_metrics or not _successfulConversionMetricsAvailable(previous_metrics):
        return True

    previous_status = str(previous_metrics.get('status', '')).strip().lower()
    candidate_status = str(candidate_metrics.get('status', '')).strip().lower()
    if previous_status == 'semantic_ok' and candidate_status != 'semantic_ok':
        return False
    if previous_status != 'semantic_ok' and candidate_status == 'semantic_ok':
        return True

    improved, _decision, _prev_error, _new_error, _prev_delta, _new_delta = _evaluateQualityPassCandidate(
        previous_metrics,
        candidate_metrics,
    )
    return improved
