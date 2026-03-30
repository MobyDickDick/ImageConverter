"""Description mapping helpers extracted from :mod:`src.image_composite_converter`."""

from __future__ import annotations

import csv
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable


def load_description_mapping(
    path: str,
    *,
    description_mapping_error_cls: type[Exception],
    source_span_cls: type,
    get_base_name_from_file: Callable[[str], str],
) -> dict[str, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        return load_description_mapping_from_xml(
            path,
            description_mapping_error_cls=description_mapping_error_cls,
            source_span_cls=source_span_cls,
            get_base_name_from_file=get_base_name_from_file,
        )
    return load_description_mapping_from_csv(
        path,
        description_mapping_error_cls=description_mapping_error_cls,
        source_span_cls=source_span_cls,
    )


def load_description_mapping_from_csv(
    path: str,
    *,
    description_mapping_error_cls: type[Exception],
    source_span_cls: type,
) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    if not os.path.exists(path):
        return raw_desc

    with open(path, mode="r", encoding="utf-8-sig") as f:
        content = f.read()
        delimiter = ";" if ";" in content.split("\n", 1)[0] else ","
        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader, None)
        if not headers:
            return raw_desc

        root_idx, desc_idx = -1, -1
        for i, h in enumerate(headers):
            low = h.lower()
            if "wurzelform" in low:
                root_idx = i
            elif "beschreibung" in low:
                desc_idx = i
        if root_idx == -1:
            root_idx = 1
        if desc_idx == -1:
            desc_idx = 2

        for row_number, row in enumerate(reader, start=2):
            if len(row) > max(root_idx, desc_idx):
                root_name = row[root_idx].strip()
                desc = row[desc_idx].strip()
                if root_name:
                    raw_desc[root_name] = desc
                continue

            expected_columns = max(root_idx, desc_idx) + 1
            raise description_mapping_error_cls(
                (
                    "Description table row is missing expected columns "
                    f"(expected at least {expected_columns}, got {len(row)})."
                ),
                span=source_span_cls(path=path, line=row_number, column=1),
            )
    return raw_desc


def load_description_mapping_from_xml(
    path: str,
    *,
    description_mapping_error_cls: type[Exception],
    source_span_cls: type,
    get_base_name_from_file: Callable[[str], str],
) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    resolved_path = resolve_description_xml_path(path)
    if resolved_path is None:
        return raw_desc

    try:
        tree = ET.parse(resolved_path)
    except ET.ParseError as exc:
        raise description_mapping_error_cls(
            "Description XML could not be parsed.",
            span=source_span_cls(path=resolved_path, line=exc.position[0], column=exc.position[1] + 1),
        ) from exc

    root = tree.getroot()

    def _register_description(key: str, description: str) -> None:
        normalized_desc = str(description or "").strip()
        if not normalized_desc:
            return

        normalized_key = str(key or "").strip()
        stem = get_base_name_from_file(normalized_key)
        plain_stem = os.path.splitext(normalized_key)[0]
        for candidate in {
            normalized_key,
            normalized_key.upper(),
            normalized_key.lower(),
            stem,
            stem.upper(),
            stem.lower(),
            plain_stem,
            plain_stem.upper(),
            plain_stem.lower(),
        }:
            if candidate:
                raw_desc[candidate] = normalized_desc

    def _merge_entry_and_image_desc(entry_desc: str, image_desc: str) -> str:
        e = entry_desc.strip()
        i = image_desc.strip()
        if e and i and e != i:
            return f"{e} {i}".strip()
        return i or e

    def _extract_image_specific_description(entry: ET.Element, image_name: str) -> str:
        image_name = str(image_name or "").strip()
        if not image_name:
            return ""

        for image_tag in entry.findall("./bilder/bild"):
            tag_name = (image_tag.text or "").strip()
            if tag_name == image_name:
                attr_desc = (image_tag.attrib.get("beschreibung") or "").strip()
                if attr_desc:
                    return attr_desc
                child_desc = (image_tag.findtext("beschreibung") or "").strip()
                if child_desc:
                    return child_desc

        for detail_tag in entry.findall("./bildbeschreibungen/bildbeschreibung"):
            detail_name = (detail_tag.attrib.get("bild") or detail_tag.attrib.get("image") or "").strip()
            if detail_name and detail_name == image_name:
                text_desc = ("".join(detail_tag.itertext()) or "").strip()
                if text_desc:
                    return re.sub(r"\s+", " ", text_desc).strip()
        return ""

    for entry in root.findall(".//entry"):
        desc = (entry.findtext("beschreibung") or "").strip()
        root_form = (entry.findtext("wurzelform") or "").strip()
        key = str(entry.attrib.get("key", "")).strip()

        if root_form and desc:
            _register_description(root_form, desc)
        if key and desc:
            _register_description(key, desc)

        for image_tag in entry.findall("./bilder/bild"):
            image_name = (image_tag.text or "").strip()
            image_stem = os.path.splitext(image_name)[0].strip()
            image_specific_desc = _extract_image_specific_description(entry, image_name)
            merged_desc = _merge_entry_and_image_desc(desc, image_specific_desc)
            if merged_desc:
                _register_description(image_name, merged_desc)
                _register_description(image_stem, merged_desc)

    return raw_desc


def resolve_description_xml_path(path: str) -> str | None:
    candidate = Path(path)
    if candidate.exists():
        return str(candidate)

    basename = candidate.name
    if not basename:
        return None

    fallback_candidates = [
        Path("artifacts/descriptions") / basename,
        Path("artifacts/images_to_convert") / basename,
    ]
    for fallback in fallback_candidates:
        if fallback.exists():
            return str(fallback)
    return None
