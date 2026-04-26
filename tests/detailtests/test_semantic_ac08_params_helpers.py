from src.iCCModules import imageCompositeConverterSemanticAc08Params as helpers


def _stub_params(label: str):
    return {"label": label}


def test_make_ac08_badge_params_returns_none_for_unknown_name() -> None:
    result = helpers.makeAc08BadgeParamsImpl(
        20,
        20,
        "AC9999",
        None,
        default_ac0870_params_fn=lambda *_: _stub_params("ac0870"),
        default_ac0811_params_fn=lambda *_: _stub_params("ac0811"),
        default_ac0810_params_fn=lambda *_: _stub_params("ac0810"),
        default_ac0812_params_fn=lambda *_: _stub_params("ac0812"),
        default_ac0813_params_fn=lambda *_: _stub_params("ac0813"),
        default_ac0814_params_fn=lambda *_: _stub_params("ac0814"),
        default_ac0881_params_fn=lambda *_: _stub_params("ac0881"),
        default_ac0882_params_fn=lambda *_: _stub_params("ac0882"),
        fit_ac0870_params_from_image_fn=lambda img, defaults: defaults,
        fit_semantic_badge_from_image_fn=lambda img, defaults: defaults,
        fit_ac0811_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0810_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0812_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0813_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0814_params_from_image_fn=lambda img, defaults: defaults,
        apply_co2_label_fn=lambda p: p,
        apply_voc_label_fn=lambda p: p,
        tune_ac0831_co2_badge_fn=lambda p: p,
        tune_ac0832_co2_badge_fn=lambda p: p,
        tune_ac0833_co2_badge_fn=lambda p: p,
        tune_ac0834_co2_badge_fn=lambda p, _w, _h: p,
        tune_ac0835_voc_badge_fn=lambda p, _w, _h: p,
        finalize_ac08_style_fn=lambda _name, p: p,
        enforce_left_arm_badge_geometry_fn=lambda p, _w, _h: p,
    )

    assert result is None


def test_make_ac08_badge_params_uses_vertical_voc_fit_for_ac0836() -> None:
    calls: list[str] = []

    def _default_ac0881(_w: int, _h: int) -> dict:
        calls.append("default_ac0881")
        return {"seed": "ac0881"}

    def _apply_voc(params: dict) -> dict:
        calls.append("apply_voc")
        patched = dict(params)
        patched["voc"] = True
        return patched

    def _fit_ac0811(_img, params: dict) -> dict:
        calls.append("fit_ac0811")
        patched = dict(params)
        patched["fit"] = True
        return patched

    def _finalize(name: str, params: dict) -> dict:
        calls.append(f"finalize:{name}")
        patched = dict(params)
        patched["finalized"] = name
        return patched

    result = helpers.makeAc08BadgeParamsImpl(
        20,
        30,
        "AC0836",
        object(),
        default_ac0870_params_fn=lambda *_: _stub_params("ac0870"),
        default_ac0811_params_fn=lambda *_: _stub_params("ac0811"),
        default_ac0810_params_fn=lambda *_: _stub_params("ac0810"),
        default_ac0812_params_fn=lambda *_: _stub_params("ac0812"),
        default_ac0813_params_fn=lambda *_: _stub_params("ac0813"),
        default_ac0814_params_fn=lambda *_: _stub_params("ac0814"),
        default_ac0881_params_fn=_default_ac0881,
        default_ac0882_params_fn=lambda *_: _stub_params("ac0882"),
        fit_ac0870_params_from_image_fn=lambda img, defaults: defaults,
        fit_semantic_badge_from_image_fn=lambda img, defaults: defaults,
        fit_ac0811_params_from_image_fn=_fit_ac0811,
        fit_ac0810_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0812_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0813_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0814_params_from_image_fn=lambda img, defaults: defaults,
        apply_co2_label_fn=lambda p: p,
        apply_voc_label_fn=_apply_voc,
        tune_ac0831_co2_badge_fn=lambda p: p,
        tune_ac0832_co2_badge_fn=lambda p: p,
        tune_ac0833_co2_badge_fn=lambda p: p,
        tune_ac0834_co2_badge_fn=lambda p, _w, _h: p,
        tune_ac0835_voc_badge_fn=lambda p, _w, _h: p,
        finalize_ac08_style_fn=_finalize,
        enforce_left_arm_badge_geometry_fn=lambda p, _w, _h: p,
    )

    assert calls == ["default_ac0881", "apply_voc", "fit_ac0811", "finalize:AC0836"]
    assert result == {"seed": "ac0881", "voc": True, "fit": True, "finalized": "AC0836"}


