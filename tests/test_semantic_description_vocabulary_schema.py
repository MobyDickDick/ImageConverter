from __future__ import annotations

import json
import re
from pathlib import Path


SCHEMA_PATH = Path("docs/vision/semantic_scene_description_v1.schema.json")
EXAMPLES_PATH = Path(
    "artifacts/evaluation/semantic_scene_description_v1/description_vocabulary_examples.json"
)
CATALOG_ID_RE = re.compile(r"\b(?:AC|GE|SE|DLG)\d{4}(?:_[0-9A-Z]+)?\b")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_semantic_description_vocabulary_is_catalog_id_free() -> None:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    examples_text = EXAMPLES_PATH.read_text(encoding="utf-8")

    assert CATALOG_ID_RE.search(schema_text) is None
    assert CATALOG_ID_RE.search(examples_text) is None
    assert "image_id" not in schema_text
    assert "variant" not in schema_text


def test_semantic_description_vocabulary_covers_required_concepts() -> None:
    schema = _load_json(SCHEMA_PATH)
    defs = schema["$defs"]

    primitive_types = set(defs["primitive_type"]["enum"])
    assert {"circle", "ring", "line", "rectangle", "polygon", "path", "text", "glyph"} <= primitive_types

    directions = set(defs["direction"]["enum"])
    assert {"left", "right", "top", "bottom", "horizontal", "vertical", "center"} <= directions

    predicates = set(defs["relation"]["properties"]["predicate"]["enum"])
    assert {"attached_to", "centered_in", "covers", "continues_behind", "left_of", "right_of"} <= predicates

    constraint_rules = set(defs["constraint"]["properties"]["rule"]["enum"])
    assert {"color_hint", "text_content", "text_absent", "occlusion_order", "relation_required"} <= constraint_rules

    negation_rules = set(defs["negation"]["properties"]["rule"]["enum"])
    assert {"without_label", "without_connector", "not_occluded"} <= negation_rules


def test_semantic_description_examples_cover_three_symbol_families() -> None:
    payload = _load_json(EXAMPLES_PATH)
    examples = payload["examples"]

    assert payload["schema_version"] == "semantic_scene_description_examples_v1"
    assert {example["family"] for example in examples} == {
        "circle_connector_left",
        "labeled_badge",
        "occluded_polygon_arrow",
    }

    for example in examples:
        description = example["description"]
        assert description["schema_version"] == "semantic_scene_description_v1"
        assert description["description_id"].startswith("synthetic_")
        assert "canvas" in description
        assert description["objects"]
        assert "negations" in description
        assert all("evidence" in obj for obj in description["objects"])
