"""Check the original conversion before accepting 16 seeded Plan-B variations."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_quality_complexity_gate import analyze_svg_complexity
from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl

CASE_COUNT = 16
MAX_ADDITIONAL_SVGS = 8
REQUIRED_COUNT = CASE_COUNT + 1  # Original plus all variations.
DEFAULT_SVG_DIR = ROOT / "artifacts/images_to_convert/samples"
DEFAULT_DESCRIPTIONS = ROOT / "artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"
# Frozen before conversion. No historical scores or batch success labels are used.
LIMITS = {"max_normalized_mse": 0.01, "max_foreground_mse": 0.04,
          "min_edge_alignment": 0.72, "min_foreground_iou": 0.85,
          "max_svg_elements": 80, "max_path_commands": 160}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def forbidden_vector_read(path, mode, flags, conversion_dir: Path) -> bool:
    """Only this case's own generated vectors may be read by the converter."""
    if not isinstance(path, (str, bytes, os.PathLike)):
        return False
    candidate = Path(os.fsdecode(path)).resolve()
    reads = ("r" in mode or "+" in mode) if isinstance(mode, str) else (flags & (os.O_WRONLY | os.O_RDWR)) != os.O_WRONLY
    return reads and candidate.suffix.lower() == ".svg" and not candidate.is_relative_to(conversion_dir.resolve())


def converter_worker(argv: list[str]) -> int:
    conversion_dir, cli_args = Path(argv[0]).resolve(), argv[1:]
    blocked = []
    def audit(event, args):
        if event == "open" and forbidden_vector_read(*args, conversion_dir):
            blocked.append(os.fsdecode(args[0]))
            raise PermissionError("Plan-B acceptance forbids reading reference SVGs")
    sys.addaudithook(audit)
    try:
        from src.iCCModules.imageCompositeConverterCli import main as convert
        return convert(cli_args)
    finally:
        (conversion_dir.parent / "reference_access.json").write_text(
            json.dumps({"blocked_svg_reads": blocked}, indent=2) + "\n", encoding="utf-8")


class TaskPoolExhausted(ValueError):
    """Every SVG/description pair in the pool has already been attempted."""


def select_task(svg_dir: Path, descriptions_path: Path, seed: int, *,
                excluded_svg_paths: set[Path] | None = None) -> tuple[Path, str, dict]:
    """Select anew on every invocation from all SVGs with an associated description."""
    mapping = loadDescriptionMappingImpl(str(descriptions_path), get_base_name_from_file_fn=getBaseNameFromFileImpl)
    pairs, excluded = [], []
    for path in sorted(svg_dir.rglob("*.svg")):
        # A sidecar is useful for arbitrary new Plan-B tasks outside the catalog.
        sidecar = path.with_suffix(".txt")
        key = path.stem.removesuffix("_PlanB")
        description = sidecar.read_text(encoding="utf-8").strip() if sidecar.exists() else (
            mapping.get(key) or mapping.get(key.upper()) or mapping.get(getBaseNameFromFileImpl(key)) or "").strip()
        if not description:
            excluded.append({"svg": str(path.resolve()), "reason": "missing_description"})
            continue
        pairs.append((path.resolve(), description))
    if not pairs:
        raise ValueError("No SVG/description pairs found in the selected pool")
    attempted = {path.resolve() for path in (excluded_svg_paths or set())}
    remaining = [index for index, pair in enumerate(pairs) if pair[0] not in attempted]
    if not remaining:
        raise TaskPoolExhausted("No untried SVG/description pairs remain in the selected pool")
    index = remaining[random.Random(seed).randrange(len(remaining))]
    svg_path, description = pairs[index]
    return svg_path, description, {"mode": "random_pool", "selected_index": index,
                                   "pool_size": len(pairs), "remaining_pool_size": len(remaining),
                                   "source_svg": str(svg_path),
                                   "descriptions_path": str(descriptions_path.resolve()),
                                   "pool": [str(p[0]) for p in pairs], "excluded": excluded}


