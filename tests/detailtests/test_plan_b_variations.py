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
        return {"status": "completed", "original_satisfactory": True,
                "variations_started": True, "summary": {"satisfactory": True}}
    monkeypatch.setattr(battery, "select_task", select)
    monkeypatch.setattr(battery, "run_battery", run)
    assert battery.main(["--output-dir", str(tmp_path / "first")]) == 0
    assert battery.main(["--output-dir", str(tmp_path / "second")]) == 0
    assert selections == [11, 22]
    assert runs[0][2] != runs[1][2]
    assert all(r[3]["selection"] == {"seed": r[3]["seed"]} for r in runs)


def task_pool(tmp_path, count):
    pool = tmp_path / "pool"
    pool.mkdir()
    catalog = tmp_path / "descriptions.xml"
    description_catalog(catalog, [])
    for index in range(count):
        svg = pool / f"scene_{index:02d}.svg"
        svg.write_text(SVG, encoding="utf-8")
        svg.with_suffix(".txt").write_text(f"{DESCRIPTION} Motiv {index}.", encoding="utf-8")
    return pool, catalog


@pytest.mark.parametrize("failure", ["foreground_iou_outside_limit", "conversion_timeout",
                                    "converter_error", "missing_or_ambiguous_output", "reference_svg_access"])
def test_failed_original_retries_another_svg_and_runs_its_full_task(tmp_path, monkeypatch, failure):
    pool, catalog = task_pool(tmp_path, 4)
    calls = []
    def run(case, output, **kwargs):
        calls.append((output.name, case["case_id"]))
        satisfactory = output.name != "attempt_01"
        return {**case, "satisfactory": satisfactory,
                "failures": [] if satisfactory else [failure], "elapsed_seconds": 0}
    monkeypatch.setattr(battery, "run_case", run)
    output = tmp_path / "run"
    assert battery.main(["--svg-dir", str(pool), "--descriptions-path", str(catalog),
                         "--output-dir", str(output), "--seed", "12"]) == 0
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "completed" and report["summary"]["satisfactory"]
    assert calls == [("attempt_01", "original"), ("attempt_02", "original"),
                     *[("attempt_02", f"probe_{i:02d}") for i in range(1, 17)]]
    assert len({a["source_svg"] for a in report["attempts"]}) == 2
    for index, attempt in enumerate(report["attempts"]):
        directory = (output / attempt["report"]).parent
        assert {p.name for p in directory.iterdir()} == {"report.json", "source.png"}
        detail = json.loads((output / attempt["report"]).read_text(encoding="utf-8"))
        assert detail["selection"]["source_svg"] == attempt["source_svg"]
        assert detail["source_description"] == Path(attempt["source_svg"]).with_suffix(".txt").read_text(encoding="utf-8")
        assert detail["summary"] == attempt["summary"]
        assert detail["limits"] == battery.LIMITS
        if index == 0:
            assert detail["cases"][0]["failures"] == [failure]


@pytest.mark.parametrize("pool_size,budget,expected,status", [
    (12, 8, 9, "retry_limit_reached"), (12, 0, 1, "retry_limit_reached"),
    (12, 2, 3, "retry_limit_reached"), (2, 8, 2, "pool_exhausted"), (1, 8, 1, "pool_exhausted")])
def test_failed_search_is_bounded_distinct_and_reproducible(tmp_path, monkeypatch, pool_size, budget, expected, status):
    pool, catalog = task_pool(tmp_path, pool_size)
    calls = []
    def run(case, output, **kwargs):
        calls.append(case["case_id"])
        return {**case, "satisfactory": False, "failures": ["converter_error"], "elapsed_seconds": 0}
    monkeypatch.setattr(battery, "run_case", run)
    def search(directory):
        assert battery.main(["--svg-dir", str(pool), "--descriptions-path", str(catalog),
                             "--output-dir", str(directory), "--seed", "42",
                             "--max-additional-svgs", str(budget)]) == 1
        return json.loads((directory / "report.json").read_text(encoding="utf-8"))
    first = search(tmp_path / "first")
    second = search(tmp_path / "second")
    assert first == second
    assert first["status"] == status and not first["summary"]["satisfactory"]
    assert len(first["attempts"]) == len({a["source_svg"] for a in first["attempts"]}) == expected
    assert calls == ["original"] * (expected * 2)
    assert all(not a["variations_started"] for a in first["attempts"])


