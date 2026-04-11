from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticConnectors as semantic_connector_helpers


def test_enforce_left_arm_badge_geometry_sets_visible_left_connector() -> None:
    params = {
        "circle_enabled": True,
        "cx": 14.0,
        "cy": 8.0,
        "r": 5.0,
    }

    result = semantic_connector_helpers.enforceLeftArmBadgeGeometryImpl(
        params,
        ac08_stroke_width_px=2.0,
    )

    assert result["arm_enabled"] is True
    assert result["arm_x1"] == 0.0
    assert result["arm_x2"] >= 0.0
    assert result["arm_len_min"] >= 1.0


def test_enforce_top_stem_badge_geometry_keeps_circle_in_lower_half() -> None:
    params = {
        "circle_enabled": True,
        "cx": 12.0,
        "cy": 10.0,
        "r": 6.0,
        "template_circle_cy": 28.0,
    }

    result = semantic_connector_helpers.enforceTopStemBadgeGeometryImpl(
        params,
        h=45,
        ac08_stroke_width_px=2.0,
    )

    assert result["arm_enabled"] is True
    assert float(result["cy"]) >= 24.0
    assert float(result["arm_y2"]) == 0.0


def test_enforce_semantic_connector_expectation_routes_to_left_and_right_handlers() -> None:
    called = {"left": 0, "right": 0, "top": 0}

    def _left(p: dict[str, object]) -> dict[str, object]:
        called["left"] += 1
        q = dict(p)
        q["route"] = "left"
        return q

    def _right(p: dict[str, object]) -> dict[str, object]:
        called["right"] += 1
        q = dict(p)
        q["route"] = "right"
        return q

    def _top(p: dict[str, object]) -> dict[str, object]:
        called["top"] += 1
        q = dict(p)
        q["route"] = "top"
        return q

    left = semantic_connector_helpers.enforceSemanticConnectorExpectationImpl(
        "AC0812_L.jpg",
        ["SEMANTIC: Kreis mit waagrechter Strich links"],
        {},
        normalize_base_name_fn=lambda name: name.split("_")[0],
        enforce_left_fn=_left,
        enforce_right_fn=_right,
        enforce_top_fn=_top,
    )
    right = semantic_connector_helpers.enforceSemanticConnectorExpectationImpl(
        "AC0810_L.jpg",
        ["SEMANTIC: Kreis mit waagrechter Strich rechts"],
        {},
        normalize_base_name_fn=lambda name: name.split("_")[0],
        enforce_left_fn=_left,
        enforce_right_fn=_right,
        enforce_top_fn=_top,
    )

    assert left["route"] == "left"
    assert right["route"] == "right"
    assert called == {"left": 1, "right": 1, "top": 0}


def test_enforce_semantic_connector_expectation_routes_top_stem_family() -> None:
    result = semantic_connector_helpers.enforceSemanticConnectorExpectationImpl(
        "AC0838_M.jpg",
        ["SEMANTIC: senkrechter Strich oben vom Kreis"],
        {"route": "unchanged"},
        normalize_base_name_fn=lambda name: name.split("_")[0],
        enforce_left_fn=lambda p: {**p, "route": "left"},
        enforce_right_fn=lambda p: {**p, "route": "right"},
        enforce_top_fn=lambda p: {**p, "route": "top"},
    )

    assert result["route"] == "top"
