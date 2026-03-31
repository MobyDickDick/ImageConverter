def _resolveCliCsvAndOutput(args: argparse.Namespace) -> tuple[str, str | None]:
    """Resolve effective table path and output directory from mixed CLI styles."""
    csv_path = args.csv_path
    output_dir = args.output_dir
    if args.csv_or_output:
        c = str(args.csv_or_output)
        looks_like_csv = c.lower().endswith(".csv") or c.lower().endswith(".tsv") or c.lower().endswith(".xml")
        if csv_path is None and looks_like_csv:
            csv_path = c
        elif output_dir is None and not looks_like_csv:
            output_dir = c
        elif csv_path is None:
            csv_path = c

    if csv_path is None:
        csv_path = _autoDetectCsvPath(args.folder_path) or ""
    elif str(csv_path).lower().endswith(".xml"):
        csv_path = _resolveDescriptionXmlPath(csv_path) or csv_path

    return csv_path, output_dir
