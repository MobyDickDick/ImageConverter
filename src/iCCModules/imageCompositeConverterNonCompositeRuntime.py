from __future__ import annotations

import os
import re
from pathlib import Path


def _build_vector_placeholder_svg(width: int, height: int, *, description: str = "") -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    desc = (description or "Automatisch erzeugte Platzhalter-Vektorgrafik").strip()
    escaped_desc = (
        desc.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <desc>{escaped_desc}</desc>\n'
        '  <defs>\n'
        '    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">\n'
        '      <stop offset="0%" stop-color="#6d6d6d"/>\n'
        '      <stop offset="50%" stop-color="#d7d7d7"/>\n'
        '      <stop offset="100%" stop-color="#6d6d6d"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        f'  <rect x="0" y="0" width="{safe_w}" height="{safe_h}" fill="url(#bg)"/>\n'
        f'  <line x1="0" y1="0" x2="{safe_w}" y2="{safe_h}" stroke="#8e8e8e" stroke-width="1"/>\n'
        f'  <line x1="{safe_w}" y1="0" x2="0" y2="{safe_h}" stroke="#8e8e8e" stroke-width="1"/>\n'
        f'  <rect x="{max(1, safe_w//4)}" y="{max(1, safe_h//10)}" width="{max(2, safe_w//2)}" height="{max(2, safe_h//8)}" fill="#4a4a4a" rx="1"/>\n'
        f'  <line x1="{max(2, safe_w//2 - safe_w//8)}" y1="{max(2, safe_h//6)}" x2="{max(3, safe_w//2 - safe_w//20)}" y2="{max(2, safe_h//6)}" stroke="#f2f2f2" stroke-width="1"/>\n'
        f'  <line x1="{max(2, safe_w//2 + safe_w//20)}" y1="{max(2, safe_h//6)}" x2="{max(3, safe_w//2 + safe_w//8)}" y2="{max(2, safe_h//6)}" stroke="#f2f2f2" stroke-width="1"/>\n'
        '</svg>\n'
    )



def _description_requests_diagonal_band(description: str) -> bool:
    text = (description or "").lower()
    return "diagon" in text and "links unten" in text and "rechts oben" in text


def _build_diagonal_band_svg(width: int, height: int, *, stroke_width: float, description: str = "") -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    margin = 0.5
    x1, y1 = margin, safe_h - margin
    x2, y2 = safe_w - margin, margin
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        '  <defs>\n'
        '    <linearGradient id="bg" x1="100%" y1="0%" x2="0%" y2="0%">\n'
        '      <stop offset="0%" stop-color="#b4b4b4"/>\n'
        '      <stop offset="30%" stop-color="#fbfbfb"/>\n'
        '      <stop offset="37%" stop-color="#fbfbfb"/>\n'
        '      <stop offset="100%" stop-color="#b4b4b4"/>\n'
        '    </linearGradient>\n'
        f'    <clipPath id="innerRect"><rect x="{margin}" y="{margin}" width="{safe_w-1}" height="{safe_h-1}"/></clipPath>\n'
        '  </defs>\n'
        f'  <rect x="{margin}" y="{margin}" width="{safe_w-1}" height="{safe_h-1}" fill="url(#bg)" stroke="#adadad" stroke-width="1"/>\n'
        f'  <path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="#8f8f8f" stroke-width="{stroke_width:.3f}" stroke-linecap="butt" clip-path="url(#innerRect)"/>\n'
        '</svg>\n'
    )


def _fit_diagonal_band_iterative(*, width: int, height: int, description: str, perc_img, render_svg_to_numpy_fn, calculate_error_fn):
    ratios = (0.08, 0.11, 0.14, 0.17, 0.20, 0.23, 0.26)
    scale = max(2.0, min(width, height))
    best = None
    for ratio in ratios:
        stroke_w = max(1.0, scale * ratio)
        svg = _build_diagonal_band_svg(width, height, stroke_width=stroke_w, description=description)
        rendered = render_svg_to_numpy_fn(svg, width, height)
        if rendered is None:
            continue
        err = calculate_error_fn(perc_img, rendered)
        if best is None or err < best[0]:
            best = (err, svg, rendered, stroke_w)
    return best

def _contains_svg_image_tag(svg_content: str) -> bool:
    lowered = svg_content.lower()
    return "<image" in lowered and ('href="data:image' in lowered or 'xlink:href="data:image' in lowered)


