from __future__ import annotations

from dataclasses import dataclass

from src.iCCModules import imageCompositeConverterOptimizationGlobalSearch as helpers


class _Image:
    def __init__(self, h: int, w: int):
        self.shape = (h, w)


@dataclass(frozen=True)
class _Vector:
    cx: float
    cy: float
    r: float
    stem_x: float | None = None
    stem_width: float | None = None
    text_x: float | None = None
    text_y: float | None = None
    text_scale: float | None = None

    @staticmethod
    def fromParams(params: dict) -> "_Vector":
        return _Vector(
            cx=float(params["cx"]),
            cy=float(params["cy"]),
            r=float(params["r"]),
            stem_x=float(params["stem_x"]) if "stem_x" in params else None,
            stem_width=float(params["stem_width"]) if "stem_width" in params else None,
            text_x=float(params["text_x"]) if "text_x" in params else None,
            text_y=float(params["text_y"]) if "text_y" in params else None,
            text_scale=float(params["text_scale"]) if "text_scale" in params else None,
        )

    def applyToParams(self, params: dict) -> dict:
        out = dict(params)
        out.update(
            {
                "cx": float(self.cx),
                "cy": float(self.cy),
                "r": float(self.r),
            }
        )
        optional_values = {
            "stem_x": self.stem_x,
            "stem_width": self.stem_width,
            "text_x": self.text_x,
            "text_y": self.text_y,
            "text_scale": self.text_scale,
        }
        for key, value in optional_values.items():
            if value is not None:
                out[key] = float(value)
        return out

    def apply_to_params(self, params: dict) -> dict:
        return self.applyToParams(params)


def _bounds(_params: dict, _w: int, _h: int) -> dict:
    return {
        "cx": (0.0, 10.0, False, "test"),
        "cy": (0.0, 10.0, False, "test"),
        "r": (1.0, 8.0, False, "test"),
        "stem_x": (0.0, 10.0, False, "test"),
        "stem_width": (0.5, 5.0, False, "test"),
        "text_x": (0.0, 10.0, False, "test"),
        "text_y": (0.0, 10.0, False, "test"),
        "text_scale": (0.5, 3.0, True, "locked-test"),
    }


class _Rng:
    def normal(self, loc: float, _sigma: float) -> float:
        return loc


def test_full_badge_error_for_params_returns_inf_when_render_is_none() -> None:
    img = _Image(6, 6)

    result = helpers.fullBadgeErrorForParamsImpl(
        img,
        {"cx": 3.0},
        fit_to_original_size_fn=lambda _img_orig, _render: None,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg/>",
        calculate_error_fn=lambda _a, _b: 0.0,
    )

    assert result == float("inf")


def test_full_badge_error_for_params_uses_render_pipeline_result() -> None:
    img = _Image(4, 4)

    result = helpers.fullBadgeErrorForParamsImpl(
        img,
        {"cx": 2.0},
        fit_to_original_size_fn=lambda _img_orig, render: render,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: {"render": "ok"},
        generate_badge_svg_fn=lambda w, h, params: f"<svg w='{w}' h='{h}' cx='{params['cx']}'/>",
        calculate_error_fn=lambda _a, b: 1.0 if b == {"render": "ok"} else 5.0,
    )

    assert result == 1.0


def test_global_search_skips_when_less_than_two_parameters_are_active() -> None:
    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 3.0,
    }

    def bounds_only_one_active(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (0.0, 10.0, False, "test"),
            "cy": (0.0, 10.0, True, "test"),
            "r": (1.0, 8.0, True, "test"),
            "stem_x": (0.0, 10.0, True, "test"),
            "stem_width": (0.5, 5.0, True, "test"),
            "text_x": (0.0, 10.0, True, "test"),
            "text_y": (0.0, 10.0, True, "test"),
            "text_scale": (0.5, 3.0, True, "test"),
        }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=1,
        samples_per_round=1,
        global_parameter_vector_cls=_Vector,
        global_parameter_vector_bounds_fn=bounds_only_one_active,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _Rng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, _probe: 1.0,
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is False
    assert any("benötigt >=2" in line for line in logs)


def test_global_search_logs_reduced_mode_for_two_or_three_active_parameters() -> None:
    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 3.0,
        "text_scale": 1.0,
    }

    helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=1,
        samples_per_round=1,
        global_parameter_vector_cls=_Vector,
        global_parameter_vector_bounds_fn=_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _Rng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, _probe: 1.0,
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert any("modus=reduziert" in line for line in logs)
