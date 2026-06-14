"""Canonicalization helpers for filename-invariance regression checks."""

from __future__ import annotations

import copy
import json
from typing import Any
from xml.etree import ElementTree


_IGNORED_IR_KEYS = {
    "created_at",
    "output_name",
    "source_file",
    "source_name",
    "timestamp",
    "variant_name",
}
_IGNORED_SVG_ATTRIBUTES = {
    "data-created-at",
    "data-output-name",
    "data-source-file",
    "data-source-name",
    "data-timestamp",
    "data-variant-name",
}
_IGNORED_SVG_ELEMENTS = {"desc", "metadata", "title"}


def normalize_geometry_ir(geometry_ir: list[dict[str, Any]]) -> str:
    """Return stable JSON for the semantic and geometric parts of Geometry-IR."""

    normalized = copy.deepcopy(geometry_ir)
    for element in normalized:
        for key in _IGNORED_IR_KEYS:
            element.pop(key, None)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_svg_geometry(svg: str) -> str:
    """Return canonical SVG XML without output-only names or volatile metadata."""

    root = ElementTree.fromstring(svg)
    for parent in root.iter():
        for child in list(parent):
            local_name = child.tag.rsplit("}", 1)[-1]
            if local_name in _IGNORED_SVG_ELEMENTS:
                parent.remove(child)
        for attribute in list(parent.attrib):
            local_name = attribute.rsplit("}", 1)[-1]
            if local_name in _IGNORED_SVG_ATTRIBUTES:
                del parent.attrib[attribute]
        sorted_attributes = sorted(parent.attrib.items())
        parent.attrib.clear()
        parent.attrib.update(sorted_attributes)
        if parent.text is not None and not parent.text.strip():
            parent.text = None
        if parent.tail is not None and not parent.tail.strip():
            parent.tail = None
    return ElementTree.tostring(root, encoding="unicode", short_empty_elements=True)
