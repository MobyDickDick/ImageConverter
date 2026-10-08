from pathlib import Path

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterChevronPanel import fit_chevron_panel
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_chevron_panel_recheck import chevron_panel_semantics, measure
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Rechteckiges Feld mit dünnem Rahmen und vertikalem Farbverlauf. Eine kontrastierende '
               'offene Dachlinie besteht aus zwei geraden Schenkeln, die sich oben in einer Spitze treffen.')


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, render_fn=render, error_fn=None):
    return fit_chevron_panel(image.shape[1], image.shape[0], description=description, image=image,
        render_fn=render_fn, error_fn=error_fn or (lambda a,b: normalized_mse(a,b)[0]))


@pytest.mark.parametrize('name', ['AC0554_1_L', 'AC0554_1_M', 'AC0554_1_S',
                                 'AC0554_2_L', 'AC0554_2_M', 'AC0554_2_S',
                                 'AC0554_L', 'AC0554_M', 'AC0554_S'])
def test_observed_roof_panel_generalizes_all_color_and_size_holdouts(name):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{name}.jpg'))
    result = fit(image)
    assert result is not None
    assert result['error'] < result['initial_error']
    assert chevron_panel_semantics(result['svg']) == 1.
    assert normalized_mse(image, result['rendered'])[1] < .003


def synthetic(scale=1, color='#285ba0', mark=True, valley=False, extra=''):
    w, h = 100*scale, 60*scale
    peak = 42 if valley else 12
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
           '<defs><linearGradient id="paint" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{color}"/><stop offset=".5" stop-color="#95bcda"/>'
           f'<stop offset="1" stop-color="{color}"/></linearGradient></defs>'
           f'<rect x="{10*scale}" y="{8*scale}" width="{80*scale}" height="{44*scale}" '
           f'fill="url(#paint)" stroke="#777777" stroke-width="{scale}"/>'
           + (f'<polyline points="{10*scale},{32*scale} {46*scale},{peak*scale} {90*scale},{32*scale}" '
              f'fill="none" stroke="#eeeeee" stroke-width="{3*scale}"/>' if mark else '')+extra+'</svg>')
    return svg, render(svg,w,h)


@pytest.mark.parametrize('scale,color', [(1,'#285ba0'), (2,'#b04a38')])
def test_generic_shifted_panel_with_other_colors_and_resolution(scale,color):
    _, image = synthetic(scale,color)
    result = fit(image)
    assert result is not None
    assert chevron_panel_semantics(result['svg']) == 1.
    assert normalized_mse(image,result['rendered'])[1] < .003


@pytest.mark.parametrize('kind', ['missing', 'valley', 'extra'])
def test_unsupported_topology_is_rejected(kind):
    _, image = synthetic(mark=kind!='missing', valley=kind=='valley',
                         extra='<circle cx="5" cy="55" r="4" fill="#111111"/>' if kind=='extra' else '')
    assert fit(image) is None


def test_description_renderer_and_nonfinite_error_are_hard_guards():
    _, image = synthetic()
    assert fit(image, DESCRIPTION+' Zusätzlich ein Kreis.') is None
    assert fit(image, DESCRIPTION.replace('vertikal','horizontal')) is None
    assert fit(image, render_fn=lambda *args: None) is None
    assert fit(image, error_fn=lambda *args: float('nan')) is None


def test_cli_fallback_dispatch_is_filename_invariant_and_does_not_read_reference(monkeypatch):
    _, image = synthetic()
    monkeypatch.setattr(runtime, '_try_load_sample_svg', lambda **kw: pytest.fail('reference read'))
    outputs = []
    for name in ('foreign_roof', 'unrelated_symbol'):
        logs, artifacts, params = [], [], {}
        result = runtime.runNonCompositeIterationImpl(mode='auto', params=params, stripe_strategy=None,
            semantic_mode_visual_override=False, width=image.shape[1], height=image.shape[0],
            base_name=name, description=DESCRIPTION, perc_img=image, img_path=name+'.png',
            print_fn=lambda *args:None, render_embedded_raster_svg_fn=lambda *args:pytest.fail('raster embedding'),
            build_gradient_stripe_svg_fn=lambda *args,**kw:None,
            build_gradient_stripe_validation_log_lines_fn=lambda **kw:[], write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render, record_render_failure_fn=lambda *args,**kw:None,
            write_attempt_artifacts_fn=lambda svg,raster:artifacts.append((svg,raster)),
            calculate_error_fn=lambda a,b:normalized_mse(a,b)[0])
        assert result is not None and 'raster_chevron_panel_v1' in params
        assert logs[-1] == ['status=non_composite_raster_chevron_panel']
        outputs.append(artifacts[-1])
    assert outputs[0][0] == outputs[1][0]
    np.testing.assert_array_equal(outputs[0][1],outputs[1][1])


def test_perfect_saved_pair_calibrates_metrics_and_wrong_roof_is_rejected(tmp_path):
    svg, image = synthetic()
    svg_path, image_path = tmp_path/'perfect.svg', tmp_path/'perfect.png'
    svg_path.write_text(svg, encoding='utf-8')
    assert cv2.imwrite(str(image_path), image)
    metrics = measure(image_path,svg_path)['metrics']
    assert metrics == {'error_per_pixel':0., 'edge_alignment':1., 'object_mask_iou':1.,
                       'semantic_score':1., 'dimension_match':1.}
    assert chevron_panel_semantics(synthetic(valley=True)[0]) == 0.
    assert chevron_panel_semantics(svg.replace('</svg>','<text>T</text></svg>')) == 0.


def test_recheck_runner_rejects_reused_output(tmp_path,monkeypatch):
    import sys
    from tools.run_chevron_panel_recheck import main
    output = tmp_path/'old'
    output.mkdir()
    monkeypatch.setattr(sys,'argv',['recheck','missing.json','--output-dir',str(output)])
    with pytest.raises(ValueError,match='fresh output'):
        main()


def test_baseline_archiving_cannot_remove_an_after_input(tmp_path,monkeypatch):
    import json
    import sys
    from tools import run_chevron_panel_recheck as runner
    source = tmp_path/'source.jpg'
    source.write_bytes(b'original raster bytes')
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'description':DESCRIPTION,'baseline_description':'old description',
                                   'cases':[{'case_id':'foreign_image','image':'source.jpg'}]}),encoding='utf-8')
    seen = []
    def worker(command,**kwargs):
        run_dir = Path(command[command.index('--output-dir')+1])
        mode_inputs = Path(command[command.index('--descriptions-path')-1])
        image = mode_inputs/'foreign_image.jpg'
        assert image.read_bytes() == source.read_bytes()
        seen.append(mode_inputs)
        (run_dir/'converted_svgs').mkdir(parents=True)
        (run_dir/'converted_svgs/foreign_image.svg').write_text('<svg/>',encoding='utf-8')
        (run_dir.parent/'reference_access.json').write_text('{"blocked_svg_reads":[]}',encoding='utf-8')
        if len(seen) == 1:
            # Simulate the input disappearing from the scan after archival.
            image.unlink()
    monkeypatch.setattr(runner.subprocess,'run',worker)
    monkeypatch.setattr(runner,'evaluate',lambda *args:{'satisfaction_gate':{'summary':{},'cases':[{'satisfactory':True}]}})
    monkeypatch.setattr(sys,'argv',['recheck',str(manifest),'--output-dir',str(tmp_path/'output')])
    assert runner.main() == 0
    assert seen[0] != seen[1]
    assert source.read_bytes() == b'original raster bytes'
