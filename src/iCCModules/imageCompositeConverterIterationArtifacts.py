"""Iteration artifact IO helpers extracted from the converter monolith."""

from __future__ import annotations

import os
import json
import numpy as np
import time
from pathlib import Path
from typing import Callable

from src.iCCModules import imageCompositeConverterDiffing as diffing_helpers


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
    # Validation logs are used as reproducibility evidence. Do not mix a
    # wall-clock nonce into the recorded run metadata: otherwise two identical
    # conversions differ in their first log line even when all effective
    # parameters are unchanged. Keep ``time_ns_fn`` in the signature for older
    # call sites/tests that inject it, but intentionally leave it unused.
    _ = time_ns_fn
    trace_id = int(run_seed) * 1009 + int(pass_seed_offset) * 101
    payload = [
        (
            "run-meta: "
            f"run_seed={int(run_seed)} "
            f"pass_seed_offset={int(pass_seed_offset)} "
            f"trace_id={trace_id}"
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
    commented_diff_out_dir: str | None = None,
    create_commented_diff: bool = True,
) -> None:
    suffix = "_failed" if failed else ""
    svg_path = os.path.join(svg_out_dir, f"{base_name}{suffix}.svg")
    with open(svg_path, "w", encoding="utf-8") as handle:
        handle.write(svg_content)

    # Failed attempts are tracked in logs/leaderboard but should not emit
    # additional diff artifacts.
    if failed:
        return

    render = (
        rendered_img
        if rendered_img is not None
        else render_svg_to_numpy_fn(svg_content)
    )
    if render is None:
        return

    diff = (
        diff_img if diff_img is not None else create_diff_image_fn(target_img, render)
    )
    cv2_module.imwrite(
        os.path.join(diff_out_dir, f"{base_name}{suffix}_diff.png"), diff
    )

    if (
        create_commented_diff
        and hasattr(target_img, "shape")
        and hasattr(render, "shape")
    ):
        comment_dir = (
            Path(commented_diff_out_dir)
            if commented_diff_out_dir
            else Path(diff_out_dir).parent / "commented_diff_images"
        )
        comment_dir.mkdir(parents=True, exist_ok=True)
        summary = diffing_helpers.diffPixelSummaryImpl(
            target_img, render, cv2_module=cv2_module, np_module=np
        )
        commented = diffing_helpers.createCommentedDiffImageImpl(
            diff,
            summary,
            cv2_module=cv2_module,
            np_module=np,
            title=f"{base_name}{suffix}: source vs converted render",
        )
        if commented is not None:
            cv2_module.imwrite(
                str(comment_dir / f"{base_name}{suffix}_commented_diff.png"), commented
            )


def paramsSnapshotImpl(snapshot: dict[str, object]) -> str:
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str)


def writeRenderFailureLogImpl(
    *,
    reason: str,
    filename: str,
    base_name: str,
    write_attempt_artifacts_fn: Callable[..., None],
    write_validation_log_fn: Callable[[list[str]], None],
    svg_content: str | None = None,
    params_snapshot: dict[str, object] | None = None,
    params_snapshot_serializer: Callable[[dict[str, object]], str] = paramsSnapshotImpl,
) -> None:
    if svg_content:
        write_attempt_artifacts_fn(svg_content, failed=True)
    lines = [
        "status=render_failure",
        f"failure_reason={reason}",
        f"filename={filename}",
    ]
    if svg_content:
        lines.append(f"best_attempt_svg={base_name}_failed.svg")
    if params_snapshot is not None:
        lines.append("params_snapshot=" + params_snapshot_serializer(params_snapshot))
    write_validation_log_fn(lines)
