"""Auto-generated loader for split module chunks.

DO NOT EDIT MANUALLY. Re-run tools/split_python_module.py instead.
"""

from __future__ import annotations

from pathlib import Path
import contextlib

_BASE_DIR = Path(__file__).resolve().parent
_CHUNK_DIR = _BASE_DIR / 'image_composite_converter_parts'
_SOURCE_FILE = _BASE_DIR / "image_composite_converter.py.pre_split.bak"

_CHUNK_FILES = [
    "image_composite_converter.chunk_0001_detect_relevant_regions_to_annotate_image_regions.py",
    "image_composite_converter.chunk_0002_analyze_range_to_clip.py",
    "image_composite_converter.chunk_0003_abstand_to_build_oriented_kelle.py",
    "image_composite_converter.chunk_0004_load_grayscale_image.py",
    "image_composite_converter.chunk_0005_create_diff_image_without_cv2_to_load_binary_image_with_mode.py",
    "image_composite_converter.chunk_0006_render_candidate_mask_to_candidate_to_svg.py",
    "image_composite_converter.chunk_0007_decompose_circle_with_stem.py",
    "image_composite_converter.chunk_0008_missing_required_image_dependencies_to_dotted_attr_name.py",
    "image_composite_converter.chunk_0009_module_call_edges_for_path.py",
    "image_composite_converter.chunk_0010_export_module_call_tree_csv_to_load_description_mapping.py",
    "image_composite_converter.chunk_0011_load_description_mapping_from_csv.py",
    "image_composite_converter.chunk_0012_load_description_mapping_from_xml_to_required_vendor_packages.py",
    "image_composite_converter.chunk_0013_build_linux_vendor_install_command.py",
    "image_composite_converter.chunk_0014.py",
    "image_composite_converter.chunk_0015_render_svg_to_numpy_inprocess_to_run_svg_render_subprocess_entrypoint.py",
    "image_composite_converter.chunk_0016.py",
    "image_composite_converter.chunk_0017_semantic_quality_flags.py",
    "image_composite_converter.chunk_0018_run_iteration_pipeline.py",
    "image_composite_converter.chunk_0019_extract_ref_parts_to_matches_exact_prefix_filter.py",
    "image_composite_converter.chunk_0020_in_requested_range_to_write_batch_failure_summary.py",
    "image_composite_converter.chunk_0021_collect_description_fragments_to_reports_output_dir.py",
    "image_composite_converter.chunk_0022_is_semantic_template_variant_to_load_existing_conversion_rows.py",
    "image_composite_converter.chunk_0023_sniff_raster_size_to_write_quality_config.py",
    "image_composite_converter.chunk_0024_quality_sort_key_to_adaptive_iteration_budget_for_quality_row.py",
    "image_composite_converter.chunk_0025_write_quality_pass_report_to_build_transformed_svg_from_template.py",
    "image_composite_converter.chunk_0026_template_transfer_scale_candidates_to_template_transfer_transform_candidates.py",
    "image_composite_converter.chunk_0027_rank_template_transfer_donors_to_semantic_transfer_is_compatible.py",
    "image_composite_converter.chunk_0028_connector_arm_direction_to_semantic_transfer_scale_candidates.py",
    "image_composite_converter.chunk_0029_semantic_transfer_badge_params.py",
    "image_composite_converter.chunk_0030_try_template_transfer.py",
    "image_composite_converter.chunk_0031.py",
    "image_composite_converter.chunk_0032_convert_range.py",
    "image_composite_converter.chunk_0033.py",
    "image_composite_converter.chunk_0034_read_svg_geometry.py",
    "image_composite_converter.chunk_0035_normalized_geometry_signature_to_needs_large_circle_overflow_guard.py",
    "image_composite_converter.chunk_0036_scale_badge_params_to_clip_gray.py",
    "image_composite_converter.chunk_0037_family_harmonized_badge_colors.py",
    "image_composite_converter.chunk_0038_harmonize_semantic_size_variants.py",
    "image_composite_converter.chunk_0039_write_ac08_regression_manifest_to_summarize_previous_good_ac08_variants.py",
    "image_composite_converter.chunk_0040_write_ac08_success_criteria_report.py",
    "image_composite_converter.chunk_0041.py",
    "image_composite_converter.chunk_0042_write_ac08_weak_family_status_report.py",
    "image_composite_converter.chunk_0043_write_pixel_delta2_ranking_to_find_image_path_by_variant.py",
    "image_composite_converter.chunk_0044_collect_successful_conversion_quality_metrics_to_successful_conversion_metrics_available.py",
    "image_composite_converter.chunk_0045_parse_successful_conversion_manifest_line_to_is_successful_conversion_candidate_better.py",
    "image_composite_converter.chunk_0046_merge_successful_conversion_metrics_to_latest_failed_conversion_manifest_entry.py",
    "image_composite_converter.chunk_0047_update_successful_conversions_manifest_with_metrics_to_sorted_successful_conversion_metrics_rows.py",
    "image_composite_converter.chunk_0048_write_successful_conversion_csv_table_to_write_successful_conversion_quality_report.py",
    "image_composite_converter.chunk_0049_parse_args.py",
    "image_composite_converter.chunk_0050_optional_log_capture_to_prompt_interactive_range.py",
    "image_composite_converter.chunk_0051_main_to_convert_image.py",
    "image_composite_converter.chunk_0052_convert_image_variants.py",
]

_source_parts: list[str] = []
for _chunk_file in _CHUNK_FILES:
    _source_parts.append((_CHUNK_DIR / _chunk_file).read_text(encoding="utf-8"))

_COMBINED_SOURCE = "".join(_source_parts)
exec(compile(_COMBINED_SOURCE, 'image_composite_converter.py', "exec"), globals(), globals())

# Keep source-introspection helpers/tests pointed at the original monolith source.
if _SOURCE_FILE.exists():
    globals()["__file__"] = str(_SOURCE_FILE)