def render(svg: str, width: int, height: int):
    np = import_with_vendored_fallback("numpy")
    cv2 = import_with_vendored_fallback("cv2")
    fitz = import_with_vendored_fallback("fitz")
    raster = render_svg_to_numpy_inprocess(
        svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)
    if raster is None:
        raise ValueError("SVG could not be rendered")
    return raster


def viewport(svg: str) -> tuple[float, float, float, float, int, int]:
    fitz = import_with_vendored_fallback("fitz")
    root = ET.fromstring(svg)
    if local_name(root.tag) != "svg":
        raise ValueError("Input must be an SVG document")
    with fitz.open(stream=svg.encode("utf-8"), filetype="svg") as doc:
        width, height = math.ceil(doc[0].rect.width), math.ceil(doc[0].rect.height)
    values = root.get("viewBox", f"0 0 {width} {height}").replace(",", " ").split()
    if len(values) != 4:
        raise ValueError("Invalid SVG viewBox")
    x, y, w, h = map(float, values)
    if not all(math.isfinite(v) for v in (x, y, w, h)) or min(w, h, width, height) <= 0:
        raise ValueError("SVG dimensions must be finite and positive")
    return x, y, w, h, width, height


def make_original_case(svg: str, description: str) -> dict:
    """The unchanged source is both the prerequisite and the first acceptance case."""
    if not description.strip():
        raise ValueError("A nonempty description is required")
    _, _, _, _, width, height = viewport(svg)
    complexity = analyze_svg_complexity(svg)
    if complexity["embedded_raster_count"] or not complexity["vector_element_count"]:
        raise ValueError("Reference must contain vectors and no embedded raster")
    return {"case_id": "original", "width": width, "height": height,
            "variation": {"scale": 1.0, "relative_x": 0.0, "relative_y": 0.0},
            "svg": svg, "description": description}


def make_variations(svg: str, description: str, seed: int) -> list[dict]:
    """Change geometry and wording together; never expose numeric geometry in text."""
    make_original_case(svg, description)
    x, y, w, h, width, height = viewport(svg)
    original = ET.fromstring(svg)
    rng = random.Random(seed)
    namespace = original.tag[:-3]  # preserve both namespaced and plain SVGs
    if namespace:
        ET.register_namespace("", namespace[1:-1])
    cases = []
    for index in range(CASE_COUNT):
        scale = round(rng.uniform(0.94, 1.06), 8)
        dx, dy = (round(rng.uniform(-0.025, 0.025), 8) for _ in range(2))
        varied = copy.deepcopy(original)
        group = ET.Element(namespace + "g", transform=(
            f"translate({dx*w:.8f} {dy*h:.8f}) "
            f"translate({x+w/2:.8f} {y+h/2:.8f}) scale({scale:.8f}) "
            f"translate({-x-w/2:.8f} {-y-h/2:.8f})"))
        # Definitions and CSS stay in their original scope; drawing order is preserved.
        for child in list(varied):
            if local_name(child.tag) not in {"defs", "style", "metadata", "title", "desc"}:
                varied.remove(child)
                group.append(child)
        varied.append(group)
        size = "kleiner" if scale < 1 else "größer"
        horizontal, vertical = ("links" if dx < 0 else "rechts"), ("oben" if dy < 0 else "unten")
        # Vary wording without dropping/reversing any facts in the original description.
        existing_descriptions = {case["description"] for case in cases}
        while True:
            subject = rng.choice(("Das gesamte Motiv", "Das Motiv", "Die gesamte Darstellung", "Die Darstellung"))
            extent = rng.choice(("geringfügig", "etwas", "ein wenig", "leicht"))
            position = rng.choice(("leicht", "geringfügig", "ein wenig", "etwas"))
            verb = rng.choice(("versetzt", "verschoben"))
            varied_description = (f"{description.strip()} {subject} ist {extent} {size} dargestellt "
                                  f"und {position} nach {horizontal} und {vertical} {verb}.")
            if varied_description not in existing_descriptions:
                break
        cases.append({"case_id": f"probe_{index+1:02d}", "width": width, "height": height,
                      "variation": {"scale": scale, "relative_x": dx, "relative_y": dy},
                      "svg": ET.tostring(varied, encoding="unicode"),
                      "description": varied_description})
    if len({case["svg"] for case in cases}) != CASE_COUNT:
        raise ValueError("Variations are not unique")
    return cases


