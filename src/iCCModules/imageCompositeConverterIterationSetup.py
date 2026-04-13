from __future__ import annotations

import os


def ensureIterationOutputDirsImpl(
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str | None,
    *,
    makedirs_fn=os.makedirs,
) -> None:
    makedirs_fn(svg_out_dir, exist_ok=True)
    makedirs_fn(diff_out_dir, exist_ok=True)
    if reports_out_dir:
        makedirs_fn(reports_out_dir, exist_ok=True)


def buildIterationBaseAndLogPathImpl(
    filename: str,
    reports_out_dir: str | None,
    *,
    splitext_fn=os.path.splitext,
    join_fn=os.path.join,
) -> tuple[str, str | None]:
    base = splitext_fn(filename)[0]
    log_path = None
    if reports_out_dir:
        log_path = join_fn(reports_out_dir, f"{base}_element_validation.log")
    return base, log_path


def emitIterationDescriptionHeaderImpl(
    *,
    filename: str,
    params: dict[str, object],
    print_fn=print,
) -> None:
    print_fn(f"\n--- Verarbeite {filename} ---")
    description_fragments = params.get("description_fragments", [])
    description_text = " ".join(
        str(fragment.get("text", "")).strip()
        for fragment in description_fragments
        if isinstance(fragment, dict)
    ).strip()
    if description_text:
        print_fn(f"Bildbeschreibung: {description_text}")
    elements = ", ".join(params.get("elements", [])) if params.get("elements") else "Kein Compositing-Befehl gefunden"
    print_fn(f"Befehl erkannt: {elements}")
