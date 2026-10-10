from __future__ import annotations

import os


_VALID_IMAGE_EXTENSIONS = (".bmp", ".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".webp")


def normalizeSelectedVariantsImpl(selected_variants: set[str] | None) -> set[str]:
    return {str(variant).upper() for variant in (selected_variants or set()) if str(variant).strip()}


def listRequestedImageFilesImpl(
    folder_path: str,
    start_ref: str,
    end_ref: str,
    *,
    selected_variants: set[str] | None,
    in_requested_range_fn,
) -> tuple[set[str], list[str]]:
    normalized_selected_variants = normalizeSelectedVariantsImpl(selected_variants)
    files = sorted(
        filename
        for filename in os.listdir(folder_path)
        if filename.lower().endswith(_VALID_IMAGE_EXTENSIONS)
        and in_requested_range_fn(filename, start_ref, end_ref)
        and (
            not normalized_selected_variants
            or os.path.splitext(filename)[0].upper() in normalized_selected_variants
        )
    )
    # Explicit regression selections must keep archived successes in scope.
    # Ordinary batches process only the remaining intake files.
    archive_name = "succesessfulConvertedImages"
    archive_path = os.path.join(folder_path, archive_name)
    if normalized_selected_variants and os.path.isdir(archive_path):
        present = {os.path.splitext(os.path.basename(name))[0].upper() for name in files}
        for filename in sorted(os.listdir(archive_path)):
            variant = os.path.splitext(filename)[0].upper()
            if (filename.lower().endswith(_VALID_IMAGE_EXTENSIONS)
                    and variant in normalized_selected_variants and variant not in present
                    and in_requested_range_fn(filename, start_ref, end_ref)):
                files.append(os.path.join(archive_name,filename))
                present.add(variant)
    return normalized_selected_variants, files


def inputSelectionSummaryImpl(
    *,
    folder_path: str,
    start_ref: str,
    end_ref: str,
    selected_variants: set[str],
    matched_files: list[str],
) -> str:
    selected_list = sorted(str(variant).upper() for variant in selected_variants if str(variant).strip())
    lines = [
        "Keine Eingabedateien für die Konvertierung gefunden.",
        f"Ordner: {folder_path}",
        f"Range: {start_ref}..{end_ref}",
        f"Anzahl gefundener Dateien: {len(matched_files)}",
        "Unterstützte Endungen: " + ", ".join(_VALID_IMAGE_EXTENSIONS),
    ]
    if selected_list:
        lines.append("Ausgewählte Varianten: " + ", ".join(selected_list))
    else:
        lines.append("Ausgewählte Varianten: <keine Vorgabe>")
    lines.append("Hinweis: Prüfe Range, Dateiendung und Variantennamen.")
    return "\n".join(lines) + "\n"
