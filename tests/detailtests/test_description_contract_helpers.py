from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection


def _parse(desc: str):
    mapping = {"AC9999": desc}
    return Reflection(mapping).parse_description("AC9999", "AC9999_L.jpg")


def test_description_contract_complete_description_marks_ok() -> None:
    _desc, params = _parse("Wie AC0030, Kreis mit Rechteck und Kreuz, nur oben verwenden.")
    contract = params["description_contract"]
    assert contract["has_reference"] is True
    assert contract["has_geometry_terms"] is True
    assert contract["has_conditions"] is True
    assert contract["status"] == "ok"
    assert params["contract_status"] == "ok"


def test_description_contract_recursive_alias_keeps_contract() -> None:
    mapping = {
        "AC9998": "Wie AC9997, Kreis mit Linie",
        "AC9997": "Wie AC0030, Kreis mit Linie",
    }
    _desc, params = Reflection(mapping).parse_description("AC9998", "AC9998_L.jpg")
    assert params["contract_status"] == "ok"


def test_description_contract_empty_description_is_insufficient() -> None:
    _desc, params = _parse("")
    assert params["contract_status"] == "insufficient_description"
    assert params["mode"] == "insufficient_description"
    assert "missing_description" in params["description_contract"]["deficits"]


def test_description_contract_alias_only_marks_reference_without_geometry_terms() -> None:
    _desc, params = _parse("Wie AC0030")
    contract = params["description_contract"]
    assert contract["has_reference"] is True
    assert contract["has_geometry_terms"] is False
    assert params["contract_status"] == "ok"
