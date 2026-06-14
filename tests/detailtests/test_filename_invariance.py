from __future__ import annotations

import copy
import random
import string

import numpy as np

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime_helpers
from tools.filename_invariance import normalize_geometry_ir, normalize_svg_geometry


def _random_catalog_foreign_name(seed: int) -> str:
    randomizer = random.Random(seed)
    alphabet = string.ascii_lowercase
    return "holdout_" + "".join(randomizer.choice(alphabet) for _ in range(12))


def test_identical_pixels_and_description_are_filename_invariant(monkeypatch) -> None:
    description = "Kompressor grau nach oben"
    source_pixels = np.full((48, 48, 3), 173, dtype=np.uint8)
    names = [_random_catalog_foreign_name(41), _random_catalog_foreign_name(97)]
    snapshots: list[tuple[str, str, np.ndarray, float]] = []
    optimized_inputs: list[list[dict[str, object]]] = []

    monkeypatch.setattr(runtime_helpers, "_try_build_perception_seeded_geometry_ir_svg", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runtime_helpers, "_fit_symbol_element_by_element", lambda **_kwargs: None)
    def record_optimization_input(geometry_ir, *, render_fn, error_fn):
        optimized_inputs.append(copy.deepcopy(geometry_ir))
        return {
            "geometry_ir": copy.deepcopy(geometry_ir),
            "rendered": render_fn(geometry_ir),
            "initial_error": error_fn(render_fn(geometry_ir)),
            "final_error": error_fn(render_fn(geometry_ir)),
            "parameters": {},
            "element_refinement": {"steps": []},
        }

    monkeypatch.setattr(
        runtime_helpers.geometry_ir_optimizer,
        "optimizeGeometryIrRegistrationImpl",
        record_optimization_input,
    )

    for name in names:
        artifacts: list[tuple[str, np.ndarray]] = []
        params: dict[str, object] = {"mode": "non_composite"}

        result = runtime_helpers.runNonCompositeIterationImpl(
            mode="non_composite",
            params=params,
            stripe_strategy=None,
            semantic_mode_visual_override=False,
            width=48,
            height=48,
            base_name=name,
            image_variant_name=name,
            description=description,
            perc_img=source_pixels.copy(),
            img_path=f"/synthetic/{name}.png",
            print_fn=lambda *_args, **_kwargs: None,
            render_embedded_raster_svg_fn=lambda _path: "<svg/>",
            build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg/>",
            build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: [],
            write_validation_log_fn=lambda _lines: None,
            render_svg_to_numpy_fn=lambda _svg, width, height: np.full(
                (height, width, 3), 173, dtype=np.uint8
            ),
            record_render_failure_fn=lambda *_args, **_kwargs: None,
            write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered.copy())),
            calculate_error_fn=lambda target, rendered: float(
                np.square(target.astype(np.int16) - rendered.astype(np.int16)).sum()
            ),
        )

        assert result is not None
        assert artifacts
        svg, rendered = artifacts[-1]
        snapshots.append(
            (
                normalize_geometry_ir(optimized_inputs[-1]),
                normalize_svg_geometry(svg),
                rendered,
                result[-1],
            )
        )

    first_ir, first_svg, first_rendered, first_error = snapshots[0]
    second_ir, second_svg, second_rendered, second_error = snapshots[1]
    assert names[0] != names[1]
    assert first_ir == second_ir
    assert first_svg == second_svg
    assert np.array_equal(first_rendered, second_rendered)
    assert first_error == second_error == 0.0


def test_invariance_normalizers_ignore_only_output_metadata() -> None:
    geometry_ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kompressor grau nach oben")
    renamed_ir = copy.deepcopy(geometry_ir)
    renamed_ir[0]["variant_name"] = "neutral_name"
    renamed_ir[0]["timestamp"] = "2099-01-01T00:00:00Z"

    first_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" data-output-name="first">'
        "<title>first</title><circle cy=\"5\" cx=\"5\" r=\"4\"/></svg>"
    )
    second_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" data-output-name="second">'
        "<metadata>volatile</metadata><circle r=\"4\" cx=\"5\" cy=\"5\"/></svg>"
    )

    assert normalize_geometry_ir(geometry_ir) == normalize_geometry_ir(renamed_ir)
    assert normalize_svg_geometry(first_svg) == normalize_svg_geometry(second_svg)
