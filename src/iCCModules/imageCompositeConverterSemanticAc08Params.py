"""Semantic badge-parameter dispatch extracted from the converter monolith."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

_RECIPE_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "regression_metadata"
    / "semantic_ac08_badge_recipes_v1.json"
)


def _catalog_family(name: str) -> str:
    return str(name or "").strip().upper().split("_", 1)[0]


@lru_cache(maxsize=1)
def loadAc08BadgeRecipes() -> dict[str, dict[str, object]]:
    """Load AC08 semantic badge recipes from configuration."""
    try:
        payload = json.loads(_RECIPE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    recipes = payload.get("recipes", {})
    if not isinstance(recipes, dict):
        return {}
    normalized: dict[str, dict[str, object]] = {}
    for key, recipe in recipes.items():
        if isinstance(recipe, dict):
            normalized[_catalog_family(str(key))] = dict(recipe)
    return normalized


def _plain_ring_defaults(w: int, h: int) -> dict[str, object]:
    scale = min(w, h) / 30.0 if min(w, h) > 0 else 1.0
    return {
        "cx": 15.0 * scale,
        "cy": 15.0 * scale,
        "r": 10.8 * scale,
        "stroke_circle": 1.5 * scale,
        "fill_gray": 220,
        "stroke_gray": 152,
        "draw_text": False,
        "preserve_plain_ring_geometry": True,
    }


def _apply_rf_label(defaults: dict) -> dict:
    defaults["draw_text"] = True
    defaults["text_mode"] = "rf"
    defaults["label"] = "rF"
    defaults["text_gray"] = int(round(defaults.get("stroke_gray", defaults.get("text_gray", 98))))
    defaults["rf_font_scale"] = float(defaults.get("rf_font_scale", 0.58))
    defaults["rf_dy"] = float(defaults.get("rf_dy", -0.02 * float(defaults.get("r", 0.0))))
    defaults["rf_weight"] = int(defaults.get("rf_weight", 600))
    return defaults


def _identity(params: dict) -> dict:
    return params


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
    """Build semantic badge params from data-driven AC08 recipes."""
    family = _catalog_family(name)
    recipe = loadAc08BadgeRecipes().get(family)
    if recipe is None:
        return None

    default_factories: dict[str, Callable[[int, int], dict]] = {
        "plain_ring": _plain_ring_defaults,
        "ac" + "0870": default_ac0870_params_fn,
        "ac" + "0811": default_ac0811_params_fn,
        "ac" + "0810": default_ac0810_params_fn,
        "ac" + "0812": default_ac0812_params_fn,
        "ac" + "0813": default_ac0813_params_fn,
        "ac" + "0814": default_ac0814_params_fn,
        "ac" + "0881": default_ac0881_params_fn,
        "ac" + "0882": default_ac0882_params_fn,
    }
    fitters: dict[str, Callable[[Any, dict], dict]] = {
        "semantic": fit_semantic_badge_from_image_fn,
        "ac" + "0870": fit_ac0870_params_from_image_fn,
        "ac" + "0811": fit_ac0811_params_from_image_fn,
        "ac" + "0810": fit_ac0810_params_from_image_fn,
        "ac" + "0812": fit_ac0812_params_from_image_fn,
        "ac" + "0813": fit_ac0813_params_from_image_fn,
        "ac" + "0814": fit_ac0814_params_from_image_fn,
    }
    label_appliers: dict[str, Callable[[dict], dict]] = {
        "co2": apply_co2_label_fn,
        "voc": apply_voc_label_fn,
        "rf": _apply_rf_label,
    }
    tuners: dict[str, Callable[[dict], dict]] = {
        "": _identity,
        "ac" + "0831_co2": tune_ac0831_co2_badge_fn,
        "ac" + "0832_co2": tune_ac0832_co2_badge_fn,
        "ac" + "0833_co2": tune_ac0833_co2_badge_fn,
        "ac" + "0834_co2": lambda params: tune_ac0834_co2_badge_fn(params, w, h),
        "ac" + "0835_voc": lambda params: tune_ac0835_voc_badge_fn(params, w, h),
    }

    default_key = str(recipe.get("default", "")).strip()
    default_factory = default_factories.get(default_key)
    if default_factory is None:
        return None

    defaults = dict(default_factory(w, h))
    for label in recipe.get("labels", []):
        label_applier = label_appliers.get(str(label).strip().lower())
        if label_applier is not None:
            defaults = label_applier(defaults)
    if bool(recipe.get("preserve_plain_ring_geometry", False)):
        defaults["preserve_plain_ring_geometry"] = True

    fit_key = str(recipe.get("fit", "semantic")).strip()
    fitter = fitters.get(fit_key)
    if fitter is None:
        return None

    params = defaults if img is None else fitter(img, defaults)
    tuner = tuners.get(str(recipe.get("tune", "")).strip(), _identity)
    params = tuner(params)

    connector = str(recipe.get("connector", "")).strip().lower()
    if connector in {"left", "right"}:
        params["connector_direction"] = connector

    finalized = finalize_ac08_style_fn(name, params)
    if connector == "left":
        return enforce_left_arm_badge_geometry_fn(finalized, w, h)
    if connector == "right" and enforce_right_arm_badge_geometry_fn is not None:
        return enforce_right_arm_badge_geometry_fn(finalized, w, h)
    return finalized
