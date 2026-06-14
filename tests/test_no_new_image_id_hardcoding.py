from tools.check_no_new_image_id_hardcoding import DEFAULT_BASELINE, scan_source, violations
import json


def test_runtime_source_adds_no_image_ids_above_migration_baseline() -> None:
    baseline = json.loads(DEFAULT_BASELINE.read_text(encoding="utf-8"))["files"]
    assert violations(scan_source(), baseline) == []
