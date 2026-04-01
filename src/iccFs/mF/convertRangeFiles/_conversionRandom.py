def conversionRandom() -> random.Random:
    """Return run-local RNG (seedable via env) for non-deterministic search order."""
    seed_raw = os.environ.get("TINY_ICC_RANDOM_SEED")
    if seed_raw is not None and str(seed_raw).strip() != "":
        try:
            return random.Random(int(str(seed_raw).strip()))
        except ValueError:
            pass
    return random.Random(time.time_ns())