def test_ninth_svg_can_pass_but_failed_variants_do_not_trigger_more_selection(tmp_path, monkeypatch):
    pool, catalog = task_pool(tmp_path, 12)
    def run(case, output, **kwargs):
        satisfactory = output.name == "attempt_09"
        return {**case, "satisfactory": satisfactory, "failures": [] if satisfactory else ["converter_error"],
                "elapsed_seconds": 0}
    monkeypatch.setattr(battery, "run_case", run)
    report = battery.run_pool_batteries(pool, catalog, tmp_path / "ninth", seed=12)
    assert len(report["attempts"]) == 9 and report["summary"]["satisfactory"]
    monkeypatch.setattr(battery, "run_case", lambda case, output, **kwargs:
                        {**case, "satisfactory": case["case_id"] != "probe_01",
                         "failures": [] if case["case_id"] != "probe_01" else ["foreground_iou_outside_limit"],
                         "elapsed_seconds": 0})
    report = battery.run_pool_batteries(pool, catalog, tmp_path / "variant_failure", seed=12)
    assert len(report["attempts"]) == 1 and report["status"] == "completed"
    assert report["summary"]["completed"] == 17 and not report["summary"]["satisfactory"]


@pytest.mark.parametrize("error", [KeyboardInterrupt, ValueError])
def test_search_stops_on_interruption_or_preparation_error_and_preserves_reports(tmp_path, monkeypatch, error):
    pool, catalog = task_pool(tmp_path, 4)
    def run(case, output, **kwargs):
        if output.name == "attempt_02":
            raise error("Stop")
        return {**case, "satisfactory": False, "failures": ["converter_error"], "elapsed_seconds": 0}
    monkeypatch.setattr(battery, "run_case", run)
    output = tmp_path / "run"
    with pytest.raises(error):
        battery.run_pool_batteries(pool, catalog, output, seed=12)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == ("interrupted" if error is KeyboardInterrupt else "preparation_error")
    assert len(report["attempts"]) == 2 and not report["summary"]["satisfactory"]
    for attempt in report["attempts"]:
        directory = (output / attempt["report"]).parent
        assert {p.name for p in directory.iterdir()} == {"report.json", "source.png"}
        assert json.loads((output / attempt["report"]).read_text(encoding="utf-8"))["status"] == attempt["status"]
    before = (output / "report.json").read_bytes()
    with pytest.raises(FileExistsError):
        battery.run_pool_batteries(pool, catalog, output, seed=12)
    assert (output / "report.json").read_bytes() == before


@pytest.mark.parametrize("budget", [-1, 9])
def test_cli_rejects_retry_budgets_outside_zero_to_eight(budget):
    with pytest.raises(SystemExit) as exc:
        battery.main(["--max-additional-svgs", str(budget)])
    assert exc.value.code == 2


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
        passed = case["case_id"] != "probe_01"
        return {**case, "satisfactory": passed, "failures": [] if passed else ["conversion_timeout"], "elapsed_seconds": 0}
    monkeypatch.setattr(battery, "run_case", run)
    output = tmp_path / "run"
    report = battery.run_battery(source, DESCRIPTION, output, seed=12)
    assert calls == ["original", *[f"probe_{i:02d}" for i in range(1, 17)]]
    assert report["summary"] == {"required": 17, "completed": 17, "passed": 16, "failed": 1, "satisfactory": False}
    assert report["original_satisfactory"] and report["variations_started"]
    assert report["status"] == "completed"
    assert json.loads((output / "report.json").read_text(encoding="utf-8")) == report
    assert {p.name for p in output.iterdir()} == {"report.json", "source.png"}
    assert battery.sha256((output / "source.png").read_bytes()) == report["source_image_sha256"]
    assert report['source_description'] == DESCRIPTION
    assert 'reference_svg' not in report['cases'][0]
    monkeypatch.setattr(battery, "run_battery", lambda *args, **kwargs: report)
    description = tmp_path / "description.txt"
    description.write_text(DESCRIPTION, encoding="utf-8")
    assert battery.main(["--svg", str(source), "--description-file", str(description)]) == 1
    assert not battery.summarize([{"satisfactory": True}] * 16)["satisfactory"]
    assert battery.summarize([{"satisfactory": True}] * 17)["satisfactory"]


