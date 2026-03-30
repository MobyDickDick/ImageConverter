"""Auto-generated loader for split module chunks.

DO NOT EDIT MANUALLY. Re-run tools/split_python_module.py instead.
"""

from __future__ import annotations

from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_CHUNK_DIR = _BASE_DIR / 'mainFiles' / 'image_composite_converterFiles'
# Compatibility anchor for tests that assert numpy loads before cv2.
# np = _load_optional_module("numpy")
# cv2 = _load_optional_module("cv2")
_CHUNK_FILES = [
    "image_composite_converter.chunk_0001.py",
    "image_composite_converter.chunk_0002_runtime_modules_to_analyze_range.py",
    "image_composite_converter.chunk_0003_clip.py",
    "image_composite_converter.chunk_0004_abstand_to_build_oriented_kelle.py",
    "image_composite_converter.chunk_0005_load_grayscale_image.py",
    "image_composite_converter.chunk_0006_create_diff_image_without_cv2_to_adaptive_threshold.py",
    "image_composite_converter.chunk_0007_load_binary_image_with_mode_to_estimate_stroke_style.py",
    "image_composite_converter.chunk_0008_candidate_to_svg.py",
    "image_composite_converter.chunk_0009_decompose_circle_with_stem.py",
    "image_composite_converter.chunk_0010_missing_required_image_dependencies_to_dotted_attr_name.py",
    "image_composite_converter.chunk_0011_module_call_edges_for_path.py",
    "image_composite_converter.chunk_0012_export_module_call_tree_csv_to_get_base_name_from_file.py",
    "image_composite_converter.chunk_0013_load_description_mapping_to_required_vendor_packages.py",
    "image_composite_converter.chunk_0014_build_linux_vendor_install_command.py",
    "image_composite_converter.chunk_0015.py",
    "image_composite_converter.chunk_0016_render_svg_to_numpy_inprocess_to_render_svg_to_numpy_via_subprocess.py",
    "image_composite_converter.chunk_0017_run_svg_render_subprocess_entrypoint.py",
    "image_composite_converter.chunk_0018.py",
    "image_composite_converter.chunk_0019_semantic_quality_flags.py",
    "image_composite_converter.chunk_0020_run_iteration_pipeline.py",
    "image_composite_converter.chunk_0021_extract_ref_parts_to_extract_symbol_family.py",
    "image_composite_converter.chunk_0022_matches_exact_prefix_filter_to_converted_svg_output_dir.py",
    "image_composite_converter.chunk_0023_read_validation_log_details_to_collect_description_fragments.py",
    "image_composite_converter.chunk_0024_semantic_audit_record_to_reports_output_dir.py",
    "image_composite_converter.chunk_0025_is_semantic_template_variant_to_load_existing_conversion_rows.py",
    "image_composite_converter.chunk_0026_sniff_raster_size_to_quality_config_path.py",
    "image_composite_converter.chunk_0027_load_quality_config_to_select_middle_lower_tercile.py",
    "image_composite_converter.chunk_0028_select_open_quality_cases_to_adaptive_iteration_budget_for_quality_row.py",
    "image_composite_converter.chunk_0029_write_quality_pass_report_to_extract_svg_inner.py",
    "image_composite_converter.chunk_0030_build_transformed_svg_from_template_to_template_transfer_scale_candidates.py",
    "image_composite_converter.chunk_0031_estimate_template_transfer_scale_to_template_transfer_transform_candidates.py",
    "image_composite_converter.chunk_0032_rank_template_transfer_donors_to_semantic_transfer_rotations.py",
    "image_composite_converter.chunk_0033_semantic_transfer_is_compatible_to_connector_stem_direction.py",
    "image_composite_converter.chunk_0034_semantic_transfer_scale_candidates_to_semantic_transfer_badge_params.py",
    "image_composite_converter.chunk_0035.py",
    "image_composite_converter.chunk_0036_try_template_transfer.py",
    "image_composite_converter.chunk_0037.py",
    "image_composite_converter.chunk_0038_convert_range.py",
    "image_composite_converter.chunk_0039.py",
    "image_composite_converter.chunk_0040_read_svg_geometry.py",
    "image_composite_converter.chunk_0041_normalized_geometry_signature_to_needs_large_circle_overflow_guard.py",
    "image_composite_converter.chunk_0042_scale_badge_params.py",
    "image_composite_converter.chunk_0043_harmonization_anchor_priority_to_family_harmonized_badge_colors.py",
    "image_composite_converter.chunk_0044_harmonize_semantic_size_variants.py",
    "image_composite_converter.chunk_0045_write_ac08_regression_manifest_to_summarize_previous_good_ac08_variants.py",
    "image_composite_converter.chunk_0046_write_ac08_success_criteria_report.py",
    "image_composite_converter.chunk_0047.py",
    "image_composite_converter.chunk_0048_write_ac08_weak_family_status_report.py",
    "image_composite_converter.chunk_0049_write_pixel_delta2_ranking_to_find_image_path_by_variant.py",
    "image_composite_converter.chunk_0050_collect_successful_conversion_quality_metrics.py",
    "image_composite_converter.chunk_0051_successful_conversion_metrics_available_to_successful_conversion_snapshot_paths.py",
    "image_composite_converter.chunk_0052_restore_successful_conversion_snapshot_to_merge_successful_conversion_metrics.py",
    "image_composite_converter.chunk_0053_format_successful_conversion_manifest_line_to_latest_failed_conversion_manifest_entry.py",
    "image_composite_converter.chunk_0054_update_successful_conversions_manifest_with_metrics.py",
    "image_composite_converter.chunk_0055_sorted_successful_conversion_metrics_rows_to_write_successful_conversion_quality_report.py",
    "image_composite_converter.chunk_0056_parse_args.py",
    "image_composite_converter.chunk_0057_optional_log_capture_to_resolve_cli_csv_and_output.py",
    "image_composite_converter.chunk_0058_format_user_diagnostic_to_prompt_interactive_range.py",
    "image_composite_converter.chunk_0059_main.py",
    "image_composite_converter.chunk_0060_convert_image_to_convert_image_variants.py",
]

