from pathlib import Path
import json
import subprocess
from xml.etree import ElementTree as ET

import pytest

from tools import run_plan_b_variations as battery

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><rect width="80" height="80" fill="white"/><circle cx="40" cy="40" r="12" fill="green"/></svg>'
DESCRIPTION = "Grüner Kreis auf weißem Hintergrund."


def description_catalog(path, entries):
    root = ET.Element("root")
    for key, description, image, detail in entries:
        entry = ET.SubElement(root, "entry", key=key)
        ET.SubElement(entry, "beschreibung").text = description
        ET.SubElement(ET.SubElement(entry, "bilder"), "bild").text = image
        if detail:
            ET.SubElement(ET.SubElement(entry, "bildbeschreibungen"), "bildbeschreibung", bild=image).text = detail
    ET.ElementTree(root).write(path, encoding="utf-8")


def test_random_selection_uses_matching_image_description_and_entire_pool(tmp_path):
    catalog = tmp_path / "descriptions.xml"
    description_catalog(catalog, [("first", "Kreis.", "first_L.jpg", "Grün."),
                                   ("second", "Rechteck.", "second.jpg", "Blau.")])
    for name in ("first_L", "second", "unpaired"):
        (tmp_path / (name + ".svg")).write_text(SVG, encoding="utf-8")
    selected = {}
    for seed in range(20):
        svg, text, evidence = battery.select_task(tmp_path, catalog, seed)
        selected[svg.stem] = text
        assert evidence["pool_size"] == 2
        assert evidence["excluded"] == [{"svg": str((tmp_path / "unpaired.svg").resolve()), "reason": "missing_description"}]
    assert selected == {"first_L": "Kreis. Grün.", "second": "Rechteck. Blau."}
    assert battery.select_task(tmp_path, catalog, 7) == battery.select_task(tmp_path, catalog, 7)


def test_sidecar_pairs_work_for_arbitrary_svg_names(tmp_path):
    catalog = tmp_path / "descriptions.xml"
    description_catalog(catalog, [])
    svg = tmp_path / "arbitrary-scene.svg"
    svg.write_text(SVG, encoding="utf-8")
    svg.with_suffix(".txt").write_text(DESCRIPTION, encoding="utf-8")
    selected, description, evidence = battery.select_task(tmp_path, catalog, 1)
    assert selected == svg.resolve() and description == DESCRIPTION and evidence["pool_size"] == 1


def test_default_start_selects_new_task_and_seed_every_time(monkeypatch, tmp_path):
    seeds = iter((11, 22))
    class Entropy:
        def randrange(self, limit):
            return next(seeds)
    monkeypatch.setattr(battery.random, "SystemRandom", Entropy)
    selections, runs = [], []
    def select(directory, descriptions, seed):
        selections.append(seed)
        return tmp_path / "source.svg", DESCRIPTION, {"seed": seed}
    def run(svg, description, output, **kwargs):
        runs.append((svg, description, output, kwargs))
        return {"summary": {"satisfactory": True}}
    monkeypatch.setattr(battery, "select_task", select)
    monkeypatch.setattr(battery, "run_battery", run)
    assert battery.main([]) == 0
    assert battery.main([]) == 0
    assert selections == [11, 22]
    assert runs[0][2] != runs[1][2]
    assert all(r[3]["selection"] == {"seed": r[3]["seed"]} for r in runs)


def test_sixteen_new_rasters_and_consistent_descriptions_can_be_replayed(tmp_path):
    a = battery.make_variations(SVG, DESCRIPTION, 123)
    assert len(a) == 16
    assert a == battery.make_variations(SVG, DESCRIPTION, 123)
    assert a != battery.make_variations(SVG, DESCRIPTION, 124)
    assert len({c["svg"] for c in a}) == len({c["description"] for c in a}) == 16
    for case in a:
        v, text = case["variation"], case["description"]
        assert 0.94 <= v["scale"] <= 1.06
        assert abs(v["relative_x"]) <= .025 and abs(v["relative_y"]) <= .025
        assert ("kleiner" if v["scale"] < 1 else "größer") in text
        assert ("links" if v["relative_x"] < 0 else "rechts") in text
        assert ("oben" if v["relative_y"] < 0 else "unten") in text
        assert text.startswith(DESCRIPTION) and not any(char.isdigit() for char in text)
    cases = battery.prepare_cases(SVG, DESCRIPTION, tmp_path / "run", 123)
    assert len({c["input_sha256"] for c in cases}) == 16
    for case in cases:
        inputs = tmp_path / "run" / case["case_id"] / "input"
        assert {p.suffix for p in inputs.iterdir()} == {".png", ".xml"}
        root = ET.parse(inputs / "descriptions.xml").getroot()
        assert root.findtext("entry/beschreibung") == case["description"]
    with pytest.raises(FileExistsError):
        battery.prepare_cases(SVG, DESCRIPTION, tmp_path / "run", 123)


def test_defs_viewbox_and_existing_transforms_survive():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="10 20 40 40"><defs><linearGradient id="paint"><stop stop-color="green"/></linearGradient></defs><g transform="translate(1 2)"><circle cx="30" cy="40" r="12" fill="url(#paint)"/></g></svg>'
    case = battery.make_variations(svg, DESCRIPTION, 12)[0]
    root = ET.fromstring(case["svg"])
    assert battery.local_name(root[0].tag) == "defs"
    assert root[1][0].get("transform") == "translate(1 2)"
    assert "translate(30.00000000 40.00000000)" in root[1].get("transform")
    assert root[0][0].get("id") == "paint"
    assert root.get("viewBox") == "10 20 40 40"


