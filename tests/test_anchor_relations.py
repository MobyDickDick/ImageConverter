"""Parent anchors, coupled symmetry, paint direction and clipping, without IDs."""
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterRelations import anchor_relations, fit_relational_scene, validate_anchor_relations
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.imageConverterSample import render_svg

ROOT=Path(__file__).resolve().parents[1]
POINTS={'oberen':(.5,0), 'unteren':(.5,1), 'linken':(0,.5), 'rechten':(1,.5)}


def render(svg,w,h):
    return render_svg(svg,w,h)[:,:,::-1].copy()


def example(direction='right',axis='horizontal',color='rot',width=100,height=80):
    ends={'right':[('oberen','rechten'),('unteren','rechten')],
          'left':[('oberen','linken'),('unteren','linken')],
          'up':[('linken','oberen'),('rechten','oberen')],
          'down':[('linken','unteren'),('rechten','unteren')]}[direction]
    symmetry='waagrechten' if direction in {'right','left'} else 'senkrechten'
    desc=(f'Rechteck mit grauer Umrandung und {axis}em {color}em Farbverlauf. '
          f'Zwei weisse Linien sind symmetrisch zu einer {symmetry} Symmetrieachse. ')
    for name,(start,end) in zip(('erste','zweite'),ends):
        desc+=f'Die {name} Linie geht von der Mitte des {start} Rands bis zur Mitte des {end} Rands. '
    desc+='Die Linien werden unter den Rand des Rechtecks gelegt und am Rand abgeschnitten.'
    dark,light={'rot':('#b52a42','#ed6878'),'blau':('#285cb4','#7daee0'),
                'grün':('#27853b','#73c189'),'grau':('#777777','#cccccc')}[color]
    gradient='x1="0" x2="1" y1="0" y2="0"' if axis=='horizontal' else 'x1="0" x2="0" y1="0" y2="1"'
    l,t,r,b=8.5,7.5,width-8.5,height-7.5
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
         f'<defs><linearGradient id="p" {gradient}><stop stop-color="{dark}"/>'
         f'<stop offset=".4" stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></linearGradient></defs>'
         f'<rect width="{width}" height="{height}" fill="white"/>'
         f'<rect x="{l}" y="{t}" width="{r-l}" height="{b-t}" fill="url(#p)"/>')
    for i,(start,end) in enumerate(ends):
        a,z=np.array([POINTS[start],POINTS[end]])*[r-l,b-t]+[l,t]
        svg+=f'<line id="stroke{i}" x1="{a[0]}" y1="{a[1]}" x2="{z[0]}" y2="{z[1]}" stroke="white" stroke-width="2"/>'
    svg+=f'<rect x="{l}" y="{t}" width="{r-l}" height="{b-t}" fill="none" stroke="#999999" stroke-width="1"/></svg>'
    return desc,svg,width,height