def measure_quality(reference, svg: str, limits: dict | None = None) -> dict:
    """Independent raster checks; foreground checks stop white backgrounds hiding errors."""
    np = import_with_vendored_fallback("numpy")
    cv2 = import_with_vendored_fallback("cv2")
    limits = dict(LIMITS if limits is None else limits)
    complexity = analyze_svg_complexity(svg)
    failures = []
    if complexity["parse_error"]:
        return {"satisfactory": False, "failures": ["invalid_svg"], "metrics": {}, "limits": limits}
    if local_name(ET.fromstring(svg).tag) != "svg":
        return {"satisfactory": False, "failures": ["invalid_svg_root"], "metrics": {}, "limits": limits}
    if complexity["embedded_raster_count"]:
        failures.append("embedded_raster")
    if not complexity["vector_element_count"]:
        failures.append("no_vectors")
    if complexity["vector_element_count"] > limits["max_svg_elements"]:
        failures.append("excessive_svg_elements")
    if complexity["path_command_count"] > limits["max_path_commands"]:
        failures.append("excessive_path_commands")
    height, width = reference.shape[:2]
    # Check intrinsic dimensions before rendering; resizing must not mask a wrong canvas.
    _, _, _, _, out_width, out_height = viewport(svg)
    if (width, height) != (out_width, out_height):
        failures.append("dimension_mismatch")
    output = render(svg, width, height)
    error = np.square(reference.astype(np.float32) - output.astype(np.float32)).mean(axis=2) / 255**2
    # Estimate background from border pixels, allowing non-white input SVGs.
    border = np.concatenate((reference[0], reference[-1], reference[:, 0], reference[:, -1]))
    background = np.median(border.astype(np.float32), axis=0)
    ref_mask = np.max(np.abs(reference.astype(np.float32) - background), axis=2) > 25
    out_mask = np.max(np.abs(output.astype(np.float32) - background), axis=2) > 25
    union = ref_mask | out_mask
    iou = float(np.count_nonzero(ref_mask & out_mask) / np.count_nonzero(union)) if union.any() else 1.0
    foreground_mse = float(error[union].mean()) if union.any() else float(error.mean())
    a, b = cv2.Canny(reference, 50, 140) > 0, cv2.Canny(output, 50, 140) > 0
    if a.any() and b.any():
        forward = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 3)
        backward = cv2.distanceTransform((~a).astype(np.uint8), cv2.DIST_L2, 3)
        edge = float((np.exp(-forward[a]).mean() + np.exp(-backward[b]).mean()) / 2)
    else:
        edge = float(not a.any() and not b.any())
    metrics = {"normalized_mse": float(error.mean()), "foreground_mse": foreground_mse,
               "edge_alignment": edge, "foreground_iou": iou}
    checks = (("normalized_mse", "max_normalized_mse", False),
              ("foreground_mse", "max_foreground_mse", False),
              ("edge_alignment", "min_edge_alignment", True),
              ("foreground_iou", "min_foreground_iou", True))
    for metric, limit, higher in checks:
        value = metrics[metric]
        if not math.isfinite(value) or (value < limits[limit] if higher else value > limits[limit]):
            failures.append(metric + "_outside_limit")
    return {"satisfactory": not failures, "failures": failures,
            "metrics": metrics, "limits": limits, "complexity": complexity}


