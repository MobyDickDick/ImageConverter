from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterIterationArtifacts as helpers


class _Cv2Stub:
    def __init__(self):
        self.calls = []

    def imwrite(self, path, data):
        self.calls.append((path, data))
        return True


def test_write_validation_log_writes_meta_and_lines(tmp_path: Path):
    log_path = tmp_path / "test.log"

    helpers.writeValidationLogImpl(
        log_path=str(log_path),
        lines=["status=ok", "foo=bar"],
        run_seed=7,
        pass_seed_offset=11,
        time_ns_fn=lambda: 123456789,
    )

    content = log_path.read_text(encoding="utf-8")
    assert "run-meta: run_seed=7 pass_seed_offset=11 nonce_ns=123456789" in content
    assert "status=ok" in content
    assert content.endswith("\n")


def test_write_attempt_artifacts_failed_only_writes_svg(tmp_path: Path):
    cv2_stub = _Cv2Stub()

    helpers.writeAttemptArtifactsImpl(
        svg_out_dir=str(tmp_path),
        diff_out_dir=str(tmp_path),
        base_name="AC0800_S",
        svg_content="<svg/>",
        target_img="target",
        render_svg_to_numpy_fn=lambda _svg: "rendered",
        create_diff_image_fn=lambda _target, _render: "diff",
        cv2_module=cv2_stub,
        failed=True,
    )

    assert (tmp_path / "AC0800_S_failed.svg").read_text(encoding="utf-8") == "<svg/>"
    assert cv2_stub.calls == []


def test_write_attempt_artifacts_renders_and_writes_diff(tmp_path: Path):
    cv2_stub = _Cv2Stub()

    helpers.writeAttemptArtifactsImpl(
        svg_out_dir=str(tmp_path),
        diff_out_dir=str(tmp_path),
        base_name="AC0800_M",
        svg_content="<svg/>",
        target_img="target-image",
        render_svg_to_numpy_fn=lambda _svg: "rendered-image",
        create_diff_image_fn=lambda target, render: f"diff:{target}:{render}",
        cv2_module=cv2_stub,
        failed=False,
    )

    assert (tmp_path / "AC0800_M.svg").read_text(encoding="utf-8") == "<svg/>"
    assert cv2_stub.calls == [
        (str(tmp_path / "AC0800_M_diff.png"), "diff:target-image:rendered-image")
    ]