@pytest.mark.parametrize("failure", ["foreground_iou_outside_limit", "conversion_timeout", "converter_error",
                                    "missing_or_ambiguous_output", "reference_svg_access"])
def test_original_failure_prevents_generation_and_execution_of_variations(tmp_path, monkeypatch, failure):
    source = tmp_path / "source.svg"
    source.write_text(SVG, encoding="utf-8")
    calls = []
    def run(case, output, **kwargs):
        calls.append(case["case_id"])
        assert case["description"] == DESCRIPTION
        assert (output / case["reference_svg"]).read_text(encoding="utf-8") == SVG
        assert case["variation"] == {"scale": 1.0, "relative_x": 0.0, "relative_y": 0.0}
        return {**case, "satisfactory": False, "failures": [failure], "elapsed_seconds": 0}
    def forbidden_variations(*args, **kwargs):
        pytest.fail("Variations must not be generated before the original quality check passes")
    monkeypatch.setattr(battery, "run_case", run)
    monkeypatch.setattr(battery, "make_variations", forbidden_variations)
    output = tmp_path / "run"
    report = battery.run_battery(source, DESCRIPTION, output, seed=12)
    assert calls == ["original"]
    assert report["status"] == "original_not_convertible"
    assert report["original_satisfactory"] is False and report["variations_started"] is False
    assert report["summary"] == {"required": 17, "completed": 1, "passed": 0, "failed": 1, "satisfactory": False}
    assert report["cases"][0]["failures"] == [failure]
    assert json.loads((output / "report.json").read_text(encoding="utf-8")) == report
    assert {p.name for p in output.iterdir()} == {"report.json", "source.png"}
    monkeypatch.setattr(battery, "run_battery", lambda *args, **kwargs: report)
    description = tmp_path / "description.txt"
    description.write_text(DESCRIPTION, encoding="utf-8")
    assert battery.main(["--svg", str(source), "--description-file", str(description)]) == 1


def test_debug_files_are_kept_only_when_requested(tmp_path, monkeypatch):
    source = tmp_path / 'source.svg'
    source.write_text(SVG, encoding='utf-8')
    monkeypatch.setattr(battery, 'run_case', lambda case, output, **kwargs:
                        {**case, 'satisfactory': True, 'failures': [], 'elapsed_seconds': 0})
    output = tmp_path / 'debug'
    report = battery.run_battery(source, DESCRIPTION, output, seed=12, keep_debug_artifacts=True)
    assert report['summary']['passed'] == 17
    assert report['summary']['satisfactory']
    assert report['cases'][0]['case_id'] == 'original'
    assert (output / 'source.svg').exists()
    assert (output / 'manifest.json').exists()
    assert (output / 'references').is_dir()
    assert (output / 'probe_01/input/probe_01.png').exists()
    assert (output / 'original/input/original.png').read_bytes() == (output / 'source.png').read_bytes()
    assert [c['case_id'] for c in json.loads((output / 'manifest.json').read_text())['cases']] == [
        c['case_id'] for c in report['cases']]


@pytest.mark.parametrize('interrupt_case', ['original', 'probe_02'])
def test_interruption_removes_only_the_fresh_run_work_files(tmp_path, monkeypatch, interrupt_case):
    source = tmp_path / 'source.svg'
    source.write_text(SVG, encoding='utf-8')
    def interrupted(case, output, **kwargs):
        if case['case_id'] == interrupt_case:
            raise KeyboardInterrupt
        return {**case, 'satisfactory': True, 'failures': [], 'elapsed_seconds': 0}
    monkeypatch.setattr(battery, 'run_case', interrupted)
    output = tmp_path / 'run'
    with pytest.raises(KeyboardInterrupt):
        battery.run_battery(source, DESCRIPTION, output, seed=12)
    assert {p.name for p in output.iterdir()} == {'report.json', 'source.png'}
    report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
    assert report['status'] == 'interrupted'
    assert report['summary']['completed'] == (0 if interrupt_case == 'original' else 2)
    assert not report['summary']['satisfactory']
    assert source.read_text(encoding='utf-8') == SVG
    sentinel = output / 'untouched.txt'
    sentinel.write_text('keep', encoding='utf-8')
    with pytest.raises(FileExistsError):
        battery.run_battery(source, DESCRIPTION, output, seed=12)
    assert sentinel.read_text(encoding='utf-8') == 'keep'


