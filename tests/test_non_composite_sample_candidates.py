from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime


def test_build_sample_candidates_includes_ac_alias_for_se_code() -> None:
    candidates = runtime._build_sample_candidates("SE0120")
    assert "SE0120" in candidates
    assert "AC0120" in candidates
    assert "AC0120_L" in candidates
    assert candidates.index("AC0120") < candidates.index("AC0120_L")
    assert len(candidates) == len(set(candidates))


def test_build_sample_candidates_includes_se_alias_for_ac_variant() -> None:
    candidates = runtime._build_sample_candidates("AC0120_M")
    assert "AC0120_M" in candidates
    assert "SE0120" in candidates
    assert "SE0120_S" in candidates
    assert candidates.index("SE0120") < candidates.index("SE0120_S")
    assert len(candidates) == len(set(candidates))
