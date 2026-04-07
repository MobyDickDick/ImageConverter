from __future__ import annotations

from src.iCCModules import imageCompositeConverterRandom as random_helpers


def test_conversion_random_impl_uses_seed_env(monkeypatch) -> None:
    monkeypatch.setenv("TINY_ICC_RANDOM_SEED", "123")

    rng_a = random_helpers.conversionRandomImpl()
    rng_b = random_helpers.conversionRandomImpl()

    assert rng_a.random() == rng_b.random()


def test_conversion_random_impl_falls_back_to_time_ns_for_invalid_seed(monkeypatch) -> None:
    monkeypatch.setenv("TINY_ICC_RANDOM_SEED", "not-an-int")
    monkeypatch.setattr(random_helpers.time, "time_ns", lambda: 777)

    rng = random_helpers.conversionRandomImpl()

    assert rng.random() == 0.22933408950153078
