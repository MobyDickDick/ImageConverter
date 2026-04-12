from src.iCCModules import imageCompositeConverterNaming as naming


def test_get_base_name_from_file_impl_normalizes_variant_suffixes():
    assert naming.getBaseNameFromFileImpl("AC0838_S.jpg") == "AC0838"
    assert naming.getBaseNameFromFileImpl("AC0838_S_sia.png") == "AC0838"
    assert naming.getBaseNameFromFileImpl("AC0501_2_L.svg") == "AC0501"


def test_get_base_name_from_file_impl_keeps_non_variant_suffixes():
    assert naming.getBaseNameFromFileImpl("custom-symbol.svg") == "custom-symbol"
