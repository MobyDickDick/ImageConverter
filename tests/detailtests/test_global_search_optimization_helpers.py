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


def test_global_search_logs_evaluate_telemetry_when_no_improvement() -> None:
    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 3.0,
    }

    helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=1,
        samples_per_round=2,
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

    assert any("evaluate-telemetrie" in line for line in logs)


def test_global_search_caches_duplicate_evaluations() -> None:
    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 3.0,
    }
    render_calls = 0

    def _full_badge_error(_img, _probe):
        nonlocal render_calls
        render_calls += 1
        return 1.0

    helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=1,
        samples_per_round=5,
        global_parameter_vector_cls=_Vector,
        global_parameter_vector_bounds_fn=_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _Rng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=_full_badge_error,
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    telemetry_line = next(line for line in logs if "evaluate-telemetrie" in line)
    assert "cache_hits=" in telemetry_line
    requests = int(telemetry_line.split("requests=")[1].split(",")[0])
    cache_hits = int(telemetry_line.split("cache_hits=")[1].split(",")[0])
    assert cache_hits > 0
    assert render_calls < requests


def test_global_search_reuses_cache_across_invocations_for_same_image() -> None:
    helpers._CROSS_ROUND_EVAL_CACHE.clear()
    img = _Image(10, 10)
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 3.0,
    }
    render_calls = 0

    def _full_badge_error(_img, _probe):
        nonlocal render_calls
        render_calls += 1
        return 1.0

    helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        dict(params),
        [],
        rounds=1,
        samples_per_round=5,
        global_parameter_vector_cls=_Vector,
        global_parameter_vector_bounds_fn=_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _Rng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=_full_badge_error,
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: None,
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )
    calls_after_first_run = render_calls
    helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        dict(params),
        [],
        rounds=1,
        samples_per_round=5,
        global_parameter_vector_cls=_Vector,
        global_parameter_vector_bounds_fn=_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _Rng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=_full_badge_error,
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: None,
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert calls_after_first_run > 1
    assert render_calls == calls_after_first_run


