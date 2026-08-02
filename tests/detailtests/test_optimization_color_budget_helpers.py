from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterOptimizationColor as helpers


def test_color_bracketing_stops_before_candidate_render_when_deadline_expired(monkeypatch) -> None:
    logs: list[str] = []
    renders: list[int] = []
    params = {
        "circle_enabled": True,
        "fill_gray": 128,
        "_optimization_deadline_monotonic": 4.0,
    }
    monkeypatch.setattr(helpers.time, "monotonic", lambda: 4.0)

    changed = helpers.optimizeElementColorBracketImpl(
        np.zeros((2, 2, 3), dtype=np.uint8),
        params,
        "circle",
        np.ones((2, 2), dtype=np.uint8),
        logs,
        mean_gray_for_mask_fn=lambda *_args: 128.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        element_color_keys_fn=lambda *_args: ["fill_gray"],
        element_error_for_color_fn=lambda _img, _params, _element, _key, value, _mask: renders.append(value) or 1.0,
        argmin_index_fn=lambda _values: 0,
        stochastic_survivor_scalar_fn=lambda *_args, **_kwargs: (128.0, 1.0, False),
    )

    assert changed is False
    assert renders == []
    assert any("Validierungszeitbudget ausgeschöpft" in line for line in logs)