def test_make_ac08_badge_params_uses_top_vertical_voc_fit_for_ac0838() -> None:
    calls: list[str] = []

    def _default_ac0813(_w: int, _h: int) -> dict:
        calls.append("default_ac0813")
        return {"seed": "ac0813"}

    def _apply_voc(params: dict) -> dict:
        calls.append("apply_voc")
        patched = dict(params)
        patched["voc"] = True
        return patched

    def _fit_ac0813(_img, params: dict) -> dict:
        calls.append("fit_ac0813")
        patched = dict(params)
        patched["fit"] = True
        return patched

    def _finalize(name: str, params: dict) -> dict:
        calls.append(f"finalize:{name}")
        patched = dict(params)
        patched["finalized"] = name
        return patched

    result = helpers.makeAc08BadgeParamsImpl(
        20,
        30,
        "AC0838",
        object(),
        default_ac0870_params_fn=lambda *_: _stub_params("ac0870"),
        default_ac0811_params_fn=lambda *_: _stub_params("ac0811"),
        default_ac0810_params_fn=lambda *_: _stub_params("ac0810"),
        default_ac0812_params_fn=lambda *_: _stub_params("ac0812"),
        default_ac0813_params_fn=_default_ac0813,
        default_ac0814_params_fn=lambda *_: _stub_params("ac0814"),
        default_ac0881_params_fn=lambda *_: _stub_params("ac0881"),
        default_ac0882_params_fn=lambda *_: _stub_params("ac0882"),
        fit_ac0870_params_from_image_fn=lambda img, defaults: defaults,
        fit_semantic_badge_from_image_fn=lambda img, defaults: defaults,
        fit_ac0811_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0810_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0812_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0813_params_from_image_fn=_fit_ac0813,
        fit_ac0814_params_from_image_fn=lambda img, defaults: defaults,
        apply_co2_label_fn=lambda p: p,
        apply_voc_label_fn=_apply_voc,
        tune_ac0831_co2_badge_fn=lambda p: p,
        tune_ac0832_co2_badge_fn=lambda p: p,
        tune_ac0833_co2_badge_fn=lambda p: p,
        tune_ac0834_co2_badge_fn=lambda p, _w, _h: p,
        tune_ac0835_voc_badge_fn=lambda p, _w, _h: p,
        finalize_ac08_style_fn=_finalize,
        enforce_left_arm_badge_geometry_fn=lambda p, _w, _h: p,
    )

    assert calls == ["default_ac0813", "apply_voc", "fit_ac0813", "finalize:AC0838"]
    assert result == {"seed": "ac0813", "voc": True, "fit": True, "finalized": "AC0838"}


def test_make_ac08_badge_params_applies_rf_text_mode_for_ac0842() -> None:
    calls: list[str] = []

    def _default_ac0812(_w: int, _h: int) -> dict:
        calls.append("default_ac0812")
        return {"seed": "ac0812", "stroke_gray": 152, "r": 9.0}

    def _fit_ac0812(_img, params: dict) -> dict:
        calls.append("fit_ac0812")
        patched = dict(params)
        patched["fit"] = True
        return patched

    def _finalize(name: str, params: dict) -> dict:
        calls.append(f"finalize:{name}")
        patched = dict(params)
        patched["finalized"] = name
        return patched

    def _enforce_left(params: dict, _w: int, _h: int) -> dict:
        calls.append("enforce_left")
        patched = dict(params)
        patched["enforced"] = True
        return patched

    result = helpers.makeAc08BadgeParamsImpl(
        20,
        30,
        "AC0842",
        object(),
        default_ac0870_params_fn=lambda *_: _stub_params("ac0870"),
        default_ac0811_params_fn=lambda *_: _stub_params("ac0811"),
        default_ac0810_params_fn=lambda *_: _stub_params("ac0810"),
        default_ac0812_params_fn=_default_ac0812,
        default_ac0813_params_fn=lambda *_: _stub_params("ac0813"),
        default_ac0814_params_fn=lambda *_: _stub_params("ac0814"),
        default_ac0881_params_fn=lambda *_: _stub_params("ac0881"),
        default_ac0882_params_fn=lambda *_: _stub_params("ac0882"),
        fit_ac0870_params_from_image_fn=lambda img, defaults: defaults,
        fit_semantic_badge_from_image_fn=lambda img, defaults: defaults,
        fit_ac0811_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0810_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0812_params_from_image_fn=_fit_ac0812,
        fit_ac0813_params_from_image_fn=lambda img, defaults: defaults,
        fit_ac0814_params_from_image_fn=lambda img, defaults: defaults,
        apply_co2_label_fn=lambda p: p,
        apply_voc_label_fn=lambda p: p,
        tune_ac0831_co2_badge_fn=lambda p: p,
        tune_ac0832_co2_badge_fn=lambda p: p,
        tune_ac0833_co2_badge_fn=lambda p: p,
        tune_ac0834_co2_badge_fn=lambda p, _w, _h: p,
        tune_ac0835_voc_badge_fn=lambda p, _w, _h: p,
        finalize_ac08_style_fn=_finalize,
        enforce_left_arm_badge_geometry_fn=_enforce_left,
    )

    assert calls == ["default_ac0812", "fit_ac0812", "finalize:AC0842", "enforce_left"]
    assert result["text_mode"] == "rf"
    assert result["label"] == "rF"
    assert result["draw_text"] is True
    assert result["enforced"] is True
