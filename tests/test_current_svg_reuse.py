"""Persist improvements, reuse the current SVG, and allow an explicit fresh search."""
import io
from pathlib import Path

from PIL import Image
import pytest

from src import imageConverterGui as gui
from src.imageConverterSample import render_svg

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24"><rect x="5" y="4" width="12" height="16" fill="#225599"/></svg>'


@pytest.fixture
def manager(tmp_path,monkeypatch):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    yield jobs
    jobs.close()


def upload(jobs,name='picture.png'):
    data = io.BytesIO()
    Image.fromarray(render_svg(SVG,32,24)).save(data,format='PNG')
    result = jobs.upload(name,data.getvalue())
    return jobs.jobs[result['id']]


def test_current_project_svg_is_used_before_a_better_but_older_history_record(manager):
    old = upload(manager)
    (manager.folder(old['id'])/'result.svg').write_text(SVG,encoding='utf-8')
    old.update(result=True,status='done',quality='passed')
    job = upload(manager)
    target = manager.project_svg(job)
    target.parent.mkdir(parents=True)
    current = SVG.replace('#225599','#255599')
    target.write_text(current,encoding='utf-8')
    manager.use_best_svg(job)
    assert (manager.folder(job['id'])/'sample.svg').read_text(encoding='utf-8') == current
    assert job['sample_origin']=='Gespeichertes Projekt-SVG'


def test_previous_result_is_reused_by_image_content_after_renaming(manager):
    old = upload(manager)
    (manager.folder(old['id'])/'result.svg').write_text(SVG,encoding='utf-8')
    old.update(result=True,status='done')
    job = upload(manager,'renamed.png')
    manager.use_best_svg(job)
    assert job['sample'] and job['sample_origin']=='Bisheriges Ergebnis'
    assert (manager.folder(job['id'])/'sample.svg').read_text(encoding='utf-8')==SVG


def test_checkbox_disables_even_an_attached_template(manager,monkeypatch):
    job = upload(manager)
    attached = manager.attach_sample(job['id'],'manual.svg',SVG.encode())
    calls = []
    def run(identifier):
        running = manager.jobs[identifier]
        calls.append((running.get('use_current_svg'),running.get('sample_pending')))
        running['status']='done'
    monkeypatch.setattr(manager,'run',run)
    manager.start(attached['id'],'Ein blaues Rechteck.','quick',use_current_svg=False)
    manager.threads[-1].join(5)
    assert calls==[(False,True)]
    assert manager.jobs[attached['id']]['use_current_svg'] is False


def test_disabled_checkbox_runs_regular_converter_and_still_saves_improvement(manager,monkeypatch):
    job = upload(manager)
    manager.attach_sample(job['id'],'manual.svg',SVG.encode())
    job.update(status='running',started=gui.time.time(),profile='quick',search_seed=0,
               use_current_svg=False,description='Ein blaues Rechteck.')
    calls = []
    class Process:
        returncode = 0
        def __init__(self,command,**kwargs):
            calls.append(command)
            path = manager.folder(job['id'])/'output/converted_svgs/UPLOAD.svg'
            path.parent.mkdir(parents=True)
            path.write_text(SVG,encoding='utf-8')
        def wait(self,timeout):
            pass
    monkeypatch.setattr(gui.subprocess,'Popen',Process)
    manager.run(job['id'])
    assert len(calls)==1 and 'src.imageCompositeConverter' in calls[0]
    assert 'src.imageConverterSample' not in calls[0]
    assert job['project_save']['status']=='saved'
    assert manager.project_svg(job).read_text(encoding='utf-8')==SVG


@pytest.mark.parametrize('previous',['faded.svg','without_template.svg'])
@pytest.mark.per_test_timeout(75, fail_on_timeout=True)
def test_real_sample_run_follows_raster_and_next_attempt_reuses_saved_svg(manager,previous):
    fixture = Path(__file__).parent/'fixtures/sample_contrast'
    job = manager.upload('contrast.png',(fixture/'source.png').read_bytes())
    attached = manager.attach_sample(job['id'],'manual.svg',(fixture/'sample.svg').read_bytes())
    description = (fixture/'description.txt').read_text(encoding='utf-8')
    target = manager.project_svg(manager.jobs[attached['id']])
    target.parent.mkdir(parents=True)
    target.write_bytes((fixture/previous).read_bytes())
    before_quality = gui.saved_svg_quality(manager.folder(attached['id'])/'source.png', target)
    before_error = gui.result_description_error(target, description)
    started = manager.start(attached['id'],description,'quick')
    manager.threads[-1].join(60)
    result = manager.snapshot(started['id'])
    assert result['status']=='done' and result['quality']=='passed',result
    assert result['project_save']['status'] in {'unchanged', 'saved'}
    after_quality = gui.saved_svg_quality(manager.folder(result['id'])/'source.png',target)
    assert after_quality['passed'] and not gui.result_description_error(target, description)
    assert (False, False, gui.vector_comparison_score(after_quality)) <= (
        bool(before_error), not before_quality['passed'], gui.vector_comparison_score(before_quality))
    backups = list((manager.project_directory/'gui_history').glob('*/*.svg'))
    if result['project_save']['status'] == 'unchanged':
        assert not backups
    else:
        assert len(backups)==1 and backups[0].read_bytes()==(fixture/previous).read_bytes()
    saved = target.read_bytes()
    # A new process and retry must discover the current file, not restart from
    # the old pale result or the originally attached unaligned assembly.
    restored = gui.Jobs(manager.directory)
    restored.project_directory = manager.project_directory
    try:
        retry = restored.editable(result['id'])
        retry['description']=description
        restored.use_best_svg(retry)
        assert (restored.folder(retry['id'])/'sample.svg').read_bytes()==saved
        assert retry['sample_origin']=='Gespeichertes Projekt-SVG'
    finally:
        restored.close()


def test_smaller_global_error_cannot_replace_svg_with_better_contours(manager):
    fixture = Path(__file__).parent/'fixtures/sample_contrast'
    uploaded = manager.upload('contrast.png',(fixture/'source.png').read_bytes())
    job = manager.jobs[uploaded['id']]
    job.update(status='done',result=True,quality='passed',use_current_svg=False,
               description=(fixture/'description.txt').read_text(encoding='utf-8'))
    target = manager.project_svg(job)
    target.parent.mkdir(parents=True)
    target.write_bytes((fixture/'faded.svg').read_bytes())
    (manager.folder(job['id'])/'result.svg').write_bytes((fixture/'without_template.svg').read_bytes())
    manager.publish_best(job['id'])
    assert job['project_save']['status'] in {'unchanged', 'skipped'}
    assert target.read_bytes()==(fixture/'faded.svg').read_bytes()


@pytest.mark.parametrize('value',['false',0,None])
def test_reuse_option_rejects_ambiguous_non_boolean_values(manager,value):
    job = upload(manager)
    with pytest.raises(gui.RequestError,match='Wahrheitswert'):
        manager.start(job['id'],'Ein Rechteck.','quick',use_current_svg=value)