def test_quality_checks_saved_pixels_not_success_labels():
    reference = battery.render(SVG, 80, 80)
    good = battery.measure_quality(reference, SVG)
    assert good["satisfactory"]
    assert good["metrics"] == {"normalized_mse": 0, "foreground_mse": 0, "edge_alignment": 1, "foreground_iou": 1}
    blank = '<svg width="80" height="80"><rect width="80" height="80" fill="white"/></svg>'
    bad = battery.measure_quality(reference, blank)
    assert not bad["satisfactory"]
    assert "foreground_iou_outside_limit" in bad["failures"]
    assert "edge_alignment_outside_limit" in bad["failures"]
    wrong = battery.measure_quality(reference, SVG.replace('fill="green"', 'fill="red"'))
    assert not wrong["satisfactory"] and "foreground_mse_outside_limit" in wrong["failures"]
    dimensions = battery.measure_quality(reference, SVG.replace('width="80" height="80"', 'width="40" height="40"', 1))
    assert "dimension_mismatch" in dimensions["failures"]
    embedded = battery.measure_quality(reference, SVG.replace('</svg>', '<image href="missing.png"/></svg>'))
    assert "embedded_raster" in embedded["failures"]
    assert not battery.measure_quality(reference, '<svg>')["satisfactory"]


@pytest.mark.parametrize("failure", ["timeout", "error", "missing", "good", "bad", "measurement_error"])
def test_real_cli_boundary_failure_paths_and_metrics(tmp_path, monkeypatch, failure):
    output = tmp_path / "run"
    case = battery.prepare_cases(SVG, DESCRIPTION, output, 123)[0]
    def invoke(command, **kwargs):
        assert command[0] == battery.sys.executable
        assert command[command.index("--execution-mode") + 1] == "semantic-only"
        assert "references" not in str(command)
        assert kwargs["timeout"] == 1
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 1)
        if failure in ("good", "bad", "measurement_error"):
            result_dir = output / case["case_id"] / "conversion/converted_svgs"
            result_dir.mkdir(parents=True)
            svg = (output / case["reference_svg"]).read_text(encoding="utf-8")
            (result_dir / (case["case_id"].upper() + ".svg")).write_text(
                svg if failure != "bad" else SVG.replace('fill="green"', 'fill="red"'), encoding="utf-8")
        return subprocess.CompletedProcess(command, 2 if failure == "error" else 0)
    monkeypatch.setattr(battery.subprocess, "run", invoke)
    if failure == "measurement_error":
        def broken_metric(*args, **kwargs):
            raise RuntimeError("Renderer failed")
        monkeypatch.setattr(battery, "measure_quality", broken_metric)
    result = battery.run_case(case, output, timeout=1, iterations=64)
    assert result["satisfactory"] == (failure == "good")
    if failure == "timeout": assert result["failures"] == ["conversion_timeout"]
    if failure == "error": assert result["failures"] == ["converter_error"]
    if failure == "missing": assert result["failures"] == ["missing_or_ambiguous_output"]
    if failure == "measurement_error":
        assert result["failures"] == ["conversion_or_measurement_error"] and result["error"] == "Renderer failed"
    if failure in ("good", "bad"):
        assert "metrics" in result and (output / case["case_id"] / "comparison.png").exists()


def test_all_sixteen_run_even_after_failure_and_overall_exit_is_red(tmp_path, monkeypatch):
    source = tmp_path / "source.svg"
    source.write_text(SVG, encoding="utf-8")
    calls = []
    def run(case, output, **kwargs):
        calls.append(case["case_id"])
        passed = len(calls) != 1
        return {**case, "satisfactory": passed, "failures": [] if passed else ["conversion_timeout"], "elapsed_seconds": 0}
    monkeypatch.setattr(battery, "run_case", run)
    output = tmp_path / "run"
    report = battery.run_battery(source, DESCRIPTION, output, seed=12)
    assert len(calls) == 16
    assert report["summary"] == {"required": 16, "completed": 16, "passed": 15, "failed": 1, "satisfactory": False}
    assert json.loads((output / "report.json").read_text(encoding="utf-8")) == report
    monkeypatch.setattr(battery, "run_battery", lambda *args, **kwargs: report)
    description = tmp_path / "description.txt"
    description.write_text(DESCRIPTION, encoding="utf-8")
    assert battery.main(["--svg", str(source), "--description-file", str(description)]) == 1
    assert not battery.summarize([{"satisfactory": True}] * 15)["satisfactory"]
    assert battery.summarize([{"satisfactory": True}] * 16)["satisfactory"]


def test_worker_blocks_external_svg_reads_even_when_catalog_references_are_in_description(tmp_path):
    generated = tmp_path / "run/conversion"
    assert battery.forbidden_vector_read(tmp_path / "references/target.svg", "r", 0, generated)
    assert battery.forbidden_vector_read(tmp_path / "samples/reference.svg", None, 0, generated)
    assert not battery.forbidden_vector_read(generated / "converted_svgs/result.svg", "r", 0, generated)
    assert not battery.forbidden_vector_read(tmp_path / "new.svg", "w", 0, generated)
    assert not battery.forbidden_vector_read(tmp_path / "input.png", "rb", 0, generated)
