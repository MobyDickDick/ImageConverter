from src.iCCModules import imageCompositeConverterSemanticAc08Families as helpers


def _base_name(name: str) -> str:
    return name


def test_tune_left_connector_family_applies_expected_guards():
    center_calls: list[dict] = []

    def _small_variant(_name: str, _params: dict):
        return True, "small", 20.0

    def _enforce_edge(params: dict, _w: int, _h: int, *, anchor: str, retain_ratio: float):
        patched = dict(params)
        patched["edge_anchor"] = anchor
        patched["edge_retain"] = retain_ratio
        return patched

    def _enforce_left(params: dict, _w: int, _h: int):
        patched = dict(params)
        patched["arm_len_min"] = 8.0
        patched["arm_enabled"] = True
        return patched

    def _center(p: dict) -> None:
        center_calls.append(dict(p))

    tuned = helpers.tuneAc08LeftConnectorFamilyImpl(
        "AC0812_L",
        {
            "template_circle_cx": 10,
            "template_circle_cy": 8,
            "template_circle_radius": 6,
            "text_mode": "path_t",
            "s": 0.0,
            "cx": 11,
        },
        get_base_name_from_file_fn=_base_name,
        is_ac08_small_variant_fn=_small_variant,
        enforce_template_circle_edge_extent_fn=_enforce_edge,
        enforce_left_arm_badge_geometry_fn=_enforce_left,
        center_glyph_bbox_fn=_center,
    )

    assert tuned["connector_family_group"] == "ac08_left_connector"
    assert tuned["edge_anchor"] == "right"
    assert tuned["edge_retain"] == 0.96
    assert tuned["max_circle_radius"] == 2.0
    assert tuned["s"] >= 0.0088
    assert center_calls


def test_tune_right_connector_family_skips_non_target_symbols():
    params = {"template_circle_cx": 12.0, "template_circle_cy": 9.0}
    tuned = helpers.tuneAc08RightConnectorFamilyImpl(
        "AC9999_M",
        params,
        get_base_name_from_file_fn=_base_name,
        is_ac08_small_variant_fn=lambda *_: (False, "", 0.0),
        enforce_template_circle_edge_extent_fn=lambda p, *_args, **_kwargs: p,
        enforce_right_arm_badge_geometry_fn=lambda p, *_args, **_kwargs: p,
    )
    assert tuned == params


def test_tune_vertical_connector_family_sets_text_and_stem_defaults():
    def _enforce_vertical(params: dict, _w: int, _h: int):
        patched = dict(params)
        patched["geometry_enforced"] = True
        return patched

    tuned = helpers.tuneAc08VerticalConnectorFamilyImpl(
        "AC0831_S",
        {
            "template_circle_cx": 8,
            "template_circle_cy": 8,
            "template_circle_radius": 7,
            "text_mode": "co2",
            "co2_font_scale": 0.80,
        },
        get_base_name_from_file_fn=_base_name,
        is_ac08_small_variant_fn=lambda *_: (True, "small", 16.0),
        enforce_vertical_connector_badge_geometry_fn=_enforce_vertical,
    )

    assert tuned["connector_family_direction"] == "vertical"
    assert tuned["stem_enabled"] is True
    assert tuned["lock_stem_center_to_circle"] is True
    assert tuned["geometry_enforced"] is True
    assert tuned["co2_anchor_mode"] == "cluster"
    assert tuned["co2_font_scale_min"] >= 0.78


def test_tune_circle_text_family_applies_voc_bounds_for_small_badges():
    tuned = helpers.tuneAc08CircleTextFamilyImpl(
        "AC0835_S",
        {
            "template_circle_cx": 10,
            "template_circle_cy": 10,
            "template_circle_radius": 5,
            "text_mode": "voc",
            "width": 14,
            "height": 14,
            "cx": 10,
            "cy": 10,
            "voc_font_scale": 0.5,
        },
        get_base_name_from_file_fn=_base_name,
        max_circle_radius_inside_canvas_fn=lambda *_: 9.0,
        center_glyph_bbox_fn=lambda *_: None,
    )

    assert tuned["connector_family_group"] == "ac08_circle_text"
    assert tuned["min_circle_radius"] >= 4.69
    assert tuned["max_circle_radius"] <= 9.0
    assert tuned["voc_font_scale_max"] <= 0.92
