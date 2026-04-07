"""Randomization helpers extracted from the converter monolith."""

from __future__ import annotations

import os
import random
import time


def conversionRandomImpl(seed_env_var: str = "TINY_ICC_RANDOM_SEED") -> random.Random:
    """Return run-local RNG (seedable via env) for non-deterministic ordering."""
    seed_raw = os.environ.get(seed_env_var)
    if seed_raw is not None and str(seed_raw).strip() != "":
        try:
            return random.Random(int(str(seed_raw).strip()))
        except ValueError:
            pass
    return random.Random(time.time_ns())