def _build_sample_candidates(base_name: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            candidates.append(name)

    _add(base_name)
    root, sep, size_suffix = base_name.rpartition("_")
    if sep:
        _add(root)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{root}_{alt_suffix}")
    else:
        for alt_suffix in ("L", "M", "S"):
            _add(f"{base_name}_{alt_suffix}")

    family_name = root if sep else base_name

    if family_name.startswith("AC") and len(family_name) > 2:
        se_alias = f"SE{family_name[2:]}"
        _add(se_alias)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{se_alias}_{alt_suffix}")
    if family_name.startswith("SE") and len(family_name) > 2:
        ac_alias = f"AC{family_name[2:]}"
        _add(ac_alias)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{ac_alias}_{alt_suffix}")

    return candidates


def _extract_reference_family_from_description(description: str) -> str | None:
    text = (description or "").strip()
    if not text:
        return None
    match = re.search(r"\bwie\s+((?:AC|SE)\d{4})\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).upper()


def _prepend_reference_candidates(candidates: list[str], reference_family: str) -> list[str]:
    preferred: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            preferred.append(name)

    _add(reference_family)
    for size in ("L", "M", "S"):
        _add(f"{reference_family}_{size}")

    for existing in candidates:
        _add(existing)
    return preferred


def _is_inkscape_svg(svg_content: str) -> bool:
    lowered = svg_content.lower()
    return "inkscape:" in lowered or "sodipodi:" in lowered or "created with inkscape" in lowered


def _sanitize_sample_svg(svg_content: str) -> str:
    # Remove editor-specific metadata that can break strict SVG parsers when
    # namespace declarations are missing in curated sample assets.
    sanitized = re.sub(r"<\/?(?:sodipodi|inkscape):[^>]*?>", "", svg_content, flags=re.IGNORECASE)
    sanitized = re.sub(r"\sxmlns:(?:inkscape|sodipodi)=\"[^\"]*\"", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\sxmlns:(?:inkscape|sodipodi)='[^']*'", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s(?:sodipodi|inkscape):[\w.-]+=\"[^\"]*\"", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s(?:sodipodi|inkscape):[\w.-]+='[^']*'", "", sanitized, flags=re.IGNORECASE)
    return sanitized


def _try_load_sample_svg(*, img_path: str, base_name: str, description: str = ""):
    local_samples_dir = os.path.join(os.path.dirname(img_path), "samples")
    fallback_dirs: list[str] = [local_samples_dir]
    env_dirs = os.environ.get("IMAGE_CONVERTER_SAMPLE_SVG_DIRS", "")
    for raw in env_dirs.split(os.pathsep):
        candidate = raw.strip()
        if candidate:
            fallback_dirs.append(candidate)
    repo_default = Path(__file__).resolve().parents[2] / "artifacts" / "images_to_convert" / "samples"
    fallback_dirs.append(str(repo_default))

    # de-duplicate and keep existing dirs only
    samples_dirs: list[str] = []
    seen_dirs: set[str] = set()
    for raw_dir in fallback_dirs:
        normalized = os.path.abspath(raw_dir)
        if normalized in seen_dirs or not os.path.isdir(normalized):
            continue
        seen_dirs.add(normalized)
        samples_dirs.append(normalized)

    sample_candidates = _build_sample_candidates(base_name)
    reference_family = _extract_reference_family_from_description(description)
    if reference_family and reference_family != base_name.upper():
        sample_candidates = _prepend_reference_candidates(sample_candidates, reference_family)
    for samples_dir in samples_dirs:
        for sample_name in sample_candidates:
            sample_svg_path = os.path.join(samples_dir, f"{sample_name}.svg")
            if not os.path.exists(sample_svg_path):
                continue
            with open(sample_svg_path, "r", encoding="utf-8") as handle:
                original_svg = handle.read()
            sanitized_svg = _sanitize_sample_svg(original_svg)
            if _is_inkscape_svg(original_svg) and sanitized_svg != original_svg:
                Path(sample_svg_path).write_text(sanitized_svg, encoding="utf-8")
            return sample_svg_path, sanitized_svg
    return None


def runNonCompositeIterationImpl(
    *,
    mode: str,
    params: dict[str, object],
    stripe_strategy: dict[str, object] | None,
    semantic_mode_visual_override: bool,
    width: int,
    height: int,
    base_name: str,
    description: str,
    perc_img,
    img_path: str,
    print_fn,
    render_embedded_raster_svg_fn,
    build_gradient_stripe_svg_fn,
    build_gradient_stripe_validation_log_lines_fn,
    write_validation_log_fn,
    render_svg_to_numpy_fn,
    record_render_failure_fn,
    write_attempt_artifacts_fn,
    calculate_error_fn,
) -> tuple[str, str, dict[str, object], int, float] | None:
    sample_svg = _try_load_sample_svg(img_path=img_path, base_name=base_name, description=description)

    if mode == "manual_review":
        generated_svg_content = None
        generated_rendered = None
        generated_err = float("inf")
        generated_status = "manual_review_generated_vector_placeholder"

        if _description_requests_diagonal_band(description):
            print_fn("  -> Plan B Grundsatz: Diagonalbreite wird iterativ bestimmt (kein Fixwert).")
            best_diagonal = _fit_diagonal_band_iterative(
                width=width,
                height=height,
                description=description,
                perc_img=perc_img,
                render_svg_to_numpy_fn=render_svg_to_numpy_fn,
                calculate_error_fn=calculate_error_fn,
            )
            if best_diagonal is not None:
                generated_err, generated_svg_content, generated_rendered, stroke_w = best_diagonal
                generated_status = "manual_review_iterative_diagonal_band"
                generated_log_lines = [
                    "status=manual_review_iterative_diagonal_band",
                    f"iterative_stroke_width={stroke_w:.6f}",
                ]
            else:
                generated_log_lines = ["status=manual_review_iterative_diagonal_band_render_failed"]
        elif stripe_strategy:
            print_fn("  -> Plan B aktiv: nutze erkannte Gradient-Stripe-Strategie trotz Manual-Review.")
            generated_svg_content = build_gradient_stripe_svg_fn(width, height, stripe_strategy)
            strategy_stop_count = len(list(stripe_strategy.get("stops", [])))
            generated_rendered = render_svg_to_numpy_fn(generated_svg_content, width, height)
            if generated_rendered is None:
                record_render_failure_fn(
                    "manual_review_gradient_stripe_render_failed",
                    svg_content=generated_svg_content,
                    params_snapshot=params,
                )
            else:
                generated_err = calculate_error_fn(perc_img, generated_rendered)
                generated_status = "manual_review_gradient_stripe"
                generated_log_lines = build_gradient_stripe_validation_log_lines_fn(
                    semantic_mode_visual_override=semantic_mode_visual_override,
                    strategy_stop_count=strategy_stop_count,
                )
        else:
            generated_svg_content = _build_vector_placeholder_svg(width, height, description=description)
            generated_rendered = render_svg_to_numpy_fn(generated_svg_content, width, height)
            if generated_rendered is None:
                record_render_failure_fn(
                    "manual_review_vector_placeholder_render_failed",
                    svg_content=generated_svg_content,
                    params_snapshot=params,
                )
            else:
                generated_err = calculate_error_fn(perc_img, generated_rendered)
            generated_log_lines = ["status=manual_review_generated_vector_placeholder"]

        if sample_svg:
            sample_svg_path, sample_svg_content = sample_svg
            sample_rendered = render_svg_to_numpy_fn(sample_svg_content, width, height)
            if sample_rendered is None:
                record_render_failure_fn(
                    "manual_review_plan_b_render_failed",
                    svg_content=sample_svg_content,
                    params_snapshot=params,
                )
            else:
                sample_err = calculate_error_fn(perc_img, sample_rendered)
                if sample_err + 1e-6 < generated_err:
                    print_fn(
                        "  -> Plan B Vergleich aktiv: verwende vorhandene Sample-SVG "
                        f"{sample_svg_path} (sample={sample_err:.3f}, generated={generated_err:.3f})."
                    )
                    write_validation_log_fn(
                        [
                            "status=manual_review_plan_b_sample_svg",
                            f"sample_svg_path={sample_svg_path}",
                            f"sample_error={sample_err:.6f}",
                            f"generated_error={generated_err:.6f}",
                            f"generated_status={generated_status}",
                        ]
                    )
                    write_attempt_artifacts_fn(sample_svg_content, sample_rendered)
                    return base_name, description, params, 1, sample_err

        if generated_rendered is not None and generated_svg_content is not None:
            print_fn(
                "  -> Plan B Vergleich aktiv: verwende generierte Vektor-Lösung "
                f"(status={generated_status}, err={generated_err:.3f})."
            )
            write_validation_log_fn(generated_log_lines)
            write_attempt_artifacts_fn(generated_svg_content, generated_rendered)
            return base_name, description, params, 1, generated_err

        reason = str(params.get("review_reason", "Manuelle Prüfung erforderlich.")).strip()
        print_fn(f"  -> Überspringe Bild: {reason}")
        write_validation_log_fn(
            [
                "status=skipped_manual_review",
                f"manual_review_reason={reason}",
            ]
        )
        return None

    if stripe_strategy:
        print_fn("  -> Fallback aktiv: verwende Gradient-Stripe-Strategie.")
        svg_content = build_gradient_stripe_svg_fn(width, height, stripe_strategy)
        strategy_stop_count = len(list(stripe_strategy.get("stops", [])))
        write_validation_log_fn(
            build_gradient_stripe_validation_log_lines_fn(
                semantic_mode_visual_override=semantic_mode_visual_override,
                strategy_stop_count=strategy_stop_count,
            )
        )
    else:
        print_fn("  -> Fallback aktiv: verwende reine SVG-Platzhalter-Konvertierung (kein eingebettetes Raster).")
        svg_content = _build_vector_placeholder_svg(width, height, description=description)
        write_validation_log_fn(["status=non_composite_pure_svg_placeholder_vector"])

    svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
    if svg_rendered is None:
        record_render_failure_fn(
            "non_composite_pure_svg_render_failed",
            svg_content=svg_content,
            params_snapshot=params,
        )
        return None

    svg_err = calculate_error_fn(perc_img, svg_rendered)

    if sample_svg:
        sample_svg_path, sample_svg_content = sample_svg
        sample_rendered = render_svg_to_numpy_fn(sample_svg_content, width, height)
        if sample_rendered is not None:
            sample_err = calculate_error_fn(perc_img, sample_rendered)
            baseline_is_embedded_raster = _contains_svg_image_tag(svg_content)
            # Favor curated sample SVGs over generated placeholders when they are
            # in a similar quality range, because sample assets usually carry
            # richer semantic structure than our generic non-composite fallback.
            sample_preference_factor = 1.08 if baseline_is_embedded_raster else 1.25
            sample_improvement_ratio = (svg_err / sample_err) if sample_err > 0 else float("inf")
            prefer_sample_svg = baseline_is_embedded_raster or sample_improvement_ratio >= sample_preference_factor
            if prefer_sample_svg:
                decision_note = ""
                if baseline_is_embedded_raster and sample_err > svg_err:
                    decision_note = " (Vector-Sample gegenüber Embedded-Raster bevorzugt)"
                print_fn(
                    "  -> Plan B Vergleich aktiv: nutze Sample-SVG "
                    f"{sample_svg_path} (err={sample_err:.3f}, baseline={svg_err:.3f})."
                    f"{decision_note}"
                )
                write_validation_log_fn(
                    [
                        "status=non_composite_plan_b_sample_svg_selected",
                        f"sample_svg_path={sample_svg_path}",
                        f"sample_error={sample_err:.6f}",
                        f"baseline_error={svg_err:.6f}",
                        f"baseline_is_embedded_raster={int(baseline_is_embedded_raster)}",
                        f"sample_preference_factor={sample_preference_factor:.2f}",
                        f"sample_improvement_ratio={sample_improvement_ratio:.6f}",
                    ]
                )
                write_attempt_artifacts_fn(sample_svg_content, sample_rendered)
                return base_name, description, params, 1, sample_err
        else:
            if _contains_svg_image_tag(svg_content):
                print_fn(
                    "  -> Plan B Vergleich aktiv: nutze Sample-SVG "
                    f"{sample_svg_path} trotz fehlendem Raster-Render (Embedded-Raster vermeiden)."
                )
                write_validation_log_fn(
                    [
                        "status=non_composite_plan_b_sample_svg_selected",
                        f"sample_svg_path={sample_svg_path}",
                        "sample_render_failed=1",
                        f"baseline_error={svg_err:.6f}",
                        "baseline_is_embedded_raster=1",
                        "sample_preference_factor=forced",
                    ]
                )
                write_attempt_artifacts_fn(sample_svg_content, None)
                return base_name, description, params, 1, svg_err

    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, svg_err
