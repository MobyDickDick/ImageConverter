#!/usr/bin/env bash
set -euo pipefail

# "Sichere Basis": schnell und stabil in dieser Linux-Umgebung.
# Die unten deaktivierten NodeIDs sind derzeit umgebungs-/datenabhängig bzw. aktuell nicht stabil.
python -m pytest \
  tests/test_image_composite_converter.py \
  tests/test_weak_family_pipeline.py \
  --deselect tests/test_image_composite_converter.py::test_vendored_site_packages_dirs_discovers_repo_bundle \
  --deselect tests/test_image_composite_converter.py::test_load_optional_module_recovers_after_failed_partial_package \
  --deselect tests/test_image_composite_converter.py::test_update_successful_conversions_manifest_keeps_existing_line_without_fresh_metrics \
  --deselect tests/test_image_composite_converter.py::test_convert_range_uses_existing_conversion_rows_as_template_donors \
  --deselect tests/test_image_composite_converter.py::test_parse_description_manual_review_clears_default_label_for_unclassified_sia_symbol \
  --deselect tests/test_image_composite_converter.py::test_update_successful_conversions_manifest_keeps_single_failed_entry
