from __future__ import annotations

from src.image_composite_converterFiles.mainFiles._sync_core_overridesFile import _sync_core_overrides


def main(argv: list[str] | None = None) -> int:
    import src.image_composite_converter as _m

    _sync_core_overrides()
    args = _m.parse_args(argv)
    if bool(getattr(args, "_render_svg_subprocess", False)):
        return _m._run_svg_render_subprocess_entrypoint()
    if bool(args.isolate_svg_render):
        _m.SVG_RENDER_SUBPROCESS_ENABLED = True
    _m.SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(1.0, float(args.isolate_svg_render_timeout_sec))
    log_path = str(args.log_file or "").strip()
    with _m._optional_log_capture(log_path):
        try:
            if args.ac08_regression_set:
                args.start = "AC0000"
                args.end = "ZZ9999"

            if args.print_linux_vendor_command:
                print(
                    " ".join(
                        _m.build_linux_vendor_install_command(
                            vendor_dir=args.vendor_dir,
                            platform_tag=args.vendor_platform,
                            python_version=args.vendor_python_version,
                        )
                    )
                )
                return 0

            if args.export_call_tree_csv:
                path = _m.export_module_call_tree_csv(output_csv_path=args.export_call_tree_csv)
                print(f"[INFO] Aufrufbaum-CSV geschrieben: {path}")
                return 0

            if args.interactive_range or args.start is None or args.end is None:
                args.start, args.end = _m._prompt_interactive_range(args)
            else:
                args.start = str(args.start or "").strip()
                args.end = str(args.end or "ZZZZZZ").strip() or args.start

            csv_path, output_dir = _m._resolve_cli_csv_and_output(args)

            if not csv_path:
                print("[WARN] Keine CSV/TSV/XML angegeben oder gefunden. Einige Symbole können ohne Beschreibung übersprungen werden.")
            elif not _m.os.path.exists(csv_path):
                print(f"[WARN] CSV/TSV/XML-Datei nicht gefunden: {csv_path}")
            elif args.mode == "convert":
                _m._load_description_mapping(csv_path)

            if args.bootstrap_deps:
                try:
                    installed = _m._bootstrap_required_image_dependencies()
                except RuntimeError as exc:
                    print(f"[ERROR] {exc}")
                    return 2
                if installed:
                    print(f"[INFO] Installiert: {', '.join(installed)}")

            if args.ac08_regression_set:
                print(
                    "[INFO] Verwende festes AC08-Regression-Set "
                    f"{_m.AC08_REGRESSION_SET_NAME}: {', '.join(_m.AC08_REGRESSION_VARIANTS)}"
                )
            selected_variants = set(_m.AC08_REGRESSION_VARIANTS) if args.ac08_regression_set else None

            if args.mode == "annotate":
                out_dir = _m.analyze_range(
                    args.folder_path,
                    output_root=output_dir,
                    start_ref=args.start,
                    end_ref=args.end,
                )
            else:
                out_dir = _m.convert_range(
                    args.folder_path,
                    csv_path,
                    args.iterations,
                    args.start,
                    args.end,
                    args.debug_ac0811_dir,
                    args.debug_element_diff_dir,
                    output_dir,
                    selected_variants,
                )
            print(f"\nAbgeschlossen! Ausgaben unter: {out_dir}")
            return 0
        except _m.DescriptionMappingError as exc:
            print(f"[ERROR] {_m._format_user_diagnostic(exc)}")
            return 2
