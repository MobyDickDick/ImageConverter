def analyze_range(folder_path: str, output_root: str | None = None, start_ref: str = "", end_ref: str = "ZZZZZZ") -> str:
    return analyzeRangeImpl(
        folder_path=folder_path,
        output_root=output_root,
        start_ref=start_ref,
        end_ref=end_ref,
        default_output_root_fn=_default_converted_symbols_root,
        in_requested_range_fn=_in_requested_range,
        detect_regions_fn=detect_relevant_regions,
        annotate_regions_fn=annotate_image_regions,
        cv2_module=cv2,
        np_module=np,
    )