@pytest.mark.parametrize('direction,axis,color', [
    ('right','horizontal','rot'),('right','vertikal','blau'),
    ('left','horizontal','grün'),('left','vertikal','grau'),
    ('up','horizontal','blau'),('up','vertikal','grün'),
    ('down','horizontal','grau'),('down','vertikal','rot'),
])
def test_same_anchor_solver_handles_all_orientations_both_paint_axes_and_palettes(direction,axis,color):
    desc,svg,w,h=example(direction,axis,color)
    image=render(svg,w,h)
    result=fit_relational_scene(w,h,description=desc,image=image,render_fn=render,
        error_fn=lambda a,b:float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
    assert result is not None
    validate_svg_assertions(result['svg'],description_assertions(desc))
    assert pixel_quality(image,result['rendered'])['normalized_mse'] < .003
    assert len(ET.fromstring(result['svg']).findall('{*}polygon'))==2
    assert len(result['anchor_offsets'])==1  # mirrored ports share their coordinate


@pytest.mark.parametrize('damage',['missing','wrong_endpoint','hidden','color','above_frame'])
def test_relationships_require_visible_correctly_placed_foreground_under_frame(damage):
    desc,svg,w,h=example()
    root=ET.fromstring(svg);node=root.find(".//*[@id='stroke0']")
    if damage=='missing':root.remove(node)
    elif damage=='wrong_endpoint':node.set('x2',node.get('x1'))
    elif damage=='hidden':node.set('opacity','0')
    elif damage=='color':node.set('stroke','#b52a42')
    else:
        root.remove(node);root.append(node)
    with pytest.raises(ValueError,match='anchor_relation:'):
        validate_anchor_relations(ET.tostring(root,encoding='unicode'),anchor_relations(desc))


def test_conflicting_symmetry_and_quoted_directions_do_not_make_new_geometry():
    desc,svg,w,h=example()
    with pytest.raises(ValueError,match='conflicting_symmetry'):
        anchor_relations(desc.replace('waagrechten','senkrechten'))
    assert anchor_relations('Rechteck. "'+desc+'"') is None
    claims=anchor_relations(desc.replace('von der Mitte','von genau der Mitte'))
    assert claims['anchor_tolerance']==0.


@pytest.mark.parametrize('damage',['gradient_axis','fill_color','unclipped_paint'])
def test_visible_paint_constraints_are_checked_independently_of_the_source(damage):
    desc,svg,w,h=example()
    root=ET.fromstring(svg)
    if damage=='gradient_axis':
        gradient=root.find('.//{*}linearGradient')
        gradient.set('x2','0');gradient.set('y2','1')
    elif damage=='fill_color':
        for node in root.findall('.//{*}stop'):
            node.set('stop-color','#2255bb' if node.get('offset')!='.4' else '#6699ee')
    else:
        root.findall('{*}rect')[0].set('fill','#335577')
        node=root.find(".//*[@id='stroke0']")
        a=np.array([float(node.get('x1')),float(node.get('y1'))])
        b=np.array([float(node.get('x2')),float(node.get('y2'))])
        end=b+(b-a)*.4
        node.set('x2',str(end[0]));node.set('y2',str(end[1]))
    with pytest.raises(ValueError,match='anchor_relation:'):
        validate_anchor_relations(ET.tostring(root,encoding='unicode'),anchor_relations(desc))


@pytest.mark.parametrize('damage',['independent_move','independent_width'])
def test_pixel_passing_independent_edits_cannot_break_symmetry(damage):
    desc,svg,w,h=example()
    root=ET.fromstring(svg);node=root.find(".//*[@id='stroke1']")
    if damage=='independent_move':
        node.set('transform','translate(0 -.5) translate(50 40) scale(.97 1) translate(-50 -40)')
    else:
        node.set('stroke-width','2.2')
    candidate=ET.tostring(root,encoding='unicode')
    assert pixel_quality(render(svg,w,h),render(candidate,w,h))['passed']
    with pytest.raises(ValueError,match='anchor_relation:inconsistent_endpoints_or_symmetry'):
        validate_anchor_relations(candidate,anchor_relations(desc))


def test_invalid_parameter_refinement_retains_the_verified_construction(monkeypatch):
    from src.iCCModules import imageCompositeConverterFilledSymbols as fits
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    desc,svg,w,h=example()
    root=ET.fromstring(svg);root.find(".//*[@id='stroke1']").set('transform','translate(0 -1)')
    wrong=ET.tostring(root,encoding='unicode')
    pixels=render(svg,w,h);target=np.clip(pixels.astype(float)-12,0,255).astype(np.uint8)
    def invalid(*args,**kwargs):
        return dict(svg=wrong,rendered=render(wrong,w,h),error=0.,evaluations=1)
    monkeypatch.setattr(fits,'_register',invalid)
    with image_search(ImageSearch(SearchPolicy(seconds=3,max_seconds=3))):
        result=polish_generated_svg(svg,target,render,assertions=description_assertions(desc),structure_mode='off')
    assert result is not None and result.get('refinement_reverted_for_description')
    validate_svg_assertions(result['svg'],description_assertions(desc))
    assert np.array_equal(result['rendered'],pixels)


def test_normal_gui_result_checks_relations_even_when_exit_code_and_pixels_pass(tmp_path):
    from src import imageConverterGui as gui
    desc,svg,w,h=example()
    cv2.imwrite(str(tmp_path/'source.png'),render(svg,w,h))
    root=ET.fromstring(svg);root.find(".//*[@id='stroke1']").set('transform','translate(0 -.5)')
    output=tmp_path/'output/converted_svgs';output.mkdir(parents=True)
    (output/'UPLOAD.svg').write_text(ET.tostring(root,encoding='unicode'),encoding='utf-8')
    job=dict(description=desc)
    gui.collect_result(tmp_path,job,0)
    assert job['pixel_quality']['passed']
    assert not job['result'] and job['quality']=='warning'
    assert job['result_rejection']=='description_inventory'
    assert 'anchor_relation:' in job['description_error']
    assert job['description_validation_version']==gui.DESCRIPTION_VALIDATION_VERSION


def test_anchor_graph_can_add_a_third_shared_segment_without_a_new_model():
    desc,svg,w,h=example()
    desc=desc.replace('Zwei weisse','Drei weisse')+(' Die dritte Linie geht von der Mitte des linken Rands '
            'bis zur Mitte des rechten Rands.')
    root=ET.fromstring(svg)
    node=ET.Element('{http://www.w3.org/2000/svg}line',x1='8.5',y1=str(h/2),
                    x2=str(w-8.5),y2=str(h/2),stroke='white',**{'stroke-width':'2'})
    root.insert(len(root)-1,node)
    image=render(ET.tostring(root,encoding='unicode'),w,h)
    result=fit_relational_scene(w,h,description=desc,image=image,render_fn=render,
        error_fn=lambda a,b:float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
    assert result is not None and len(result['relations']['lines'])==3
    validate_svg_assertions(result['svg'],description_assertions(desc))


@pytest.mark.parametrize('count',[1,2])
def test_parent_anchors_also_work_on_flat_fields_and_for_one_line(count):
    desc,svg,w,h=example()
    desc=desc.replace('Rechteck mit grauer Umrandung und horizontalem rotem Farbverlauf.',
                      'Graues Rechteck mit grauer Umrandung.')
    root=ET.fromstring(svg);root.findall('{*}rect')[1].set('fill','#777777')
    if count==1:
        desc=desc.replace('Zwei weisse Linien sind symmetrisch zu einer waagrechten Symmetrieachse.','Eine weisse Linie.')
        desc=re.sub(r'Die zweite Linie[^.]*\.','',desc)
        root.remove(root.find(".//*[@id='stroke1']"))
    image=render(ET.tostring(root,encoding='unicode'),w,h)
    result=fit_relational_scene(w,h,description=desc,image=image,render_fn=render,
        error_fn=lambda a,b:float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
    assert result is not None
    validate_svg_assertions(result['svg'],description_assertions(desc))
    assert not ET.fromstring(result['svg']).findall('.//{*}linearGradient')
    assert len(result['relations']['lines'])==count


def test_actual_compressed_upload_and_unchanged_description():
    image=cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0150_1.jpg'));h,w=image.shape[:2]
    desc=ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        ".//bild[.='AC0150_1.jpg']").get('beschreibung')
    result=fit_relational_scene(w,h,description=desc,image=image,render_fn=render,
        error_fn=lambda a,b:float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
    assert result is not None and result['quality']['passed']
    validate_svg_assertions(result['svg'],description_assertions(desc))
    assert result['relations']['gradient_axis']=='x'
    assert result['relations']['fill_color']=='red'
    assert result['quality']['edge_alignment']>.8
    # Check the actual polygons, including clipping and mirrored port offsets.
    root=ET.fromstring(result['svg']);field=root.findall('{*}rect')[1]
    x,y,width,height=(float(field.get(k)) for k in ('x','y','width','height'))
    polygons=[np.fromstring(n.get('points').replace(',',' '),sep=' ').reshape(-1,2) for n in root.findall('{*}polygon')]
    reflected=polygons[0].copy();reflected[:,1]=2*y+height-reflected[:,1]
    assert max(min(np.linalg.norm(polygons[1]-point,axis=1)) for point in reflected)<1e-4
    assert all(np.all(p >= [x-1e-5,y-1e-5]) and np.all(p <= [x+width+1e-5,y+height+1e-5]) for p in polygons)


def test_fresh_conversion_dispatch_uses_relations_under_neutral_filename(monkeypatch):
    from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
    desc,svg,w,h=example('left','horizontal','grün')
    image=render(svg,w,h);saved=[];params={}
    monkeypatch.setattr(runtime,'_try_load_sample_svg',lambda **kwargs:pytest.fail('reference read'))
    result=runtime.runNonCompositeIterationImpl(mode='insufficient_description',params=params,stripe_strategy=None,
        semantic_mode_visual_override=False,width=w,height=h,base_name='foreign',description=desc,perc_img=image,
        img_path='foreign.png',print_fn=lambda *args:None,render_embedded_raster_svg_fn=lambda *args:pytest.fail('embedded raster'),
        build_gradient_stripe_svg_fn=lambda *args,**kwargs:None,build_gradient_stripe_validation_log_lines_fn=lambda **kwargs:[],
        write_validation_log_fn=lambda *args:None,render_svg_to_numpy_fn=render,record_render_failure_fn=lambda *args,**kwargs:None,
        write_attempt_artifacts_fn=lambda svg,*args:saved.append(svg),
        calculate_error_fn=lambda a,b:float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
    assert result is not None and saved
    validate_svg_assertions(saved[-1],description_assertions(desc))
    assert params['primitive_scene_registration']['source']=='raster_relational_scene_v1'
