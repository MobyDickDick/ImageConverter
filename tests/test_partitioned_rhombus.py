"""Topology, anonymous raster registration and incomplete-candidate rejection."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterPartitionedRhombus import (
    partitioned_rhombus_spec, fit_partitioned_rhombus,
)
from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    description_assertions, validate_svg_assertions, draft_assertions, DescriptionRejected,
)
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess

ROOT=Path(__file__).resolve().parents[1]
MAIN='Eine hellgrau gefüllte, grau umrandete Raute, unterteilt in vier kleinere Rauten.'
DOUBLE=' Eine der diagonalen Trennlinien ist als schmale Doppellinie ausgeführt.'
SIGNS=' Im oberen Feld stehen ein dunkelgraues Pluszeichen und darunter ein Minuszeichen.'
BACKGROUND=' Hinter der Raute verläuft ein breites, sehr hellgraues X bis an die Bildränder.'
DESCRIPTION=MAIN+DOUBLE+SIGNS+BACKGROUND


def render(svg,w,h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


def independent_svg(scale=1, double=True, signs=True, background=True, direction=-1):
    # Authored independently: non-square canvas and rhombus, different colours,
    # dimensions, symbol proportions, rail direction and optional components.
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="180" height="150" viewBox="0 0 180 150">',
           '<rect width="180" height="150" fill="white"/>']
    if background:
        parts += ['<polyline points="0,17 24,17 156,133 180,133" fill="none" stroke="#e2e2e2" stroke-width="12"/>',
                  '<polyline points="0,133 24,133 156,17 180,17" fill="none" stroke="#e2e2e2" stroke-width="12"/>']
    parts += ['<polygon points="90,15 156,75 90,135 24,75" fill="#e1e1e1" stroke="#919191" stroke-width="1.8"/>']
    for slope in (-1,1):
        for b in ((-.04,.04) if double and slope==direction else (0,)):
            x0=(-1-slope*b)/2; x1=(1-slope*b)/2
            parts += [f'<line x1="{90+66*x0}" y1="{75+60*(slope*x0+b)}" '
                      f'x2="{90+66*x1}" y2="{75+60*(slope*x1+b)}" stroke="#919191" stroke-width="1.8"/>']
    if signs:
        parts += ['<line x1="80" y1="40" x2="100" y2="40" stroke="#606060" stroke-width="4"/>',
                  '<line x1="90" y1="30" x2="90" y2="50" stroke="#606060" stroke-width="4"/>',
                  '<line x1="81" y1="56" x2="99" y2="56" stroke="#606060" stroke-width="3"/>']
    svg=''.join(parts)+'</svg>'
    if scale!=1:
        svg=svg.replace('width="180" height="150" viewBox=',f'width="{180*scale}" height="{150*scale}" viewBox=',1)
    return svg,180*scale,150*scale


def fit(image,description):
    return fit_partitioned_rhombus(image.shape[1],image.shape[0],description=description,image=image,
        render_fn=render,error_fn=lambda a,b:float(np.square(a.astype(float)-b).mean()/255**2))


def test_subregions_are_owned_by_one_parent_and_complete_dispatch_is_anonymous():
    for name in ('anonymous','another_upload'):
        _,params=Reflection({name:DESCRIPTION}).parseDescription(name,name+'.png')
        assert params['mode']=='non_composite' and params['geometry_ir']==[] and params['label']==''
        assert params['language_assertions']['objects']==dict(rhombus=1,diagonal=5,line=4)
        assert params['language_assertions']['partitioned_rhombus']==dict(double=True,signs='oberen',background=True)


def test_clauses_are_composable_and_accept_alternate_subdivision_wording():
    assert partitioned_rhombus_spec(MAIN)==dict(double=False,signs=False,background=False)
    alternate=('Eine grau umrandete, hellgrau gefüllte Raute ist in 4 kleine Rauten aufgeteilt.'
               +BACKGROUND+SIGNS+' Eine der diagonalen Trennlinien besteht aus zwei parallelen Linien.')
    assert partitioned_rhombus_spec(alternate)==partitioned_rhombus_spec(DESCRIPTION)


@pytest.mark.parametrize('extra',[' Zusätzlich ein Kreis.',' Ohne Pluszeichen.',' Die Raute ist rot.',' Ein zweites X.'])
def test_unknown_or_conflicting_claims_are_not_ignored(extra):
    assert partitioned_rhombus_spec(DESCRIPTION+extra) is None


@pytest.mark.parametrize('draft',[False,True])
@pytest.mark.parametrize('fault',['outline','rail','minus','plus','background','order','paint','endpoint','cell'])
def test_incomplete_or_wrong_topology_is_rejected_even_as_draft(draft,fault):
    svg,_,_=independent_svg()
    root=ET.fromstring(svg)
    children=list(root)
    if fault=='outline': root.remove(children[3])
    elif fault=='rail': root.remove(children[4])
    elif fault=='minus': root.remove(children[-1])
    elif fault=='plus': children[-2].set('x1','91')
    elif fault=='background': root.remove(children[1])
    elif fault=='order': root.remove(children[1]);root.append(children[1])
    elif fault=='paint': children[3].set('fill','#ee9999')
    elif fault=='endpoint': children[4].set('x1','45')
    elif fault=='cell': children[-1].set('y1','95');children[-1].set('y2','95')
    assertions=description_assertions(DESCRIPTION)
    with pytest.raises(DescriptionRejected):
        validate_svg_assertions(ET.tostring(root,encoding='unicode'),draft_assertions(assertions) if draft else assertions)


@pytest.mark.parametrize('double,signs,background,direction,scale',[
    (True,True,True,-1,1),(True,True,True,1,1),(False,False,False,1,1),
    (False,True,True,1,2),
])
def test_independent_sizes_proportions_and_optional_parts(double,signs,background,direction,scale):
    description=MAIN+(DOUBLE if double else '')+(SIGNS if signs else '')+(BACKGROUND if background else '')
    svg,w,h=independent_svg(scale,double,signs,background,direction)
    validate_svg_assertions(svg,description_assertions(description))
    result=fit(render(svg,w,h),description)
    assert result is not None and result['quality']['passed'],result
    validate_svg_assertions(result['svg'],description_assertions(description))


def test_reported_catalog_image_with_unchanged_description():
    description=next(e.get('beschreibung') for e in ET.parse(ROOT/'artifacts/descriptions/Finale_Wurzelformen_V3.xml').iter('bild') if e.text=='AC0160_M.jpg')
    result=fit(cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0160_M.jpg')),description)
    assert result is not None and result['quality']['passed']
    assert result['error']<result['initial_error']
    validate_svg_assertions(result['svg'],description_assertions(description))


def test_real_gui_worker_converts_anonymous_upload_without_template(tmp_path,monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    jobs=gui.Jobs(tmp_path/'jobs')
    jobs.project_directory=tmp_path/'project'
    try:
        job=jobs.upload('neutral_partition.jpg',(ROOT/'artifacts/images_to_convert/AC0160_M.jpg').read_bytes())
        started=jobs.start(job['id'],DESCRIPTION,'normal',seed=2026,use_current_svg=False)
        jobs.threads[-1].join(timeout=90)
        result=jobs.snapshot(started['id'])
        assert result['status']=='done' and result['quality']=='passed',result
        assert result['description']==DESCRIPTION
        validate_svg_assertions((jobs.folder(result['id'])/'result.svg').read_text(encoding='utf-8'),description_assertions(DESCRIPTION))
        assert result['project_save']['status']=='saved'
    finally:
        jobs.close()
