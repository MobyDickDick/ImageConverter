"""The unmodified circle-valve description must produce complete native geometry."""
from pathlib import Path
import threading
from xml.etree import ElementTree as ET

import cv2
import pytest

from src import imageConverterGui as gui
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    DescriptionRejected, description_assertions, draft_assertions, validate_svg_assertions,
)
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterThreeWingValve import three_wing_valve_spec
from tools.evaluate_svg_text_baseline import render_librsvg

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Links: drei je gleichschenklige Dreiecke, welche sich in einem Punkt berühren.\n'
               'Das Innere der Dreieck hat jeweils einen Farbübergang.\n'
               'Rechts ist eine Kelle mit einem leeren Kreis und einem Griff nach links vorhanden.')


def test_original_description_has_the_complete_inventory_and_route():
    actual = next(e.get('beschreibung') for e in ET.parse(ROOT/'artifacts/descriptions/Finale_Wurzelformen_V3.xml').iter('bild')
                  if e.text=='AC0222_L.jpg')
    assert actual==DESCRIPTION
    assertions = description_assertions(actual)
    assert assertions['objects']==dict(triangle=3, circle=1, line=1)
    assert assertions['three_wing_valve']['isosceles']
    for name in ('AC0222_L', 'anonymous'):
        _, params = Reflection({name:actual}).parseDescription(name, name+'.jpg')
        assert params['contract_status']=='ok' and params['mode']=='non_composite'
        assert params['geometry_ir']==[] and params['label']==''


@pytest.mark.parametrize('extra', [' Zusätzlich ein Quadrat.', ' Die Dreiecke sind rechts.', ' Ohne Griff.'])
def test_unknown_claims_are_not_silently_ignored(extra):
    assert three_wing_valve_spec(DESCRIPTION+extra) is None


@pytest.mark.parametrize('profile,seed', [('quick',17), ('quick',18), ('normal',17)])
def test_real_worker_and_independent_renderer(tmp_path, monkeypatch, profile, seed):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    try:
        # An anonymous upload prevents any filename-based geometry or SVG reuse.
        uploaded = jobs.upload('anonymous.jpg', (ROOT/'artifacts/images_to_convert/AC0222_L.jpg').read_bytes())
        started = jobs.start(uploaded['id'], DESCRIPTION, profile, seed=seed, use_current_svg=False)
        jobs.threads[-1].join(gui.PROFILES[profile][1]+25)
        result = jobs.snapshot(started['id'])
        assert result['status']=='done' and result['quality']=='passed',result
        svg = (jobs.folder(result['id'])/'result.svg').read_text(encoding='utf-8')
        validate_svg_assertions(svg, description_assertions(DESCRIPTION))
        source = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0222_L.jpg'))
        rendered = render_librsvg(svg, source.shape[1], source.shape[0])
        quality = pixel_quality(source, rendered)
        (tmp_path/'result.svg').write_text(svg, encoding='utf-8')
        cv2.imwrite(str(tmp_path/'result-librsvg.png'), rendered)
        import json
        (tmp_path/'quality.json').write_text(json.dumps(dict(
            seed=seed, profile=profile, independent_quality=quality,
            search=result.get('search_summary'), elapsed=result.get('elapsed')), indent=2))
        assert quality['passed'] and quality['foreground_iou']>.95, quality
        # Geometric and paint errors must remain invalid even for failed drafts.
        for fault in ('missing_wing', 'filled_circle', 'unequal_sides', 'flat_gradient'):
            root = ET.fromstring(svg)
            circle = next(e for e in root if e.tag.rsplit('}',1)[-1]=='circle')
            wing = next(e for e in root if e.tag.rsplit('}',1)[-1]=='path')
            if fault=='missing_wing': root.remove(wing)
            elif fault=='filled_circle': circle.set('fill','gray')
            elif fault=='unequal_sides':
                coordinates = wing.get('d').split()
                coordinates[5] = str(float(coordinates[5])+1)
                wing.set('d', ' '.join(coordinates))
            else: wing.set('fill','gray')
            for assertions in (description_assertions(DESCRIPTION), draft_assertions(description_assertions(DESCRIPTION))):
                with pytest.raises(DescriptionRejected):
                    validate_svg_assertions(ET.tostring(root,encoding='unicode'), assertions)
    finally:
        jobs.close()


def test_real_server_loop_runs_new_seeds_and_keeps_the_winner_on_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    completed, stopped = [], threading.Event()
    def on_result(job_id):
        completed.append(job_id)
        if len(completed)>=2 and not stopped.is_set():
            jobs.seed_retry.stop(job_id)
            stopped.set()
    jobs.on_result = on_result
    try:
        uploaded = jobs.upload('neutral-loop.jpg', (ROOT/'artifacts/images_to_convert/AC0222_L.jpg').read_bytes())
        first = jobs.seed_retry.toggle(uploaded['id'], DESCRIPTION, 'quick', seed=17, use_current_svg=False)
        assert stopped.wait(2*gui.PROFILES['quick'][1]+35)
        session = jobs.seed_retry.session(first['id'])
        assert not session['active'] and session['attempts']>=2
        assert len({jobs.jobs[job_id]['search_seed'] for job_id in completed[:2]})==2
        assert all(jobs.jobs[job_id]['result'] for job_id in completed[:2])
        winner = jobs.folder(first['id'])/'seed-best.svg'
        assert winner.is_file() and jobs.export_file(first['id'])==winner
        validate_svg_assertions(winner.read_text(encoding='utf-8'), description_assertions(DESCRIPTION))
        assert session['best_quality']['passed'] and not session['best_description_error']
    finally:
        jobs.close()
