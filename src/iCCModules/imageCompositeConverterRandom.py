"""Randomization helpers extracted from the converter monolith."""

from __future__ import annotations

import os
import random
import time


def conversionRandomImpl(seed_env_var: str = "TINY_ICC_RANDOM_SEED") -> random.Random:
    """Return run-local RNG (seedable via env) for non-deterministic ordering."""
    from src.iCCModules.imageCompositeConverterSearchPortfolio import settings
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
    session = current_search()
    if session is not None and session.search_seed is not None:
        return random.Random(session.search_seed)
    config = settings()
    if config is not None:
        return random.Random(int(config['seed']))
    seed_raw = os.environ.get(seed_env_var)
    if seed_raw is not None and str(seed_raw).strip() != "":
        try:
            return random.Random(int(str(seed_raw).strip()))
        except ValueError:
            pass
    return random.Random(time.time_ns())


def conversionSeedImpl(rng, *, deterministic_order: bool = False) -> int:
    """One selected seed for semantic/composite and analytic model searches.

    Deterministic file ordering does not override a selected geometry seed.
    Keep the legacy behavior for library callers without search configuration.
    """
    from src.iCCModules.imageCompositeConverterSearchPortfolio import settings
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
    session = current_search()
    if session is not None and session.search_seed is not None:
        return session.search_seed
    config = settings()
    return int(config['seed']) if config is not None else (0 if deterministic_order else rng.randrange(1 << 30))
