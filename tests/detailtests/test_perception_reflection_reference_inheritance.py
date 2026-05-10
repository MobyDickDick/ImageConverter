from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection


def test_parse_description_inherits_dual_arrow_mode_from_wie_reference() -> None:
    mapping = {
        "AC0021": "zwei vertikale Striche links blau, rechts, rot, unten Dreiecke blau rot, links Spitze nach unten, rechts Spitze nach oben",
        "AC0040": "Wie AC0021: identisch zur Referenz.",
    }

    _desc, params = Reflection(mapping).parse_description("AC0040", "AC0040_L.jpg")

    assert params["mode"] == "dual_arrow_badge"
    assert any("zwei vertikale farbige Pfeile" in element for element in params["elements"])
    assert any("REFERENZ: Abgeleitet aus AC0021" == element for element in params["elements"])


def test_parse_description_breaks_reference_cycles_without_crashing() -> None:
    mapping = {
        "AC1000": "Wie AC1001",
        "AC1001": "Wie AC1000",
    }

    _desc, params = Reflection(mapping).parse_description("AC1000", "AC1000_L.jpg")

    assert params["mode"] in {"auto", "non_composite", "manual_review", "composite", "semantic_badge", "dual_arrow_badge"}
