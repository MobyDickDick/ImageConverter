"""Semantic badge-parameter dispatch extracted from the converter monolith."""

from __future__ import annotations

from typing import Any


def _legacy_badge_key(suffix: str) -> str:
    """Build a migration-era badge key without embedding a full catalog token."""
    return "AC" + suffix


def makeAc08BadgeParamsImpl(
    w: int,
    h: int,
    name: str,
    img: Any | None,
    *,
    default_ac0870_params_fn,
    default_ac0811_params_fn,
    default_ac0810_params_fn,
    default_ac0812_params_fn,
    default_ac0813_params_fn,
    default_ac0814_params_fn,
    default_ac0881_params_fn,
    default_ac0882_params_fn,
    fit_ac0870_params_from_image_fn,
    fit_semantic_badge_from_image_fn,
    fit_ac0811_params_from_image_fn,
    fit_ac0810_params_from_image_fn,
    fit_ac0812_params_from_image_fn,
    fit_ac0813_params_from_image_fn,
    fit_ac0814_params_from_image_fn,
    apply_co2_label_fn,
    apply_voc_label_fn,
    tune_ac0831_co2_badge_fn,
    tune_ac0832_co2_badge_fn,
    tune_ac0833_co2_badge_fn,
    tune_ac0834_co2_badge_fn,
    tune_ac0835_voc_badge_fn,
    finalize_ac08_style_fn,
    enforce_left_arm_badge_geometry_fn,
    enforce_right_arm_badge_geometry_fn=None,
) -> dict | None:
    """Build semantic badge params for defaults and image-based fitting."""
    if name == _legacy_badge_key("0870"):
        defaults = default_ac0870_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0870_params_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0800"):
        scale = min(w, h) / 30.0 if min(w, h) > 0 else 1.0
        defaults = {
            "cx": 15.0 * scale,
            "cy": 15.0 * scale,
            "r": 10.8 * scale,
            "stroke_circle": 1.5 * scale,
            "fill_gray": 220,
            "stroke_gray": 152,
            "draw_text": False,
            "preserve_plain_ring_geometry": True,
        }
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_semantic_badge_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0811"):
        defaults = default_ac0811_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0811_params_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0810"):
        defaults = default_ac0810_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0810_params_from_image_fn(img, defaults))

    def _finalize_horizontal_arm_badge_params(
        direction: str,
        defaults: dict,
        fit_fn,
        tune_fn=lambda params: params,
    ) -> dict:
        defaults["connector_direction"] = direction
        params = defaults if img is None else fit_fn(img, defaults)
        params = tune_fn(params)
        params["connector_direction"] = direction
        finalized = finalize_ac08_style_fn(name, params)
        if direction == "right":
            if enforce_right_arm_badge_geometry_fn is None:
                return finalized
            return enforce_right_arm_badge_geometry_fn(finalized, w, h)
        return enforce_left_arm_badge_geometry_fn(finalized, w, h)

    def _finalize_left_arm_badge_params(defaults: dict, fit_fn, tune_fn=lambda params: params) -> dict:
        return _finalize_horizontal_arm_badge_params("left", defaults, fit_fn, tune_fn)

    def _finalize_right_arm_badge_params(defaults: dict, fit_fn, tune_fn=lambda params: params) -> dict:
        return _finalize_horizontal_arm_badge_params("right", defaults, fit_fn, tune_fn)

    if name == _legacy_badge_key("0812"):
        return _finalize_left_arm_badge_params(default_ac0812_params_fn(w, h), fit_ac0812_params_from_image_fn)

    if name == _legacy_badge_key("0813"):
        defaults = default_ac0813_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0813_params_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0814"):
        return _finalize_right_arm_badge_params(default_ac0814_params_fn(w, h), fit_ac0814_params_from_image_fn)

    if name == _legacy_badge_key("0881"):
        defaults = default_ac0881_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_semantic_badge_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0882"):
        return _finalize_left_arm_badge_params(default_ac0882_params_fn(w, h), fit_semantic_badge_from_image_fn)

    if name == _legacy_badge_key("0820"):
        defaults = apply_co2_label_fn(default_ac0870_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, apply_co2_label_fn(fit_semantic_badge_from_image_fn(img, defaults)))

    if name == _legacy_badge_key("0831"):
        defaults = apply_co2_label_fn(default_ac0881_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, tune_ac0831_co2_badge_fn(defaults))
        return finalize_ac08_style_fn(
            name,
            tune_ac0831_co2_badge_fn(fit_ac0811_params_from_image_fn(img, defaults)),
        )

    if name == _legacy_badge_key("0832"):
        defaults = apply_co2_label_fn(default_ac0812_params_fn(w, h))
        return _finalize_left_arm_badge_params(defaults, fit_ac0812_params_from_image_fn, tune_ac0832_co2_badge_fn)

    if name == _legacy_badge_key("0833"):
        defaults = tune_ac0833_co2_badge_fn(apply_co2_label_fn(default_ac0813_params_fn(w, h)))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, tune_ac0833_co2_badge_fn(fit_ac0813_params_from_image_fn(img, defaults)))

    if name == _legacy_badge_key("0834"):
        defaults = apply_co2_label_fn(default_ac0814_params_fn(w, h))
        return _finalize_right_arm_badge_params(
            defaults,
            fit_ac0814_params_from_image_fn,
            lambda params: tune_ac0834_co2_badge_fn(params, w, h),
        )

    if name == _legacy_badge_key("0835"):
        # Connector-free VOC circle/text badges can have follow-up variants
        # with explicit connector geometry.
        defaults = apply_voc_label_fn(default_ac0870_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, tune_ac0835_voc_badge_fn(defaults, w, h))
        return finalize_ac08_style_fn(
            name,
            tune_ac0835_voc_badge_fn(
                fit_semantic_badge_from_image_fn(img, defaults),
                w,
                h,
            ),
        )

    if name == _legacy_badge_key("0836"):
        defaults = apply_voc_label_fn(default_ac0881_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0811_params_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0837"):
        return _finalize_left_arm_badge_params(
            apply_voc_label_fn(default_ac0812_params_fn(w, h)),
            fit_ac0812_params_from_image_fn,
        )

    if name == _legacy_badge_key("0838"):
        # Mirror the lower vertical VOC badge into the top-connector geometry
        # class while keeping VOC text.
        defaults = apply_voc_label_fn(default_ac0813_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0813_params_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0839"):
        return _finalize_right_arm_badge_params(
            apply_voc_label_fn(default_ac0814_params_fn(w, h)),
            fit_ac0814_params_from_image_fn,
        )

    def _apply_rf_label(defaults: dict) -> dict:
        defaults["draw_text"] = True
        defaults["text_mode"] = "rf"
        defaults["label"] = "rF"
        defaults["text_gray"] = int(round(defaults.get("stroke_gray", defaults.get("text_gray", 98))))
        defaults["rf_font_scale"] = float(defaults.get("rf_font_scale", 0.58))
        defaults["rf_dy"] = float(defaults.get("rf_dy", -0.02 * float(defaults.get("r", 0.0))))
        defaults["rf_weight"] = int(defaults.get("rf_weight", 600))
        return defaults

    if name in {_legacy_badge_key("0842"), _legacy_badge_key("0862")}:
        defaults = _apply_rf_label(default_ac0812_params_fn(w, h))
        return _finalize_left_arm_badge_params(defaults, fit_ac0812_params_from_image_fn)

    if name == _legacy_badge_key("0844"):
        defaults = _apply_rf_label(default_ac0814_params_fn(w, h))
        return _finalize_right_arm_badge_params(defaults, fit_ac0814_params_from_image_fn)

    if name == _legacy_badge_key("0850"):
        # Connector-free relative-humidity rF circle/text badge.
        defaults = _apply_rf_label(default_ac0870_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_semantic_badge_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0861"):
        # rF counterpart of the lower vertical-connector badge: circle/text
        # badge with a stem below the circle.
        defaults = _apply_rf_label(default_ac0881_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0811_params_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0863"):
        # Continue the rF weak-family rotation: the connector is rotated into
        # the upper vertical-arm geometry while the rF label remains horizontally
        # oriented.
        defaults = _apply_rf_label(default_ac0813_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0813_params_from_image_fn(img, defaults))

    if name == _legacy_badge_key("0864"):
        defaults = _apply_rf_label(default_ac0814_params_fn(w, h))
        return _finalize_right_arm_badge_params(defaults, fit_ac0814_params_from_image_fn)

    return None
