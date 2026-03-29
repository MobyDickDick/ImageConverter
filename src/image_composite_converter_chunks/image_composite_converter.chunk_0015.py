        "cx": 12.654,
        "cy": 12.065,
        "r": 11.280,
        "stroke_width": 1.618,
        "fill_gray": 244,
        "stroke_gray": 171,
        "text_gray": 110,
        "tx": 6.249,
        "ty": 5.946,
        "s": 0.007665,
    }

    AC0870_BASE = {
        "cx": 15.0,
        "cy": 15.0,
        "r": 12.0,
        "stroke_width": 2.0,
        "fill_gray": 220,
        "stroke_gray": 152,
        "text_gray": 98,
        "label": "T",
    }

    LIGHT_CIRCLE_FILL_GRAY = 242
    # Einheitliche AC08xx-Grauwerte (entspricht #7F7F7F).
    LIGHT_CIRCLE_STROKE_GRAY = 127
    LIGHT_CIRCLE_TEXT_GRAY = 127

    # Global guardrail for text sizing in semantic badges.
    # Historical runs were deliberately conservative to avoid overscaling on
    # noisy rasters, but this can make converted labels consistently too small.
    # Keep a mild global uplift that applies across text modes.
    SEMANTIC_TEXT_BASE_SCALE = 1.08
    AC08_STROKE_WIDTH_PX = 1.0

    @staticmethod
    def grayhex(gray: int) -> str:
        g = max(0, min(255, int(round(gray))))
        return f"#{g:02x}{g:02x}{g:02x}"

    @staticmethod
    def _snap_half(value: float) -> float:
        return round(float(value) * 2.0) / 2.0

    @staticmethod
    def _clip_scalar(value: float, low: float, high: float) -> float:
        """Return value clamped to ``[low, high]`` with ``numpy.clip`` scalar semantics."""
        lo = float(low)
        hi = float(high)
        # Mirror numpy.clip behaviour for inverted bounds (a_min > a_max):
        # any scalar collapses to the supplied upper bound.
        if lo > hi:
            return hi
        v = float(value)
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v

    class _ScalarRng:
        def __init__(self, seed: int) -> None:
            self._rng = random.Random(int(seed))

        def uniform(self, low: float, high: float) -> float:
            return float(self._rng.uniform(float(low), float(high)))

        def normal(self, mean: float, sigma: float) -> float:
            return float(self._rng.gauss(float(mean), float(sigma)))

    @staticmethod
    def _make_rng(seed: int):
        if np is not None:
            return np.random.default_rng(int(seed))
        return Action._ScalarRng(int(seed))

    @staticmethod
    def _argmin_index(values: list[float]) -> int:
        return min(range(len(values)), key=lambda i: float(values[i]))

    @staticmethod
    def _snap_int_px(value: float, minimum: float = 1.0) -> float:
        return float(max(int(round(float(minimum))), int(round(float(value)))))

    @staticmethod
    def _max_circle_radius_inside_canvas(cx: float, cy: float, w: int, h: int, stroke: float = 0.0) -> float:
        """Return the largest circle radius that stays inside the SVG viewport."""
        if w <= 0 or h <= 0:
            return 1.0
        edge_margin = min(float(cx), float(w) - float(cx), float(cy), float(h) - float(cy))
        return float(max(1.0, edge_margin - (max(0.0, float(stroke)) / 2.0)))

    @staticmethod
    def _is_circle_with_text(params: dict) -> bool:
        """Return True when the badge encodes a circle-with-text shape."""
        return bool(params.get("circle_enabled", True)) and bool(params.get("draw_text", False))

    @staticmethod
    def _apply_circle_text_width_constraint(params: dict, radius: float, w: int) -> float:
        """Enforce CircleWithText constraint: 2 * radius < image width."""
