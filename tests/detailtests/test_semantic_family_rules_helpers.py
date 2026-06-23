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


def test_apply_semantic_badge_family_rules_supports_ac0862_left_connector() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_family_rules(
        base_upper="AC0862",
        symbol_upper="AC0862",
        desc='grauer kreis mit text "rf" (relative feuchtigkeit) und griff nach rechts gedreht',
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


def test_apply_semantic_badge_family_rules_derives_left_connector_from_rotated_alias_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_family_rules(
        base_upper="AC0832",
        symbol_upper="AC0832",
        desc="wie AC0832, jedoch nach rechts gedreht, text immer noch horizontal",
        params=params,
    )

    assert applied is True
    assert "SEMANTIC: waagrechter Strich links vom Kreis" in params["elements"]
    assert (
        "SEMANTIC: waagrechter Strich links vom Kreis"
        in params["semantic_sources"]["description_heuristic"]
    )


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
    assert (
        "SEMANTIC: waagrechter Strich rechts vom Kreis"
        not in params["semantic_sources"]["family_rule"]
    )
    assert (
        "SEMANTIC: waagrechter Strich rechts vom Kreis"
        in params["semantic_sources"]["description_heuristic"]
    )
    assert "SEMANTIC: Kreis + Buchstabe rF" in params["elements"]


def test_apply_semantic_badge_family_rules_derives_right_connector_from_rotated_alias_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_family_rules(
        base_upper="AC0844",
        symbol_upper="AC0844",
        desc='grauer kreis mit text "rf" (relative feuchtigkeit) und griff nach links gedreht, text immer noch horizontal',
        params=params,
    )

    assert applied is True
    assert params["label"] == "rF"
    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in params["elements"]
    assert (
        "SEMANTIC: waagrechter Strich rechts vom Kreis"
        not in params["semantic_sources"]["family_rule"]
    )
    assert (
        "SEMANTIC: waagrechter Strich rechts vom Kreis"
        in params["semantic_sources"]["description_heuristic"]
    )


def test_apply_semantic_badge_family_rules_derives_left_connector_without_family_id_list() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_family_rules(
        base_upper="AC0842",
        symbol_upper="AC0842",
        desc=(
            'grauer kreis mit text "rf" (relative feuchtigkeit) '
            "und waagrechter strich links vom kreis"
        ),
        params=params,
    )

    assert applied is True
    assert "SEMANTIC: waagrechter Strich links vom Kreis" in params["elements"]
    assert (
        "SEMANTIC: waagrechter Strich links vom Kreis"
        not in params["semantic_sources"]["family_rule"]
    )
    assert (
        "SEMANTIC: waagrechter Strich links vom Kreis"
        in params["semantic_sources"]["description_heuristic"]
    )


def test_apply_semantic_badge_family_rules_derives_legacy_right_connectors_without_family_id_list() -> None:
    cases = [
        ("AC0810", "Kelle mit Kreis, Griff nach unten."),
        ("AC0814", "Wie AC0811: Kelle mit Kreis oben und Griff nach unten."),
        ("AC0834", "Kelle mit Kreis und Griff unten, Text bleibt horizontal."),
        (
            "AC0839",
            "VOC-Kreis in der gegenüberliegenden Drehlage; "
            "der Griff bleibt als Zusatzarm am Kreis erkennbar.",
        ),
    ]

    for base_upper, desc in cases:
        params: dict[str, object] = {"elements": []}

        applied = helpers.apply_semantic_badge_family_rules(
            base_upper=base_upper,
            symbol_upper=base_upper,
            desc=desc.lower(),
            params=params,
        )

        assert applied is True
        assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in params["elements"]
        assert (
            "SEMANTIC: waagrechter Strich rechts vom Kreis"
            not in params["semantic_sources"]["family_rule"]
        )
        assert (
            "SEMANTIC: waagrechter Strich rechts vom Kreis"
            in params["semantic_sources"]["description_heuristic"]
        )


def test_apply_semantic_badge_description_rules_derives_left_connector_from_relation_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_description_rules(
        desc="neutraler Kreis mit Linie links vom Kreis und ohne Buchstabe",
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == ""
    assert "SEMANTIC: waagrechter Strich links vom Kreis" in params["elements"]
    assert params["semantic_sources"]["description_heuristic"] == [
        "SEMANTIC: Kreis ohne Buchstabe",
        "SEMANTIC: waagrechter Strich links vom Kreis",
    ]


def test_apply_semantic_badge_description_rules_derives_left_connector_from_inverse_relation_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_description_rules(
        desc="neutraler Kreis rechts von der Linie mit linker Anschlusslinie und ohne Buchstabe",
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == ""
    assert "SEMANTIC: waagrechter Strich links vom Kreis" in params["elements"]


def test_apply_semantic_badge_description_rules_derives_right_connector_from_relation_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_description_rules(
        desc="neutraler Kreis mit Linie rechts vom Kreis und ohne Buchstabe",
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == ""
    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in params["elements"]
    assert params["semantic_sources"]["description_heuristic"] == [
        "SEMANTIC: Kreis ohne Buchstabe",
        "SEMANTIC: waagrechter Strich rechts vom Kreis",
    ]


def test_apply_semantic_badge_description_rules_derives_right_connector_from_inverse_relation_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_description_rules(
        desc="neutraler Kreis links vom Strich mit rechter Anschlusslinie und ohne Buchstabe",
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == ""
    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in params["elements"]

def test_apply_semantic_badge_description_rules_derives_top_connector_from_relation_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_description_rules(
        desc="neutraler Kreis mit oberer Anschlusslinie und ohne Buchstabe",
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == ""
    assert "SEMANTIC: senkrechter Strich oben vom Kreis" in params["elements"]
    assert params["semantic_sources"]["description_heuristic"] == [
        "SEMANTIC: Kreis ohne Buchstabe",
        "SEMANTIC: senkrechter Strich oben vom Kreis",
    ]


def test_apply_semantic_badge_description_rules_derives_bottom_connector_from_inverse_relation_text() -> None:
    params: dict[str, object] = {"elements": []}

    applied = helpers.apply_semantic_badge_description_rules(
        desc="neutraler Kreis über der Linie mit unterem Anschluss und ohne Buchstabe",
        params=params,
    )

    assert applied is True
    assert params["mode"] == "semantic_badge"
    assert params["label"] == ""
    assert "SEMANTIC: senkrechter Strich hinter dem Kreis" in params["elements"]


def test_apply_semantic_badge_family_rules_loads_neutral_family_metadata(tmp_path, monkeypatch) -> None:
    metadata_path = tmp_path / "semantic_badge_families_v1.json"
    metadata_path.write_text(
        '{"schema_version": 1, "families": ["ZZ_NEUTRAL_BADGE"]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(helpers, "_SEMANTIC_BADGE_FAMILY_METADATA_PATH", metadata_path)
    helpers.load_semantic_badge_families.cache_clear()
    try:
        params: dict[str, object] = {"elements": []}

        applied = helpers.apply_semantic_badge_family_rules(
            base_upper="ZZ_NEUTRAL_BADGE",
            symbol_upper="ZZ_NEUTRAL_BADGE",
            desc="neutraler Kreis mit Buchstabe",
            params=params,
        )

        assert applied is True
        assert params["mode"] == "semantic_badge"
        assert "SEMANTIC: Kreis + Buchstabe" in params["elements"]
    finally:
        helpers.load_semantic_badge_families.cache_clear()