@pytest.mark.parametrize('original_passes', [False, True])
def test_original_uses_real_independent_quality_gate_before_variants(tmp_path, monkeypatch, original_passes):
    source = tmp_path / 'source.svg'
    source.write_text(SVG, encoding='utf-8')
    output = tmp_path / 'run'
    calls = []
    def invoke(command, **kwargs):
        conversion = Path(command[command.index('--output-dir') + 1])
        name = conversion.parent.name
        calls.append(name)
        inputs = conversion.parent / 'input'
        description = ET.parse(inputs / 'descriptions.xml').findtext('entry/beschreibung')
        reference = (output / 'references' / (name + '.svg')).read_text(encoding='utf-8')
        if name == 'original':
            assert reference == SVG
            assert description == DESCRIPTION
        else:
            assert description.startswith(DESCRIPTION)
        result_dir = conversion / 'converted_svgs'
        result_dir.mkdir(parents=True)
        result_svg = reference.replace('fill="green"', 'fill="red"') if name == 'original' and not original_passes else reference
        (result_dir / (name.upper() + '.svg')).write_text(result_svg, encoding='utf-8')
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(battery.subprocess, 'run', invoke)
    report = battery.run_battery(source, DESCRIPTION, output, seed=123)
    assert report['original_satisfactory'] == original_passes
    assert report['summary']['satisfactory'] == original_passes
    assert len(calls) == (17 if original_passes else 1) and calls[0] == 'original'
    original_error = report['cases'][0]['metrics']['foreground_mse']
    assert original_error == 0 if original_passes else original_error > battery.LIMITS['max_foreground_mse']
    assert report['limits'] == battery.LIMITS
    if not original_passes:
        assert 'foreground_mse_outside_limit' in report['cases'][0]['failures']


def test_variant_preparation_error_retains_original_result_and_cleans_work_files(tmp_path, monkeypatch):
    source = tmp_path / 'source.svg'
    source.write_text(SVG, encoding='utf-8')
    monkeypatch.setattr(battery, 'run_case', lambda case, output, **kwargs:
                        {**case, 'satisfactory': True, 'failures': [], 'elapsed_seconds': 0})
    def broken_variants(*args):
        raise ValueError('Duplicate raster variation')
    monkeypatch.setattr(battery, 'make_variations', broken_variants)
    output = tmp_path / 'run'
    with pytest.raises(ValueError, match='Duplicate raster'):
        battery.run_battery(source, DESCRIPTION, output, seed=12)
    report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
    assert report['status'] == 'preparation_error' and report['original_satisfactory']
    assert report['summary']['completed'] == 1 and not report['summary']['satisfactory']
    assert {p.name for p in output.iterdir()} == {'report.json', 'source.png'}


def test_worker_blocks_external_svg_reads_even_when_catalog_references_are_in_description(tmp_path):
    generated = tmp_path / "run/conversion"
    assert battery.forbidden_vector_read(tmp_path / "references/target.svg", "r", 0, generated)
    assert battery.forbidden_vector_read(tmp_path / "samples/reference.svg", None, 0, generated)
    assert not battery.forbidden_vector_read(generated / "converted_svgs/result.svg", "r", 0, generated)
    assert not battery.forbidden_vector_read(tmp_path / "new.svg", "w", 0, generated)
    assert not battery.forbidden_vector_read(tmp_path / "input.png", "rb", 0, generated)


def test_real_worker_preserves_parent_toolchain_with_incompatible_pythonpath(tmp_path, monkeypatch):
    broken = tmp_path / 'broken-environment'
    broken.mkdir()
    (broken / 'sitecustomize.py').write_text("raise RuntimeError('Wrong startup environment')", encoding='utf-8')
    (broken / 'numpy.py').write_text("raise ImportError('Wrong binary ABI')", encoding='utf-8')
    monkeypatch.setenv('PYTHONPATH', str(broken))
    # This integration check exercises the production worker startup. Pytest's
    # inherited marker would enable a separate renderer subprocess per probe.
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)
    output = tmp_path / 'isolated-run'
    case = battery.make_original_case(SVG, DESCRIPTION)
    output.mkdir()
    battery.write_cases([case], output)
    result = battery.run_case(case, output, timeout=30, iterations=1)
    assert result['returncode'] == 0
    assert result['blocked_svg_reads'] == []
    assert 'metrics' in result
    assert (output / result['output_svg']).is_file()
