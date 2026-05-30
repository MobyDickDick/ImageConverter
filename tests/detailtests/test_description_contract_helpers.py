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

def test_description_parser_attaches_geometry_ir_for_ac0120_like_description() -> None:
    _desc, params = _parse(
        "Wie AC0030: Kühlelement, graues Rechteck, Minus-Minus-Zeichen oben Mitte, "
        "Farbverlauf horizontal dunkel-hell-dunkel, graue Linien in beiden Diagonalen."
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]][:4] == [
        "HorizontalGradient",
        "RectBorder",
        "DiagonalBand",
        "DiagonalBand",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0160_like_description() -> None:
    _desc, params = _parse(
        'Differenzdruckmessung oben kleines graues Rechteck mit "dp" geschrieben, '
        'vor halbem Rechteck mit doppelten grauen Rand'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "HalfDoubleRectBorder",
        "LabelBox",
        "TextGlyph",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0201_upward_compressor() -> None:
    _desc, params = _parse("Kompressor grau nach oben")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "UpwardCompressorGlyph",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0202_rightward_compressor() -> None:
    _desc, params = _parse("Kompressor grau nach rechts")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "RightwardCompressorGlyph",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0203_main_diagonal_mirrored_compressor() -> None:
    _desc, params = _parse(
        "Wie AC0202: Kompressor grau nach rechts. Geometrische Variante: Hauptdiagonal gespiegelt."
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "MainDiagonalMirroredCompressorGlyph",
    ]
