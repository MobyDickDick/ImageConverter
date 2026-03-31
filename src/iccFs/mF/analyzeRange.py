def analyzeRange(folder_path: str, output_root: str | None = None, start_ref: str = "", end_ref: str = "ZZZZZZ") -> str:
    return analyze_range_impl(
        folder_path=folder_path,
        output_root=output_root,
        start_ref=start_ref,
        end_ref=end_ref,
        default_output_root_fn=_defaultConvertedSymbolsRoot,
        in_requested_range_fn=_inRequestedRange,
        detect_regions_fn=detect_relevant_regions,
        annotate_regions_fn=annotate_image_regions,
        cv2_module=cv2,
        np_module=np,
    )
