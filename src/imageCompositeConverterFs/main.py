from __future__ import annotations

from src.imageCompositeConverterFs.syncCoreOverrides import syncCoreOverrides


def main(argv: list[str] | None = None) -> int:
    import src.image_composite_converter as module

    syncCoreOverrides()
    args = module.parse_args(argv)
    if bool(getattr(args, "_render_svg_subprocess", False)):
        return module._run_svg_render_subprocess_entrypoint()
    if bool(args.isolate_svg_render):
        module.SVG_RENDER_SUBPROCESS_ENABLED = True
    module.SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(1.0, float(args.isolate_svg_render_timeout_sec))
    logPath = str(args.log_file or "").strip()
    with module._optional_log_capture(logPath):
        try:
            if args.ac08_regression_set:
                args.start = "AC0000"
                args.end = "ZZ9999"

            if args.print_linux_vendor_command:
                print(
                    " ".join(
                        module.build_linux_vendor_install_command(
                            vendor_dir=args.vendor_dir,
                            platform_tag=args.vendor_platform,
                            python_version=args.vendor_python_version,
                        )
                    )
                )
                return 0

            if args.export_call_tree_csv:
                path = module.export_module_call_tree_csv(output_csv_path=args.export_call_tree_csv)
                print(f"[INFO] Aufrufbaum-CSV geschrieben: {path}")
                return 0

            if args.interactive_range or args.start is None or args.end is None:
                args.start, args.end = module._prompt_interactive_range(args)
            else:
                args.start = str(args.start or "").strip()
                args.end = str(args.end or "ZZZZZZ").strip() or args.start

            csvPath, outputDir = module._resolve_cli_csv_and_output(args)

            if not csvPath:
                print("[WARN] Keine CSV/TSV/XML angegeben oder gefunden. Einige Symbole können ohne Beschreibung übersprungen werden.")
            elif not module.os.path.exists(csvPath):
                print(f"[WARN] CSV/TSV/XML-Datei nicht gefunden: {csvPath}")
            elif args.mode == "convert":
                module._load_description_mapping(csvPath)

            if args.bootstrap_deps:
                try:
                    installed = module._bootstrap_required_image_dependencies()
                except RuntimeError as exc:
                    print(f"[ERROR] {exc}")
                    return 2
                if installed:
                    print(f"[INFO] Installiert: {', '.join(installed)}")

            if args.ac08_regression_set:
                print(
                    "[INFO] Verwende festes AC08-Regression-Set "
                    f"{module.AC08_REGRESSION_SET_NAME}: {', '.join(module.AC08_REGRESSION_VARIANTS)}"
                )
            selectedVariants = set(module.AC08_REGRESSION_VARIANTS) if args.ac08_regression_set else None

            if args.mode == "annotate":
                outDir = module.analyze_range(
                    args.folder_path,
                    output_root=outputDir,
                    start_ref=args.start,
                    end_ref=args.end,
                )
            else:
                outDir = module.convert_range(
                    args.folder_path,
                    csvPath,
                    args.iterations,
                    args.start,
                    args.end,
                    args.debug_ac0811_dir,
                    args.debug_element_diff_dir,
                    outputDir,
                    selectedVariants,
                )
            print(f"\nAbgeschlossen! Ausgaben unter: {outDir}")
            return 0
        except module.DescriptionMappingError as exc:
            print(f"[ERROR] {module._format_user_diagnostic(exc)}")
            return 2