def prepare_cases(svg: str, description: str, output: Path, seed: int) -> list[dict]:
    # Validate/generate before creating the directory, and never reuse stale output.
    cases = make_variations(svg, description, seed)
    output.mkdir(parents=True, exist_ok=False)
    write_cases(cases, output)
    return cases


def write_cases(cases: list[dict], output: Path) -> None:
    """Write cases inside a fresh run directory already owned by this runner."""
    cv2 = import_with_vendored_fallback("cv2")
    references = output / "references"
    references.mkdir(exist_ok=True)
    raster_hashes = set()
    for case in cases:
        name = case["case_id"]
        source = references / (name + ".svg")
        source.write_text(case.pop("svg"), encoding="utf-8")
        case_dir = output / name
        inputs = case_dir / "input"
        inputs.mkdir(parents=True)
        image = render(source.read_text(encoding="utf-8"), case["width"], case["height"])
        digest = sha256(image.tobytes())
        if digest in raster_hashes:
            raise ValueError("Duplicate raster variation; choose a larger reference SVG or a different seed")
        raster_hashes.add(digest)
        image_path = inputs / (name + ".png")
        if not cv2.imwrite(str(image_path), image):
            raise ValueError("Could not save raster input")
        description_root = ET.Element("root")
        entry = ET.SubElement(description_root, "entry", kind="wurzelform", key=name)
        ET.SubElement(entry, "beschreibung").text = case["description"]
        ET.SubElement(ET.SubElement(entry, "bilder"), "bild").text = image_path.name
        ET.ElementTree(description_root).write(inputs / "descriptions.xml", encoding="utf-8", xml_declaration=True)
        case.update(reference_svg=str(source.relative_to(output)), input_sha256=sha256(image_path.read_bytes()),
                    reference_svg_sha256=sha256(source.read_bytes()))