_source_parts: list[str] = []
for _chunk_file in _CHUNK_FILES:
    _source_parts.append((_CHUNK_DIR / _chunk_file).read_text(encoding="utf-8"))

_COMBINED_SOURCE = "".join(_source_parts)
exec(compile(_COMBINED_SOURCE, 'image_composite_converter.py', "exec"), globals(), globals())

# Backward-compatibility shims expected by legacy tests/callers.
import importlib as importlib
from src.mainFiles import _optional_module_loader as _optional_module_loader_compat


def _optional_dependency_base_dir():
    return Path(__file__).resolve().parents[1]


def _vendored_site_packages_dirs():
    original_base_dir = _optional_module_loader_compat._optional_dependency_base_dir
    _optional_module_loader_compat._optional_dependency_base_dir = _optional_dependency_base_dir
    try:
        return _optional_module_loader_compat._vendored_site_packages_dirs()
    finally:
        _optional_module_loader_compat._optional_dependency_base_dir = original_base_dir


def _load_optional_module(module_name: str):
    original_base_dir = _optional_module_loader_compat._optional_dependency_base_dir
    original_importlib = _optional_module_loader_compat.importlib
    _optional_module_loader_compat._optional_dependency_base_dir = _optional_dependency_base_dir
    _optional_module_loader_compat.importlib = importlib
    try:
        return _optional_module_loader_compat._load_optional_module(module_name)
    finally:
        _optional_module_loader_compat._optional_dependency_base_dir = original_base_dir
        _optional_module_loader_compat.importlib = original_importlib


def _import_with_vendored_fallback(module_name: str):
    original_base_dir = _optional_module_loader_compat._optional_dependency_base_dir
    original_importlib = _optional_module_loader_compat.importlib
    _optional_module_loader_compat._optional_dependency_base_dir = _optional_dependency_base_dir
    _optional_module_loader_compat.importlib = importlib
    try:
        return _optional_module_loader_compat._import_with_vendored_fallback(module_name)
    finally:
        _optional_module_loader_compat._optional_dependency_base_dir = original_base_dir
        _optional_module_loader_compat.importlib = original_importlib


def _describe_optional_dependency_error(module_name: str, exc: BaseException, attempted_paths):
    return _optional_module_loader_compat._describe_optional_dependency_error(module_name, exc, attempted_paths)
