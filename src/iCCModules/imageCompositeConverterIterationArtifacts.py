"""Iteration artifact IO helpers extracted from the converter monolith."""

from __future__ import annotations

import os
import time
from typing import Callable


def writeValidationLogImpl(
    *,
    log_path: str | None,
    lines: list[str],
    run_seed: int,
    pass_seed_offset: int,
    time_ns_fn: Callable[[], int] = time.time_ns,
) -> None:
    if not log_path:
        return
    payload = [
        (
            "run-meta: "
            f"run_seed={int(run_seed)} "
            f"pass_seed_offset={int(pass_seed_offset)} "
            f"nonce_ns={time_ns_fn()}"
        )
    ]
    payload.extend(str(line) for line in lines)
    with open(log_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(payload).rstrip() + "\n")


def writeAttemptArtifactsImpl(
    *,
    svg_out_dir: str,
    diff_out_dir: str,
    base_name: str,
    svg_content: str,
    target_img,
    render_svg_to_numpy_fn: Callable[[str], object],
    create_diff_image_fn: Callable[[object, object], object],
    cv2_module,
    rendered_img=None,
    diff_img=None,
    failed: bool = False,
) -> None:
    suffix = "_failed" if failed else ""
    svg_path = os.path.join(svg_out_dir, f"{base_name}{suffix}.svg")
    with open(svg_path, "w", encoding="utf-8") as handle:
        handle.write(svg_content)

    # Failed attempts are tracked in logs/leaderboard but should not emit
    # additional diff artifacts.
    if failed:
        return

    render = rendered_img if rendered_img is not None else render_svg_to_numpy_fn(svg_content)
    if render is None:
        return

    diff = diff_img if diff_img is not None else create_diff_image_fn(target_img, render)
    cv2_module.imwrite(os.path.join(diff_out_dir, f"{base_name}{suffix}_diff.png"), diff)
