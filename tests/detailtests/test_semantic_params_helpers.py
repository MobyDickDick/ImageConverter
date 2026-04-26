from src.iCCModules import imageCompositeConverterSemanticParams as helpers


def test_make_badge_params_prefers_ar0100_when_available() -> None:
    calls: list[str] = []

    def _build_ar0100(w: int, h: int, name: str):
        calls.append(f"ar0100:{w}x{h}:{name}")
        return {"family": name, "from": "ar0100"}

    def _build_ac08(_w: int, _h: int, _name: str, _img):
        calls.append("ac08")
        return {"from": "ac08"}

    result = helpers.makeBadgeParamsImpl(
        10,
        20,
        "ar0100_example",
        img=None,
        get_base_name_fn=lambda base_name: base_name.split("_")[0],
        build_ar0100_badge_params_fn=_build_ar0100,
        build_ac0223_badge_params_fn=lambda _w, _h, _name, _img: {"from": "ac0223"},
        make_ac08_badge_params_fn=_build_ac08,
    )

    assert result == {
        "family": "AR0100",
        "from": "ar0100",
        "base_name": "AR0100",
        "variant_name": "ar0100_example",
    }
    assert calls == ["ar0100:10x20:AR0100"]


def test_make_badge_params_falls_back_to_ac08_when_ar0100_missing() -> None:
    calls: list[str] = []

    result = helpers.makeBadgeParamsImpl(
        30,
        40,
        "ac0836_variant",
        img={"raw": True},
        get_base_name_fn=lambda base_name: base_name.split("_")[0],
        build_ar0100_badge_params_fn=lambda _w, _h, name: calls.append(f"ar0100:{name}") or None,
        build_ac0223_badge_params_fn=lambda _w, _h, name, _img: calls.append(f"ac0223:{name}") or None,
        make_ac08_badge_params_fn=lambda _w, _h, name, img: calls.append(f"ac08:{name}:{bool(img)}") or {"family": name},
    )

    assert result == {
        "family": "AC0836",
        "base_name": "AC0836",
        "variant_name": "ac0836_variant",
    }
    assert calls == ["ar0100:AC0836", "ac0223:AC0836", "ac08:AC0836:True"]


def test_make_badge_params_supports_ac0842_family_dispatch() -> None:
    result = helpers.makeBadgeParamsImpl(
        24,
        24,
        "AC0842_M",
        img=None,
        get_base_name_fn=lambda base_name: base_name.split("_")[0],
        build_ar0100_badge_params_fn=lambda *_args, **_kwargs: None,
        build_ac0223_badge_params_fn=lambda *_args, **_kwargs: None,
        make_ac08_badge_params_fn=lambda _w, _h, name, _img: {"family": name, "ok": True},
    )

    assert result == {
        "family": "AC0842",
        "ok": True,
        "base_name": "AC0842",
        "variant_name": "AC0842_M",
    }
