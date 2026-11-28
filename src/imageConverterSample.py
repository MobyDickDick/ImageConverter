"""Refine an explicitly uploaded SVG against its source raster, in a bounded worker."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
from src.iCCModules.imageCompositeConverterAdaptiveSearch import tracked_renderer

SVG_NS = "http://www.w3.org/2000/svg"
MAX_SAMPLE_BYTES = 2 * 1024 * 1024
NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")
TAGS = {"svg", "g", "defs", "circle", "ellipse", "rect", "path", "line", "polyline", "polygon",
        "text", "tspan", "linearGradient", "radialGradient", "stop", "clipPath", "mask", "pattern",
        "title", "desc", "metadata", "style"}
SCALARS = {"x", "y", "cx", "cy", "x1", "y1", "x2", "y2", "r", "rx", "ry", "width", "height",
           "stroke-width", "font-size", "opacity", "fill-opacity", "stroke-opacity", "stop-opacity"}
POSITIVE = {"r", "rx", "ry", "width", "height", "stroke-width", "font-size"}
EDITOR_NAMESPACES = {"http://www.inkscape.org/namespaces/inkscape",
                     "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"}


def prepare_sample(data: bytes, width: int, height: int) -> str:
    """Accept standalone vector SVGs, never active content or external resources."""
    if not data or len(data) > MAX_SAMPLE_BYTES:
        raise ValueError("Die Sample-Datei darf maximal 2 MB gross sein.")
    text = data.decode("utf-8-sig")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)|<\?xml-stylesheet", text, re.I):
        raise ValueError("Bitte ein eigenständiges SVG ohne externe Ressourcen hochladen.")
    root = ET.fromstring(text)
    from src.iCCModules.imageCompositeConverterVectorPolicy import pixel_copy_reason
    if pixel_copy_reason(root):
        raise ValueError('Pixelkopien und eingebettete Rasterbilder sind keine geometrische SVG-Vorlage.')
    if root.tag not in {"svg", f"{{{SVG_NS}}}svg"}:
        raise ValueError("Die Sample-Datei muss ein SVG sein.")
    elements = list(root.iter())
    if len(elements) > 1500:
        raise ValueError("Das Sample enthält zu viele Elemente (maximal 1500).")
    stack = [(root, 0)]
    while stack:
        element, depth = stack.pop()
        if depth > 64:
            raise ValueError("Das Sample enthält zu tief verschachtelte Gruppen.")
        stack.extend((child, depth + 1) for child in element)
    # Editor views, guides and RDF metadata are not rendered SVG geometry.
    # Discard them, while retaining the strict validation of all visual nodes.
    for parent in list(root.iter()):
        for child in list(parent):
            namespace = child.tag[1:].split('}', 1)[0] if child.tag.startswith('{') else ''
            if namespace in EDITOR_NAMESPACES or child.tag.rsplit('}', 1)[-1] == 'metadata':
                parent.remove(child)
    elements = list(root.iter())
    by_id = {}
    for element in elements:
        if element.get('id'):
            by_id.setdefault(element.get('id'), []).append(element)
    gradient_links = {}
    for element in elements:
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in TAGS or (element.tag.startswith("{") and not element.tag.startswith("{" + SVG_NS + "}")):
            raise ValueError(f"Das Sample enthält ein nicht unterstütztes Element: {tag}.")
        for key, value in element.attrib.items():
            attribute = key.rsplit("}", 1)[-1].lower()
            if attribute.startswith("on") or attribute == "src":
                raise ValueError("Das Sample muss ausschliesslich eigenständige SVG-Formen enthalten.")
            if attribute == 'href':
                targets = by_id.get(value[1:], []) if re.fullmatch(r'#[^\s#]+', value) else []
                if (key not in {'href', '{http://www.w3.org/1999/xlink}href'}
                        or tag not in {'linearGradient', 'radialGradient'}
                        or len(targets) != 1 or targets[0].tag != element.tag):
                    raise ValueError('Das Sample darf nur lokale Verweise auf eindeutige Farbverläufe desselben Typs enthalten.')
                target = targets[0]
                if element in gradient_links and gradient_links[element] is not target:
                    raise ValueError('Das Sample enthält widersprüchliche Farbverlaufsverweise.')
                gradient_links[element] = target
            if len(value) > 250000:
                raise ValueError("Das Sample enthält einen zu komplexen Pfad.")
        content = " ".join(element.attrib.values()) + " " + (element.text or "")
        if re.search(r"@import|javascript\s*:|expression\s*\(", content, re.I):
            raise ValueError("Aktive Inhalte sind in einer Sample-Datei nicht erlaubt.")
        for resource in re.findall(r"url\s*\((.*?)\)", content, re.I):
            if not resource.strip(" \t\r\n\"'").startswith("#"):
                raise ValueError("Das Sample darf keine externen Ressourcen laden.")
        for key in list(element.attrib):
            if key.startswith('{') and key[1:].split('}', 1)[0] in EDITOR_NAMESPACES:
                del element.attrib[key]
    # Fragment links reuse paint within this document. Check chains without
    # recursion: XML nesting limits do not bound gradient inheritance depth.
    for element in gradient_links:
        visiting = set()
        while element in gradient_links:
            if element in visiting:
                raise ValueError('Das Sample enthält einen zyklischen Farbverlaufsverweis.')
            if len(visiting) >= 64:
                raise ValueError('Das Sample enthält eine zu lange Farbverlaufskette (maximal 64 Verweise).')
            visiting.add(element)
            element = gradient_links[element]
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    root = ET.fromstring(inline_simple_svg_styles(ET.tostring(root, encoding="unicode")))
    if not root.get("viewBox"):
        original_w = NUMBER.match(root.get("width", ""))
        original_h = NUMBER.match(root.get("height", ""))
        w = float(original_w[0]) if original_w else width
        h = float(original_h[0]) if original_h else height
        root.set("viewBox", f"0 0 {w:g} {h:g}")
    values = NUMBER.findall(root.get("viewBox", ""))
    if len(values) != 4 or not all(math.isfinite(float(v)) for v in values) or min(map(float, values[2:])) <= 0:
        raise ValueError("Das Sample hat keine gültige SVG-Zeichenfläche.")
    root.set("width", str(width))
    root.set("height", str(height))
    ET.register_namespace("", SVG_NS)
    return ET.tostring(root, encoding="unicode")


def parameters(root):
    """Editable paint/geometry values; paths with arc flags remain intact."""
    from PIL import ImageColor
    result = []
    for node in root.iter():
        if node is root:
            continue
        for attribute, value in list(node.attrib.items()):
            if attribute in SCALARS and re.fullmatch(NUMBER.pattern + r"(?:px|%)?", value.strip()):
                result.append((node, attribute, "scalar", 0))
            elif attribute == "points" or (attribute == "d" and not re.search("[Aa]", value)):
                for index, number in enumerate(NUMBER.findall(value)):
                    if math.isfinite(float(number)):
                        result.append((node, attribute, "list", index))
            elif attribute in {"fill", "stroke", "stop-color"}:
                try:
                    rgb = ImageColor.getrgb(value)
                    if len(rgb) == 3:
                        node.set(attribute, "#%02x%02x%02x" % rgb)
                        result.extend((node, attribute, "color", channel) for channel in range(3))
                except ValueError:
                    pass
        if len(result) > 3000:
            raise ValueError("Das Sample enthält zu viele veränderbare Parameter (maximal 3000).")
    return result


def adjusted(value, kind, index, delta, attribute):
    if kind == "color":
        rgb = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
        rgb[index] = max(0, min(255, round(rgb[index] + delta)))
        return "#%02x%02x%02x" % tuple(rgb)
    matches = list(NUMBER.finditer(value))
    match = matches[index]
    number = float(match[0]) + delta
    if attribute in POSITIVE:
        number = max(0.01, number)
    elif attribute.endswith("opacity"):
        number = max(0, min(1, number))
    if not math.isfinite(number):
        return value
    return value[:match.start()] + f"{number:.5f}".rstrip("0").rstrip(".") + value[match.end():]


@tracked_renderer
def render_svg(svg, width, height):
    import fitz
    import numpy as np
    import cv2
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
    # Use the same private gradient adapters as the converter: this PyMuPDF
    # build otherwise paints native SVG gradients black during GUI validation.
    image = render_svg_to_numpy_inprocess(svg, width, height,
        fitz_module=fitz, np_module=np, cv2_module=cv2, constrain_canvas=True)
    if image is None:
        raise ValueError("Das SVG konnte nicht gerendert werden.")
    if image.shape[:2] != (height, width):
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    from src.imageConverterPreview import publish_preview
    publish_preview(svg, image)
    # The converter works in BGR; uploaded samples and Pillow sources use RGB.
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def refit_description(source, output, description, *, seed, hard_deadline, initial_mse,
                      initial_quality, template_error, started):
    """Discard an incompatible template and run the ordinary first-stage CLI.

    This is description-based construction, never the removed raster recovery.
    The caller's deadline includes process startup and all fitting work.
    """
    import csv
    import os
    import shutil
    import subprocess
    import sys
    import tempfile
    import numpy as np
    from PIL import Image
    from src.imageConverterCatalog import atomic_json
    from src.imageConverterRecovery import atomic_svg
    from src.imageConverterGui import catalog_descriptions, search_summary
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
    from src.iCCModules.imageCompositeConverterCanvas import contain_svg

    output.parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='description-fit-', dir=output.parent))
    inputs = folder/'input'
    inputs.mkdir()
    shutil.copyfile(source, inputs/'UPLOAD.png')
    table = folder/'description.csv'
    with table.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Wurzelform', 'Beschreibung'])
        writer.writerows(catalog_descriptions().items())
        writer.writerow(['UPLOAD', description])
    remaining = max(0., hard_deadline-time.monotonic())
    report = dict(passed=False, result=False, improved=False, evaluations=0, accepted=0,
        continuation=None, alignment=None, search_seed=str(seed),
        initial_mse=initial_mse, initial_quality=initial_quality,
        template_rejection=template_error, restarted_from_description=True,
        description_fit_directory=str(folder), stop_reason='description_fit_failed',
        description_error=template_error, message='Die Vorlage passt nicht zur Beschreibung. '
        'Auch die neue Konvertierung aus der Beschreibung hat noch kein passendes SVG ergeben.')
    print('Vorlage verworfen: '+template_error+'. Starte neue Konvertierung aus der Bildbeschreibung.', flush=True)
    import hashlib
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
    session = current_search()
    state = session.handoff(deadline=hard_deadline)
    state['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    handoff_path = folder/'search-context.json'
    atomic_json(handoff_path, state)
    command = [sys.executable, '-u', '-m', 'src.imageCompositeConverter', str(inputs.resolve()),
        '--descriptions-path', str(table.resolve()), '--output-dir', str((folder/'output').resolve()),
        '--start', 'UPLOAD', '--end', 'UPLOAD', '--execution-mode', 'semantic-only',
        '--no-isolate-conversion', '--search-seconds', str(max(.01, remaining)),
        '--search-max-seconds', str(max(.01, remaining)), '--search-min-seconds', '0',
        '--search-seed', str(seed), '--fail-on-batch-failures',
        '--search-budget', str(session.render_budget), '--search-context', str(handoff_path.resolve()),
        '--log-file', str((folder/'converter.log').resolve())]
    environment = dict(os.environ, PYTHONIOENCODING='utf-8', ICC_MAX_QUALITY_PASSES='0',
        IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', IMAGE_CONVERTER_REUSE_RENDER_WORKER='0',
        ICC_GUI_PREVIEW_PHASE='Beschreibungskonvertierung')
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
    if remaining > .1:
        try:
            with (folder/'console.log').open('wb') as log:
                completed = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=environment,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    timeout=remaining, **options)
            report['description_fit_returncode'] = completed.returncode
        except subprocess.TimeoutExpired:
            report['stop_reason'] = 'time_limit'
    else:
        report['stop_reason'] = 'time_limit'
    summary = search_summary(folder/'output')
    completed_context = Path(str(handoff_path)+'.completed.json')
    if completed_context.is_file():
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch
        returned = ImageSearch.from_handoff(json.loads(completed_context.read_text(encoding='utf-8')))
        for name in ('renderings', 'render_failures', 'render_cache_hits', 'render_sequence_sha256',
                     'render_memo', 'render_memo_bytes', 'candidates'):
            setattr(session, name, getattr(returned, name))
    if summary:
        report['description_search_summary'] = summary
        report['evaluations'] = summary['candidate_evaluations']
        # The child journal includes the inherited prefix, not another budget.
        session.renderings = summary.get('renderings', session.renderings)
        session.render_cache_hits = summary.get('render_cache_hits', session.render_cache_hits)
        session.render_sequence_sha256 = summary.get('render_sequence_sha256', session.render_sequence_sha256)
    assertions = description_assertions(description)
    with Image.open(source) as image:
        target = np.asarray(image.convert('RGB'))
    h, w = target.shape[:2]
    candidates = []
    paths = [path for name in ('converted_svgs', 'converted_svg_failed')
             for path in (folder/'output'/name).glob('*.svg')]
    for path in paths:
        try:
            svg = contain_svg(path.read_text(encoding='utf-8'), w, h)
            validate_svg_assertions(svg, assertions)
            # Reuse the exact child render, including when its final proposal
            # spent the remaining budget. The CLI cache uses BGR pixels.
            from src.iCCModules.imageCompositeConverterAdaptiveSearch import candidate_identity, raster_identity
            renderer = 'src.imageCompositeConverter.Action.renderSvgToNumpy'
            bgr_target = target[:, :, ::-1].copy()
            key = (raster_identity(bgr_target), renderer, w, h, candidate_identity(svg))
            if key in session.render_memo:
                import cv2
                bgr, _ = session.render_candidate(bgr_target, svg, lambda *a: None, w, h, renderer=renderer)
                pixels = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if bgr is not None else None
            else:
                pixels = render_svg(svg, w, h)
            if pixels is None:
                continue
            quality = pixel_quality(target, pixels)
            error = float(np.square(target.astype(float)-pixels.astype(float)).mean()/255**2)
            passed = bool(quality['passed'] and report.get('description_fit_returncode') == 0
                          and path.parent.name == 'converted_svgs' and not path.name.startswith('Failed_'))
            candidates.append((not passed, error, svg, quality))
        except (ValueError, OSError, SyntaxError):
            continue
    if candidates:
        failed, error, svg, quality = min(candidates, key=lambda item: item[:2])
        atomic_svg(output, svg)
        report.update(result=True, passed=not failed, final_mse=error, final_quality=quality,
            improved=initial_mse is not None and error < initial_mse-1e-10, stop_reason='description_fit_complete',
            message='Unpassende Vorlage verworfen; SVG neu aus der Bildbeschreibung erstellt.')
    report['elapsed'] = round(time.monotonic()-started, 2)
    atomic_json(output.with_suffix('.json'), report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


def refine(source: Path, sample: Path, output: Path, description: str, seconds: float, *, seed=None, deadline=None) -> dict:
    from src.iCCModules.imageCompositeConverterSearchPortfolio import standalone_image_search
    from src.iCCModules.imageCompositeConverterSceneProgram import scene_program
    program=scene_program(description)
    with standalone_image_search(str(source.resolve()), seconds=seconds, seed=seed,
                                 directory=output.parent/'search',
                                 render_budget=4096 if program and program.get('paint_claims') else 384) as session:
        report = _refine(source, sample, output, description, seconds, seed=seed, deadline=deadline)
        report['search_context'] = session.report()
        report['evaluations'] = session.renderings
        from src.imageConverterCatalog import atomic_json
        atomic_json(output.with_suffix('.json'), report)
        return report


def _refine(source: Path, sample: Path, output: Path, description: str, seconds: float, *, seed=None, deadline=None) -> dict:
    started = time.monotonic()
    hard_deadline = started+seconds
    if deadline is not None:
        hard_deadline = min(hard_deadline, started+max(0., deadline-time.time()-.25))
    import numpy as np
    from PIL import Image
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality, preferred_quality, vector_candidate_quality, vector_quality_score
    from src.iCCModules.imageCompositeConverterSearchPortfolio import settings
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    from src.iCCModules.imageCompositeConverterSimilarity import resolve_catalog_similarity_description
    from src.iCCModules.imageCompositeConverterStrokeConstraints import constrain_stroke_width
    from src.iCCModules.imageCompositeConverterCanvas import contain_svg

    config = settings()
    effective_seed = (config['seed'] if config else 0) if seed is None else seed
    if type(effective_seed) is not int or not 0 <= effective_seed < 2**64:
        raise ValueError('Seed muss eine ganze Zahl zwischen 0 und 2^64-1 sein.')
    description = resolve_catalog_similarity_description(description, Path(__file__).resolve().parents[1]).text

    with Image.open(source) as image:
        target = np.asarray(image.convert("RGB"))
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
    current_search().bind_reference(target)
    height, width = target.shape[:2]
    root = ET.fromstring(prepare_sample(sample.read_bytes(), width, height))
    prepared = contain_svg(ET.tostring(root, encoding="unicode"), width, height)
    root = ET.fromstring(prepared)
    assertions = description_assertions(description)
    from src.iCCModules.imageCompositeConverterSceneProgram import scene_program, sample_parameters
    program=scene_program(description)
    if program and program.get('paint_claims'):
        initial=sample_parameters(program,prepared,width,height)
        if initial is not None:
            from src.iCCModules.imageCompositeConverterPrimitiveEvolution import evolve_primitives
            from src.imageConverterRecovery import atomic_svg
            from src.imageConverterCatalog import atomic_json
            initial_rendered,_=current_search().render_candidate(target,prepared,render_svg,width,height)
            initial_quality=pixel_quality(target,initial_rendered) if initial_rendered is not None else None
            fitted=evolve_primitives(target,description,render_svg,
                seed=effective_seed,seconds=max(.001,hard_deadline-time.monotonic()),
                initial_parameters=initial,color_order='RGB')
            if fitted and fitted['valid']:
                if fitted['quality']['passed']:
                    from src.iCCModules.imageCompositeConverterAdaptiveSearch import candidate_scope
                    with candidate_scope('full_scene','scoped_sample'):
                        current_search().validate(fitted,target)
                atomic_svg(output,fitted['svg'])
                report=dict(result=True,passed=fitted['quality']['passed'],final_mse=fitted['error'],
                    initial_mse=initial_quality['normalized_mse'] if initial_quality else None,
                    initial_quality=initial_quality,
                    improved=bool(initial_quality and fitted['error']<initial_quality['normalized_mse']-1e-10),
                    final_quality=fitted['quality'],description_error='',
                    search_seed=str(effective_seed),stop_reason=fitted['search_report']['stop_reason'],
                    primitive_evolution=fitted['search_report'],elapsed=round(time.monotonic()-started,2),
                    message='Vorlagenformen mit allen beschriebenen Rändern und Verläufen neu angepasst.')
                atomic_json(output.with_suffix('.json'),report)
                return report
    constrained = contain_svg(constrain_stroke_width(prepared, assertions), width, height)
    initial_description_error = ''
    try:
        validate_svg_assertions(constrained, assertions)
    except ValueError as exc:
        initial_description_error = str(exc)
        from src.iCCModules.imageCompositeConverterSampleAlignment import compatible_sample_pose
        # A stale current SVG is optional input, never a prerequisite for
        # conversion. First allow orientation to satisfy directional claims.
        if not compatible_sample_pose(ET.fromstring(constrained), width, height, assertions, deadline=hard_deadline):
            initial = None if current_search().reason() else render_svg(prepared, width, height)
            initial_quality = pixel_quality(target, initial) if initial is not None else None
            initial_mse = initial_quality['normalized_mse'] if initial_quality else None
            return refit_description(source, output, description, seed=effective_seed,
                hard_deadline=hard_deadline, initial_mse=initial_mse, initial_quality=initial_quality,
                template_error=str(exc), started=started)
    rendered = render_svg(prepared, width, height)
    if rendered is None:
        return dict(passed=False, result=False, stop_reason=current_search().reason() or 'render_failure',
                    description_error='', search_seed=str(effective_seed), elapsed=time.monotonic()-started)
    initial_rendered = rendered.copy()
    initial_mse = float(np.square(target.astype(np.float32)-rendered.astype(np.float32)).mean()/255**2)
    initial_quality = pixel_quality(target, rendered)
    if constrained != prepared:
        root = ET.fromstring(constrained)
        rendered = render_svg(constrained, width, height)
        if rendered is None:
            return dict(passed=False, result=False, stop_reason=current_search().reason() or 'render_failure',
                        description_error='', search_seed=str(effective_seed), elapsed=time.monotonic()-started)
    accepted_input = bool(not initial_description_error and pixel_quality(target, rendered)['passed'])
    final_svg = constrained
    best_mse = float(np.square(target.astype(np.float32)-rendered.astype(np.float32)).mean()/255**2)
    evaluations, accepted, alignment = (2 if constrained != prepared else 1), 0, None
    alignment_search = None
    print(f"Sample geladen: mittlerer Pixelfehler={initial_mse:.8f}", flush=True)
    if not accepted_input or not preferred_quality(pixel_quality(target, rendered)):
        from src.iCCModules.imageCompositeConverterSampleAlignment import align_sample
        # Description-only conversion has no second raster reconstruction.
        # Alignment uses the original image deadline, including initial work.
        fitted = align_sample(root, target, render_svg, deadline=hard_deadline, initial=rendered,
                              assertions=assertions,seed=effective_seed)
        final_svg, rendered, best_mse = fitted['svg'], fitted['rendered'], fitted['error']
        evaluations += fitted['evaluations']
        accepted = fitted['accepted']
        alignment = fitted['transform']
        alignment_search = fitted.get('search_control')
        print(f"Sample gemeinsam ausgerichtet: Prüfungen={evaluations}, "
              f"Pixelfehler={best_mse:.8f}", flush=True)
    contained = contain_svg(final_svg, width, height)
    if contained != final_svg:
        rendered = render_svg(contained, width, height)
        if rendered is None:
            return dict(passed=False, result=False, stop_reason=current_search().reason() or 'render_failure',
                        description_error='', search_seed=str(effective_seed), elapsed=time.monotonic()-started)
        best_mse = float(np.square(target.astype(np.float32)-rendered.astype(np.float32)).mean()/255**2)
    final_svg = contained
    quality = pixel_quality(target, rendered)
    description_error = ""
    try:
        validate_svg_assertions(final_svg, assertions)
    except ValueError as exc:
        description_error = str(exc)
    if description_error and initial_description_error:
        return refit_description(source, output, description, seed=effective_seed,
            hard_deadline=hard_deadline, initial_mse=initial_mse, initial_quality=initial_quality,
            template_error=description_error, started=started)
    active = current_search()
    active.measured(final_svg, float(quality['normalized_mse']), source='template_final',
                    scope='full_scene', valid=not description_error, passed=quality['passed'])
    if quality['passed'] and not description_error:
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import candidate_scope
        with candidate_scope('full_scene', 'template_final'):
            active.validate(dict(svg=final_svg), target)
    from src.imageConverterRecovery import atomic_svg
    from src.imageConverterCatalog import atomic_json
    output.parent.mkdir(parents=True, exist_ok=True)
    def ordering(candidate_svg, pixels, error):
        measured = vector_candidate_quality(target, pixels, candidate_svg)
        return (bool(error), not measured['passed'], vector_quality_score(measured)), measured
    initial_order, measured = ordering(final_svg, rendered, description_error)
    deliverable = dict(svg=final_svg, rendered=rendered, error=description_error, quality=measured, rank=initial_order)
    def save_checkpoint(candidate=None):
        nonlocal deliverable
        if candidate is not None:
            candidate_svg, pixels = candidate['svg'], candidate['rendered']
            error = ''
            try:
                validate_svg_assertions(candidate_svg, assertions)
            except ValueError as exc:
                error = str(exc)
            rank, measured = ordering(candidate_svg, pixels, error)
            if rank >= deliverable['rank']:
                return
            deliverable = dict(svg=candidate_svg, rendered=pixels, error=error, quality=measured, rank=rank)
        actual = float(np.square(target.astype(float)-deliverable['rendered'].astype(float)).mean()/255**2)
        progress = dict(search_seed=str(effective_seed), search_budget_seconds=seconds,
            initial_mse=initial_mse, initial_quality=initial_quality, final_mse=actual,
            final_quality=deliverable['quality'], improved=actual < initial_mse-1e-10,
            evaluations=evaluations, accepted=accepted, description_error=deliverable['error'],
            stop_reason='searching', alignment=alignment, continuation=None,
            passed=bool(deliverable['quality']['passed'] and not deliverable['error']))
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
        active = current_search()
        if active is not None:
            progress['continuation'] = active.report()
            progress['evaluations'] += active.evaluations
        atomic_svg(output, deliverable['svg'])
        atomic_json(output.with_suffix('.json'), progress)
    save_checkpoint()
    continuation = None
    if deliverable['rank'] < ordering(final_svg, rendered, description_error)[0]:
        final_svg, rendered, description_error = deliverable['svg'], deliverable['rendered'], deliverable['error']
        quality = deliverable['quality']
        best_mse = float(np.square(target.astype(float)-rendered.astype(float)).mean()/255**2)
    selection_improved = vector_quality_score(vector_candidate_quality(target, rendered, final_svg)) < vector_quality_score(
        vector_candidate_quality(target, initial_rendered, prepared))-1e-10
    report = dict(search_seed=str(effective_seed), search_budget_seconds=seconds,
                  initial_mse=initial_mse, final_mse=best_mse,
                  initial_quality=initial_quality, final_quality=quality,
                  improved=selection_improved, evaluations=evaluations,
                  accepted=accepted, description_error=description_error,
                  stop_reason=('description_conflict' if best_mse <= 1e-12 and description_error else
                               'native_search_accepted' if continuation and quality['passed'] and not description_error else
                               'quality_target_reached' if accepted_input and not description_error else
                               'sample_alignment_accepted' if quality and quality['passed'] else 'search_complete'),
                  continuation=continuation, alignment=alignment,
                  alignment_search=alignment_search,
                  search_goal_reached=bool(preferred_quality(quality) and not description_error),
                  passed=bool(quality and quality["passed"] and not description_error),
                  elapsed=round(time.monotonic() - started, 2))
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_svg(output, final_svg)
    atomic_json(output.with_suffix('.json'), report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


def main():
    from src.iCCModules.imageCompositeConverterDependencies import activate_vendored_site_packages
    activate_vendored_site_packages()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--description", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--deadline', type=float)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 240:
        parser.error("--seconds muss zwischen 0 und 240 liegen")
    if not 0 <= args.seed < 2**64:
        parser.error('--seed muss zwischen 0 und 2^64-1 liegen')
    if args.deadline is not None and not math.isfinite(args.deadline):
        parser.error('--deadline muss endlich sein')
    try:
        report = refine(args.source, args.sample, args.output, args.description.read_text(encoding="utf-8"), args.seconds,
                        seed=args.seed, deadline=args.deadline)
    except (ValueError, OSError) as exc:
        from src.imageConverterCatalog import atomic_json
        args.output.parent.mkdir(parents=True, exist_ok=True)
        message = 'Konvertierung konnte nicht ausgeführt werden: '+str(exc)
        atomic_json(args.output.with_suffix('.json'), dict(passed=False, result=False,
            stop_reason='invalid_input', description_error=str(exc), message=message))
        print(message, flush=True)
        return 1
    return 1 if report.get('result') is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