def test_global_search_can_improve_error_by_varying_arm_x1() -> None:
    @dataclass(frozen=True)
    class _ArmVector:
        cx: float
        cy: float
        r: float
        arm_x1: float
        text_x: float
        text_y: float

        @staticmethod
        def fromParams(params: dict) -> "_ArmVector":
            return _ArmVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                arm_x1=float(params["arm_x1"]),
                text_x=float(params["text_x"]),
                text_y=float(params["text_y"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "arm_x1": float(self.arm_x1),
                    "text_x": float(self.text_x),
                    "text_y": float(self.text_y),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 7.0

    def _arm_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "arm_x1": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "arm_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "arm_x1": 1.0,
        "text_x": 2.0,
        "text_y": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_ArmVector,
        global_parameter_vector_bounds_fn=_arm_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["arm_x1"]) - 7.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["arm_x1"]) == 7.0
    assert any("arm_x1 1.000->7.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_arm_y1() -> None:
    @dataclass(frozen=True)
    class _ArmVector:
        cx: float
        cy: float
        r: float
        arm_y1: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_ArmVector":
            return _ArmVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                arm_y1=float(params["arm_y1"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "arm_y1": float(self.arm_y1),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 8.0

    def _arm_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "arm_y1": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "arm_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "arm_y1": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_ArmVector,
        global_parameter_vector_bounds_fn=_arm_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["arm_y1"]) - 8.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["arm_y1"]) == 8.0
    assert any("arm_y1 1.000->8.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_arm_x2() -> None:
    @dataclass(frozen=True)
    class _ArmVector:
        cx: float
        cy: float
        r: float
        arm_x2: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_ArmVector":
            return _ArmVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                arm_x2=float(params["arm_x2"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "arm_x2": float(self.arm_x2),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 9.0

    def _arm_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "arm_x2": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "arm_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "arm_x2": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_ArmVector,
        global_parameter_vector_bounds_fn=_arm_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["arm_x2"]) - 9.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["arm_x2"]) == 9.0
    assert any("arm_x2 1.000->9.000" in line for line in logs)


def test_global_search_skips_deterministic_track_after_strong_stochastic_gain() -> None:
    @dataclass(frozen=True)
    class _ArmVector:
        cx: float
        cy: float
        r: float
        arm_x1: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_ArmVector":
            return _ArmVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                arm_x1=float(params["arm_x1"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "arm_x1": float(self.arm_x1),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 7.0

    def _arm_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "arm_x1": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "arm_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "arm_x1": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=3,
        samples_per_round=3,
        global_parameter_vector_cls=_ArmVector,
        global_parameter_vector_bounds_fn=_arm_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["arm_x1"]) - 7.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["arm_x1"]) == 7.0
    assert any("deterministischer track übersprungen" in line for line in logs)


def test_global_search_does_not_count_small_relevant_gain_as_no_improvement() -> None:
    @dataclass(frozen=True)
    class _ArmVector:
        cx: float
        cy: float
        r: float
        arm_x1: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_ArmVector":
            return _ArmVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                arm_x1=float(params["arm_x1"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "arm_x1": float(self.arm_x1),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _SmallGainRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return loc + 0.02

    def _arm_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "arm_x1": (1.0, 2.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "arm_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "arm_x1": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=6,
        samples_per_round=3,
        global_parameter_vector_cls=_ArmVector,
        global_parameter_vector_bounds_fn=_arm_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: value,
        make_rng_fn=lambda _seed: _SmallGainRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["arm_x1"]) - 1.20),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["arm_x1"]) >= 1.10
    assert not any("frühabbruch" in line for line in logs)


def test_global_search_can_improve_error_by_varying_arm_y2() -> None:
    @dataclass(frozen=True)
    class _ArmVector:
        cx: float
        cy: float
        r: float
        arm_y2: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_ArmVector":
            return _ArmVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                arm_y2=float(params["arm_y2"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "arm_y2": float(self.arm_y2),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 7.0

    def _arm_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "arm_y2": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "arm_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "arm_y2": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_ArmVector,
        global_parameter_vector_bounds_fn=_arm_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["arm_y2"]) - 7.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["arm_y2"]) == 7.0
    assert any("arm_y2 1.000->7.000" in line for line in logs)



def test_global_search_can_improve_error_by_varying_arm_stroke() -> None:
    @dataclass(frozen=True)
    class _ArmVector:
        cx: float
        cy: float
        r: float
        arm_stroke: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_ArmVector":
            return _ArmVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                arm_stroke=float(params["arm_stroke"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "arm_stroke": float(self.arm_stroke),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 4.0

    def _arm_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "arm_stroke": (1.0, 6.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "arm_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "arm_stroke": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_ArmVector,
        global_parameter_vector_bounds_fn=_arm_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["arm_stroke"]) - 4.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["arm_stroke"]) == 4.0
    assert any("arm_stroke 1.000->4.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_stem_x() -> None:
    @dataclass(frozen=True)
    class _StemVector:
        cx: float
        cy: float
        r: float
        stem_x: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_StemVector":
            return _StemVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                stem_x=float(params["stem_x"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "stem_x": float(self.stem_x),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 7.0

    def _stem_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "stem_x": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "stem_enabled": True,
        "lock_stem_center_to_circle": False,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "stem_x": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_StemVector,
        global_parameter_vector_bounds_fn=_stem_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["stem_x"]) - 7.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["stem_x"]) == 7.0
    assert any("stem_x 1.000->7.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_stem_top() -> None:
    @dataclass(frozen=True)
    class _StemVector:
        cx: float
        cy: float
        r: float
        stem_top: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_StemVector":
            return _StemVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                stem_top=float(params["stem_top"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "stem_top": float(self.stem_top),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 8.0

    def _stem_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "stem_top": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "stem_enabled": True,
        "lock_stem_center_to_circle": False,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "stem_top": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_StemVector,
        global_parameter_vector_bounds_fn=_stem_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["stem_top"]) - 8.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["stem_top"]) == 8.0
    assert any("stem_top 1.000->8.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_stem_bottom() -> None:
    @dataclass(frozen=True)
    class _StemVector:
        cx: float
        cy: float
        r: float
        stem_bottom: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_StemVector":
            return _StemVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                stem_bottom=float(params["stem_bottom"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "stem_bottom": float(self.stem_bottom),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 8.0

    def _stem_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "stem_bottom": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "stem_enabled": True,
        "lock_stem_center_to_circle": False,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "stem_bottom": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_StemVector,
        global_parameter_vector_bounds_fn=_stem_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["stem_bottom"]) - 8.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["stem_bottom"]) == 8.0
    assert any("stem_bottom 1.000->8.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_stem_width() -> None:
    @dataclass(frozen=True)
    class _StemVector:
        cx: float
        cy: float
        r: float
        stem_x: float
        stem_width: float
        text_x: float

        @staticmethod
        def fromParams(params: dict) -> "_StemVector":
            return _StemVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                stem_x=float(params["stem_x"]),
                stem_width=float(params["stem_width"]),
                text_x=float(params["text_x"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "stem_x": float(self.stem_x),
                    "stem_width": float(self.stem_width),
                    "text_x": float(self.text_x),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 8.0

    def _stem_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "stem_x": (0.0, 10.0, False, "test"),
            "stem_width": (0.0, 10.0, False, "test"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "stem_enabled": True,
        "lock_stem_center_to_circle": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "stem_x": 4.0,
        "stem_width": 1.0,
        "text_x": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_StemVector,
        global_parameter_vector_bounds_fn=_stem_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["stem_width"]) - 8.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["stem_width"]) == 8.0
    assert any("stem_width 1.000->8.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_text_x() -> None:
    @dataclass(frozen=True)
    class _TextVector:
        cx: float
        cy: float
        r: float
        text_x: float
        text_y: float

        @staticmethod
        def fromParams(params: dict) -> "_TextVector":
            return _TextVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                text_x=float(params["text_x"]),
                text_y=float(params["text_y"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "text_x": float(self.text_x),
                    "text_y": float(self.text_y),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 9.0

    def _text_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "text_x": (0.0, 10.0, False, "test"),
            "text_y": (2.0, 2.0, False, "fixed-secondary-dimension"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "text_x": 1.0,
        "text_y": 2.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_TextVector,
        global_parameter_vector_bounds_fn=_text_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["text_x"]) - 9.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["text_x"]) == 9.0
    assert any("text_x 1.000->9.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_text_y() -> None:
    @dataclass(frozen=True)
    class _TextVector:
        cx: float
        cy: float
        r: float
        text_x: float
        text_y: float

        @staticmethod
        def fromParams(params: dict) -> "_TextVector":
            return _TextVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                text_x=float(params["text_x"]),
                text_y=float(params["text_y"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "text_x": float(self.text_x),
                    "text_y": float(self.text_y),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            return 8.0

    def _text_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "text_x": (2.0, 2.0, False, "fixed-secondary-dimension"),
            "text_y": (0.0, 10.0, False, "test"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "text_x": 2.0,
        "text_y": 1.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_TextVector,
        global_parameter_vector_bounds_fn=_text_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["text_y"]) - 8.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["text_y"]) == 8.0
    assert any("text_y 1.000->8.000" in line for line in logs)


def test_global_search_can_improve_error_by_varying_text_scale() -> None:
    @dataclass(frozen=True)
    class _TextVector:
        cx: float
        cy: float
        r: float
        text_x: float
        text_y: float
        text_scale: float

        @staticmethod
        def fromParams(params: dict) -> "_TextVector":
            return _TextVector(
                cx=float(params["cx"]),
                cy=float(params["cy"]),
                r=float(params["r"]),
                text_x=float(params["text_x"]),
                text_y=float(params["text_y"]),
                text_scale=float(params["text_scale"]),
            )

        def applyToParams(self, params: dict) -> dict:
            out = dict(params)
            out.update(
                {
                    "cx": float(self.cx),
                    "cy": float(self.cy),
                    "r": float(self.r),
                    "text_x": float(self.text_x),
                    "text_y": float(self.text_y),
                    "text_scale": float(self.text_scale),
                }
            )
            return out

        def apply_to_params(self, params: dict) -> dict:
            return self.applyToParams(params)

    class _TargetRng:
        def normal(self, loc: float, _sigma: float) -> float:
            if abs(loc - 2.0) < 1e-6:
                return loc
            if abs(loc - 5.0) < 1e-6:
                return loc
            return 3.0

    def _text_bounds(_params: dict, _w: int, _h: int) -> dict:
        return {
            "cx": (5.0, 5.0, True, "locked"),
            "cy": (5.0, 5.0, True, "locked"),
            "r": (2.0, 2.0, True, "locked"),
            "text_x": (5.0, 5.0, False, "fixed-secondary-dimension"),
            "text_y": (2.0, 2.0, False, "fixed-secondary-dimension"),
            "text_scale": (0.5, 3.0, False, "test"),
        }

    img = _Image(10, 10)
    logs: list[str] = []
    params = {
        "enable_global_search_mode": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "draw_text": True,
        "text_x": 5.0,
        "text_y": 2.0,
        "text_scale": 1.0,
    }

    improved = helpers.optimizeGlobalParameterVectorSamplingImpl(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=3,
        global_parameter_vector_cls=_TextVector,
        global_parameter_vector_bounds_fn=_text_bounds,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, value)),
        snap_half_fn=lambda value: round(value * 2.0) / 2.0,
        make_rng_fn=lambda _seed: _TargetRng(),
        reanchor_arm_to_circle_edge_fn=lambda _probe, _r: None,
        full_badge_error_for_params_fn=lambda _img, probe: abs(float(probe["text_scale"]) - 3.0),
        log_global_parameter_vector_fn=lambda _logs, _params, _w, _h, label: _logs.append(label),
        stochastic_run_seed=0,
        stochastic_seed_offset=0,
    )

    assert improved is True
    assert float(params["text_scale"]) == 3.0
    assert any("text_scale 1.000->3.000" in line for line in logs)