def run_case(case: dict, output: Path, *, timeout: float, iterations: int,
             keep_debug_artifacts: bool = True) -> dict:
    cv2 = import_with_vendored_fallback("cv2")
    np = import_with_vendored_fallback("numpy")
    fitz = import_with_vendored_fallback("fitz")
    from PIL import Image
    name = case["case_id"]
    case_dir = output / name
    inputs = case_dir / "input"
    reference = cv2.imread(str(inputs / (name + ".png")))
    # Keep the parent's imported binary toolchain even when repository startup
    # discovers an old virtualenv built for a different Python ABI.
    dependency_paths = list(dict.fromkeys(str(Path(module.__file__).resolve().parents[1])
                                         for module in (np, cv2, fitz, Image)))
    worker_paths = [*dependency_paths, str(ROOT), *sys.path]
    bootstrap = ('import sys, runpy; sys.path[:0] = ' + repr(worker_paths)
                 + "; import numpy, cv2, fitz; from PIL import Image; "
                 + "runpy.run_module('tools.run_plan_b_variations', run_name='__main__')")
    command = [sys.executable, "-I", "-c", bootstrap, "--_worker",
               str(case_dir / "conversion"), str(inputs),
               "--descriptions-path", str(inputs / "descriptions.xml"),
               "--output-dir", str(case_dir / "conversion"), "--start", name, "--end", name,
               "--execution-mode", "semantic-only", "--deterministic-order", "--iterations", str(iterations)]
    environment = dict(os.environ, TINY_ICC_OUTPUT_VARIATION="0", PYTHONHASHSEED="0",
                       ICC_FORCE_RECONVERT="1", PYTHONIOENCODING="utf-8")
    environment["PYTHONPATH"] = os.pathsep.join([str(ROOT), *sys.path])
    result = {**case, "satisfactory": False, "failures": [], "command": command}
    started = time.monotonic()
    try:
        with (case_dir / "converter.log").open("w", encoding="utf-8") as log:
            completed = subprocess.run(command, cwd=ROOT, env=environment,
                                       stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        result["returncode"] = completed.returncode
        access_report = case_dir / "reference_access.json"
        blocked = json.loads(access_report.read_text(encoding="utf-8"))["blocked_svg_reads"] if access_report.exists() else []
        result["blocked_svg_reads"] = blocked
        if blocked:
            result["failures"] = ["reference_svg_access"]
            return result
        if completed.returncode:
            result["failures"] = ["converter_error"]
            return result
        # Measure final failed-folder SVGs too: the independent gate decides quality.
        candidates = [path for folder in ("converted_svgs", "converted_svg_failed")
                      for path in (case_dir / "conversion" / folder).glob("*.svg")
                      if path.stem.casefold() in {name.casefold(), "failed_" + name.casefold()}]
        if len(candidates) != 1:
            result["failures"] = ["missing_or_ambiguous_output"]
            return result
        svg_path = candidates[0]
        svg = svg_path.read_text(encoding="utf-8")
        result.update(measure_quality(reference, svg))
        result.update(output_svg=str(svg_path.relative_to(output)), output_sha256=sha256(svg_path.read_bytes()))
        # Batch acceptance is based on independently measured saved vectors, not
        # the converter's historical success/failed labels or checkpoints.
        if keep_debug_artifacts:
            raster = render(svg, case["width"], case["height"])
            cv2.imwrite(str(case_dir / "output.png"), raster)
            cv2.imwrite(str(case_dir / "difference.png"), cv2.absdiff(reference, raster))
            cv2.imwrite(str(case_dir / "comparison.png"), cv2.hconcat([reference, raster, cv2.absdiff(reference, raster)]))
    except subprocess.TimeoutExpired:
        result["failures"] = ["conversion_timeout"]
    except Exception as exc:
        # A broken renderer/metric must fail this case independently.
        result.update(failures=["conversion_or_measurement_error"], error=str(exc), satisfactory=False)
    finally:
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result


def summarize(results: list[dict]) -> dict:
    passed = sum(case["satisfactory"] for case in results)
    return {"required": REQUIRED_COUNT, "completed": len(results), "passed": passed,
            "failed": len(results) - passed,
            "satisfactory": len(results) == REQUIRED_COUNT and passed == REQUIRED_COUNT}


def run_battery(svg_path: Path, description: str, output: Path, *, seed: int,
                timeout: float = 60, iterations: int = 64, selection: dict | None = None,
                keep_debug_artifacts: bool = False) -> dict:
    if not math.isfinite(timeout) or timeout <= 0 or iterations < 1:
        raise ValueError("Timeout and iterations must be positive")
    output = output.resolve()
    svg = svg_path.read_text(encoding="utf-8")
    cases = [make_original_case(svg, description)]
    output.mkdir(parents=True, exist_ok=False)
    if keep_debug_artifacts:
        (output / "source.svg").write_text(svg, encoding="utf-8")
        (output / "source_description.txt").write_text(description, encoding="utf-8")
    manifest = {"schema_version": "plan_b_variations_v2", "seed": seed, "limits": LIMITS,
                "iterations": iterations, "timeout_seconds": timeout,
                "source_svg_sha256": sha256(svg.encode("utf-8")),
                "source_description_sha256": sha256(description.encode("utf-8")),
                "source_description": description,
                "source_image": "source.png",
                "artifact_retention": "debug" if keep_debug_artifacts else "summary_and_source_image",
                "selection": selection or {"mode": "explicit", "source_svg": str(svg_path.resolve())},
                "cases": cases}
    if not keep_debug_artifacts:
        manifest["selection"] = {key: value for key, value in manifest["selection"].items()
                                 if key not in {"pool", "excluded"}}
    report = {**manifest, "cases": [], "status": "checking_original", "original_satisfactory": None,
              "variations_started": False, "summary": summarize([])}

    def save_report():
        (output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        if keep_debug_artifacts:
            (output / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        write_cases(cases, output)
        # Keep the original pixels even if the CLI moves its input after success.
        shutil.copyfile(output / "original/input/original.png", output / "source.png")
        report["source_image_sha256"] = cases[0]["input_sha256"]
        save_report()
        for case in cases:
            print(f"[Plan B] {len(report['cases'])+1}/{REQUIRED_COUNT} {case['case_id']} started", flush=True)
            result = run_case(case, output, timeout=timeout, iterations=iterations,
                              keep_debug_artifacts=keep_debug_artifacts)
            if not keep_debug_artifacts:
                result = {key: value for key, value in result.items()
                          if key not in {"command", "output_svg", "reference_svg", "description", "limits"}}
            report["cases"].append(result)
            report["summary"] = summarize(report["cases"])
            if case["case_id"] == "original":
                report["original_satisfactory"] = result["satisfactory"]
                report["status"] = "running_variations" if result["satisfactory"] else "original_not_convertible"
            elif len(report["cases"]) == REQUIRED_COUNT:
                report["status"] = "completed"
            save_report()
            print(f"[Plan B] {case['case_id']}: {'PASS' if result['satisfactory'] else 'FAIL'} "
                  f"{','.join(result['failures'])} ({result['elapsed_seconds']}s)", flush=True)
            if case["case_id"] == "original":
                if not result["satisfactory"]:
                    print("[Plan B] Original quality check failed; 16 variations were not started", flush=True)
                    break
                # Only generate the extended task once its prerequisite passes.
                variations = make_variations(svg, description, seed)
                cases.extend(variations)
                write_cases(variations, output)
                report["variations_started"] = True
                save_report()
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        save_report()
        raise
    except Exception as exc:
        report.update(status="preparation_error", error=str(exc))
        save_report()
        raise
    finally:
        if not keep_debug_artifacts:
            # This run created the fresh directory exclusively. Delete
            # only its generated children, including after an interrupted run.
            for directory in [output / "references", *[output / case["case_id"] for case in cases]]:
                if directory.resolve().parent != output:
                    raise ValueError("Generated work directory escapes the run output")
                if directory.exists():
                    shutil.rmtree(directory)
    return report


def run_pool_batteries(svg_dir: Path, descriptions_path: Path, output: Path, *, seed: int,
                       max_additional_svgs: int = MAX_ADDITIONAL_SVGS,
                       timeout: float = 60, iterations: int = 64,
                       keep_debug_artifacts: bool = False) -> dict:
    """Try distinct originals until one can run its full extended Plan-B task."""
    if not 0 <= max_additional_svgs <= MAX_ADDITIONAL_SVGS:
        raise ValueError("At most eight additional SVGs may be attempted")
    if not math.isfinite(timeout) or timeout <= 0 or iterations < 1:
        raise ValueError("Timeout and iterations must be positive")
    task = select_task(svg_dir, descriptions_path, seed)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": "plan_b_search_v1", "seed": seed, "limits": LIMITS,
              "max_additional_svgs": max_additional_svgs, "status": "searching",
              "attempts": [], "summary": summarize([])}
    attempted: set[Path] = set()
    retry_random = random.Random(seed)
    attempt_seed = seed

    def save_report():
        (output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    save_report()
    try:
        for index in range(max_additional_svgs + 1):
            svg_path, description, selection = task
            attempted.add(svg_path.resolve())
            attempt_dir = output / f"attempt_{index+1:02d}"
            attempt = {"source_svg": str(svg_path.resolve()), "seed": attempt_seed,
                       "report": str((attempt_dir / "report.json").relative_to(output)),
                       "status": "running"}
            report["attempts"].append(attempt)
            save_report()
            print(f"[Plan B] SVG {index+1}/{max_additional_svgs+1}: selected={svg_path} "
                  f"seed={attempt_seed} output={attempt_dir}", flush=True)
            result = run_battery(svg_path, description, attempt_dir, seed=attempt_seed, selection=selection,
                                 timeout=timeout, iterations=iterations,
                                 keep_debug_artifacts=keep_debug_artifacts)
            attempt.update(status=result["status"], summary=result["summary"],
                           original_satisfactory=result["original_satisfactory"],
                           variations_started=result["variations_started"])
            report["summary"] = result["summary"]
            # A failed variant remains a failed extended task. Only the original
            # prerequisite triggers selection of another SVG.
            if result["status"] != "original_not_convertible":
                report["status"] = "completed"
                break
            if index == max_additional_svgs:
                report["status"] = "retry_limit_reached"
                break
            save_report()
            try:
                attempt_seed = retry_random.randrange(2**63)
                task = select_task(svg_dir, descriptions_path, attempt_seed, excluded_svg_paths=attempted)
            except TaskPoolExhausted:
                report["status"] = "pool_exhausted"
                break
            print("[Plan B] Original failed; trying another SVG", flush=True)
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        if report["attempts"] and report["attempts"][-1]["status"] == "running":
            report["attempts"][-1]["status"] = "interrupted"
        raise
    except Exception as exc:
        report.update(status="preparation_error", error=str(exc))
        if report["attempts"] and report["attempts"][-1]["status"] == "running":
            report["attempts"][-1].update(status="preparation_error", error=str(exc))
        raise
    finally:
        save_report()
    return report


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--_worker":
        return converter_worker(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg-dir", type=Path, default=DEFAULT_SVG_DIR, help="Pool for a fresh random selection")
    parser.add_argument("--descriptions-path", type=Path, default=DEFAULT_DESCRIPTIONS)
    parser.add_argument("--svg", type=Path, help="Explicit source, for replaying a failed run")
    parser.add_argument("--description-file", type=Path, help="Description of an explicit SVG")
    parser.add_argument("--output-dir", type=Path, help="Fresh directory; existing runs are never reused")
    parser.add_argument("--seed", type=int, help="Optional replay seed; default is fresh system randomness")
    parser.add_argument("--timeout-seconds", type=float, default=60)
    parser.add_argument("--iterations", type=int, default=64)
    parser.add_argument("--max-additional-svgs", type=int, choices=range(MAX_ADDITIONAL_SVGS + 1),
                        default=MAX_ADDITIONAL_SVGS,
                        help="Try up to this many other SVGs after original failure (default 8; pool mode only)")
    parser.add_argument("--keep-debug-artifacts", action="store_true",
                        help="Keep reference SVGs, rasters, converter outputs and logs; default keeps report.json and source.png")
    args = parser.parse_args(argv)
    if bool(args.svg) != bool(args.description_file):
        parser.error("--svg and --description-file must be supplied together")
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**63)
    if args.svg:
        svg_path, description, selection = args.svg, args.description_file.read_text(encoding="utf-8"), None
    output = args.output_dir or ROOT / "artifacts/evaluation/plan_b_variations" / f"run_{time.time_ns()}_{seed}"
    if args.svg:
        print(f"[Plan B] selected={svg_path} seed={seed} output={output}", flush=True)
        report = run_battery(svg_path, description, output, seed=seed, selection=selection,
                             timeout=args.timeout_seconds, iterations=args.iterations,
                             keep_debug_artifacts=args.keep_debug_artifacts)
    else:
        report = run_pool_batteries(args.svg_dir, args.descriptions_path, output, seed=seed,
                                    max_additional_svgs=args.max_additional_svgs,
                                    timeout=args.timeout_seconds, iterations=args.iterations,
                                    keep_debug_artifacts=args.keep_debug_artifacts)
        print(f"[Plan B] search={report['status']} attempted_svgs={len(report['attempts'])} "
              f"report={output / 'report.json'}", flush=True)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if report["summary"]["satisfactory"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
