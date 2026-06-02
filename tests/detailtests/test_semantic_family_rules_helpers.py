from src.iCCModules import imageCompositeConverterSemantic as helpers


def test_apply_semantic_badge_family_rules_supports_ac0842_left_connector() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_family_rules(
        base_upper="AC0842",
        symbol_upper="AC0842",
        desc='grauer kreis mit text "rf" (relative feuchtigkeit) und waagrechter strich links',
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == "rF"
    assert "SEMANTIC: waagrechter Strich links vom Kreis" in params["elements"]
    assert "SEMANTIC: Kreis + Buchstabe rF" in params["elements"]


def test_apply_semantic_badge_family_rules_parses_explicit_color_count_override() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_family_rules(
        base_upper="AC0800",
        symbol_upper="AC0800",
        desc="grauer Kreis, Farben: 2",
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["badge_overrides"]["palette_color_count"] == "2"


def test_apply_semantic_badge_family_rules_supports_ac0844_right_connector() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_family_rules(
        base_upper="AC0844",
        symbol_upper="AC0844",
        desc='grauer kreis mit text "rf" (relative feuchtigkeit) und griff nach unten',
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == "rF"
    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in params["elements"]
    assert "SEMANTIC: Kreis + Buchstabe rF" in params["elements"]
