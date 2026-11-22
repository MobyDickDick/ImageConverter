"""Bounded German description normalization and explicit assertion validation.

This module has no catalog names, image geometry, templates or evaluation data.
Quoted labels retain their bytes. Assertions constrain every saved candidate,
including candidates offered to the deadline supervisor.
"""
from __future__ import annotations

import re
import math
from xml.etree import ElementTree as ET


class DescriptionRejected(ValueError):
    pass


def _validate_labels(root, expected):
    """Match native text runs by content and adjacent, transformed typography.

    Separate glyph positioning and a smaller raised/lowered index remain one
    logical label. Arbitrary distant text runs cannot satisfy that label.
    """
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    runs = []
    def visit(node, parent=(1., 0., 0., 1., 0., 0.), size=16.):
        kind = node.tag.rsplit('}', 1)[-1]
        if kind in {'defs', 'clipPath', 'mask', 'symbol', 'pattern', 'marker'}:
            return
        matrix = _compose(parent, _transform(node.get('transform', '')))
        size = float(node.get('font-size', str(size)).removesuffix('px'))
        if kind == 'text':
            text = ''.join(node.itertext()).strip()
            if text:
                a,b,c,d,tx,ty = matrix
                x, y = float(node.get('x', '0')), float(node.get('y', '0'))
                runs.append((text, a*x+c*y+tx, b*x+d*y+ty, size*math.hypot(c,d)))
            return
        for child in node:
            visit(child, matrix, size)
    try:
        visit(root)
    except (ValueError, TypeError):
        raise DescriptionRejected('unsupported_label_typography')

    def matches(group, label):
        script = re.fullmatch(r'(.+?)([\^_])([0-9]+)', label)
        content = script[1]+script[3] if script else label
        if ''.join(run[0] for run in group) != content:
            return False
        if len(group) == 1:
            return not script
        for previous, current in zip(group, group[1:]):
            _, px, py, ps = previous
            _, cx, cy, cs = current
            if not all(math.isfinite(v) for v in (px, py, ps, cx, cy, cs)) or min(ps,cs) <= 0:
                return False
            if not 0 < cx-px <= max(ps,cs)*(len(previous[0])+1):
                return False
            if not script and abs(cy-py) > max(ps,cs)*.35:
                return False
        if script:
            base, index = group[:-1], group[-1]
            if ''.join(run[0] for run in base) != script[1] or index[0] != script[3]:
                return False
            _, _, by, bs = base[-1]
            _, _, iy, ins = index
            return ins < bs*.9 and (iy < by if script[2] == '^' else iy > by)
        return True

    def consume(offset, remaining):
        if offset == len(runs):
            return not remaining
        for label in remaining:
            rest = list(remaining)
            rest.remove(label)
            for end in range(offset+1, len(runs)+1):
                if matches(runs[offset:end], label) and consume(end, rest):
                    return True
        return False
    if not consume(0, expected):
        raise DescriptionRejected('wrong_described_labels')
    return len(expected)


def normalize_description(description: str, *, orientations: bool = False) -> str:
    """Normalize equivalent vocabulary, keeping polarity and quoted text.

    Orientation normalization is local to fitters using the canonical vocabulary;
    older parsers continue receiving their established orientation spellings.
    """
    def normalize(part):
        # Attributive colors can sit between the shape adjective and its noun.
        # Retain those attributes rather than assuming a particular fill color.
        part = re.sub(r'\brunde[nrms]?\s+((?:(?:(?:hell|dunkel)?(?:grau|blau|rot|grün|gelb|weiß|weiss|orange|violett)|einfarbig|gefüllt)[enrms]?\s+)+)scheibe\b',
                      r'\1Kreisscheibe', part, flags=re.IGNORECASE)
        replacements = (
            # Common triangle spellings and a head-direction synonym. Keep
            # quoted labels untouched, just like the rest of this vocabulary.
            (r'\b(?:dreick|dreiek)(e)?\b', r'Dreieck\1'),
            (r'\b(dreieck|pfeil)\s+zeigt\s+nach\s+(oben|unten)\b', r'\1 mit Spitze nach \2'),
            (r'\b(pfeil|dreieck)\s+nach\s+(oben|unten)\b', r'\1 mit Spitze nach \2'),
            (r'\bspitze?\s+(?:gegen|nach)\s+(oben|unten)\b', r'Spitze nach \1'),
            # Bounded repeated-letter typos in head directions, never labels.
            (r'\b(spitze\s+nach\s+)u+n+t+e+n+\b', r'\1unten'),
            (r'\b(spitze\s+nach\s+)o+b+e+n+\b', r'\1oben'),
            (r'\bminnus\b', 'Minus'),
            (r'\b(?:linen|lininen)\b', 'Linien'),
            (r'\bdunelgrau([enrms]*)\b', r'dunkelgrau\1'),
            (r'\bminzuszeichen\b', 'Minuszeichen'),
            (r'\bhorizonal(e|er|en|em|es)?\b', r'horizontal\1'),
            (r'\bwaagrecht(e|er|en|em|es)?\b', r'waagerecht\1'),
            (r'\bvertial(e|er|en|em|es)?\b', r'vertikal\1'),
            (r'\brunde[nrms]?\s+scheibe\b', 'Kreisscheibe'),
            (r'\bumriss\b', 'Randkontur'),
            (r'\baufschrift\b', 'Beschriftung'),
            (r'\bhelligkeitsverlauf\b', 'Farbverlauf'),
            (r'\bfarb(?:en)?(?:übergang|uebergang)\b', 'Farbverlauf'),
            (r'\bgraustufen(?:übergang|uebergang)\b', 'Graustufenverlauf'),
            (r'\b(?:ohne anschlüsse|anschlussfrei|es sind keine anschlüsse vorhanden)\b', 'keine Anschlüsse'),
            (r'\bweder text noch weitere objekte sind vorhanden\b', 'keine Schriftzeichen und keine weiteren Objekte'),
            (r'\b(?:ohne beschriftung|ohne schriftzeichen|schriftzeichen fehlen|kein text)\b', 'keine Schriftzeichen'),
            (r'\b(?:ohne weitere objekte|weitere objekte fehlen|sonst keine objekte)\b', 'keine weiteren Objekte'),
            (r'\brunde[nrms]? ecken\b', 'abgerundete Ecken'),
            (r'\brunde[nrms]? enden\b', 'abgerundete Enden'),
            (r'\bwarnzeichen in dreiecksform\b', 'Warndreieck'),
            (r'\brechts?pfeil\b', 'Pfeil nach rechts'),
            (r'\blückenlos\b', 'ohne Lücke'),
            (r'\bpunkt ist darunter abgesetzt\b', 'Punkt liegt getrennt darunter'),
            (r'\bdiagramm\b', 'Achsendiagramm'),
            (r'\bnach unten offen', 'unten offen'),
        )
        for pattern, replacement in replacements:
            part = re.sub(pattern, replacement, part, flags=re.IGNORECASE)
        if orientations:
            part = re.sub(r'\bhorizontal', 'waagerecht', part, flags=re.IGNORECASE)
            part = re.sub(r'\bvertikal', 'senkrecht', part, flags=re.IGNORECASE)
        return part
    # Labels can contain words from the dictionary, punctuation and mixed case.
    parts = re.split(r'("[^"\n]*"|„[^“\n]*“)', str(description or ''))
    return ''.join(part if i % 2 else normalize(part) for i, part in enumerate(parts))


def arrow_head_directions(description: str) -> list[tuple[str, str]]:
    """Bind each direction to its nearest preceding side, outside quoted labels."""
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', normalize_description(description)).casefold()
    side = r'(?:links|rechts|linke[nrsm]?|rechte[nrsm]?)'
    return [('links' if s.startswith('link') else 'rechts', d) for s, d in re.findall(
        r'\b('+side+r')\b(?:(?!\b'+side+r'\b)[^.;!?])*?\bspitze nach (oben|unten)\b', words)]


def horizontal_bar_colors(description: str) -> set[str]:
    """Read both adjective orders without interpreting quoted labels."""
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', normalize_description(description)).casefold()
    color = r'(rot|blau)(?:e[nrms]?)?'
    axis = r'(?:horizontal|waagerecht)(?:e[nrms]?)?'
    matches = re.findall(r'\b'+color+r'\s+'+axis+r'\s+linie\b', words)
    matches += re.findall(r'\b'+axis+r'\s+'+color+r'\s+linie\b', words)
    return {'red' if value.startswith('rot') else 'blue' for value in matches}


def arrow_side_colors(description: str, side: str) -> set[str]:
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', normalize_description(description)).casefold()
    adjective = 'linke' if side == 'links' else 'rechte'
    colors = re.findall(r'\b'+side+r'\s*[:,]?\s*(?:ist\s+)?(rot|blau)(?:e[nrsm]?)?\b', words)
    colors += re.findall(r'\b'+adjective+r'[nrsm]?\s+(?:linie|dreieck|pfeil|seite)\b'
                         r'[^.;!?]*?\b(?:ist|sind)\s+(rot|blau)\b', words)
    return {'red' if color == 'rot' else 'blue' for color in colors}


def description_assertions(description: str) -> dict:
    from src.iCCModules.imageCompositeConverterSvgComponents import parse_components
    if parse_components(description):
        # An explicit SVG list names the complete inventory directly. Geometry
        # is checked against every donor, including its paint and internal IDs.
        return dict(svg_component_description=description)
    normalized = normalize_description(description)
    labels = re.findall(r'["„]([^"“\n]+)["“]', normalized)
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', normalized).casefold()
    no_text = bool(re.search(r'\b(?:keine schriftzeichen|ohne text|ohne schriftzeichen)\b', words))
    label_claim = bool(labels and re.search(
        r'\b(?:beschriftung|aufschrift|text|(?:groß|gross|klein)?buchstabe[n]?|label|ziffer[n]?)\b[^.?!]{0,100}["„]|'
        r'["“][^.?!]{0,100}\bals\b[^.?!]{0,40}\b(?:beschriftung|aufschrift|text|label)\b', normalized,
        flags=re.IGNORECASE) or re.search(
            r'\bin der (?:kelle|kreisscheibe) ist ein ["„][^"“\n]+["“] geschrieben',
            normalized, re.IGNORECASE))
    unnamed_text = bool(not label_claim and re.search(
        r'\b(?:mit\s+(?:einer?\s+)?|eine?\s+)(?:beschriftung|aufschrift|buchstabe|text|ziffer)\b', words))
    if no_text and (label_claim or re.search(r'\b(?:ausrufezeichen|fragezeichen)\b', words)):
        raise DescriptionRejected('text_present_and_absent')
    # Front/back selectors need a declared instance identity. They are not
    # aliases for whichever object happens to make a candidate fit the raster.
    if re.search(r'\b(?:vordere[nr]?|hintere[nr]?) form\b', words):
        raise DescriptionRejected('unresolved_depth_selector')
    number = r'(null|keine|einen|ein|eine|eins|zwei|drei|vier|fünf|[0-9]+)'
    counts = []
    numbers = dict(null=0, keine=0, einen=1, ein=1, eine=1, eins=1, zwei=2, drei=3, vier=4, fünf=5)
    for match in re.finditer(r'\b(?:das motiv enthält|es gibt) genau '+number+r' (kreise?|rechtecke?|linien|dreiecke?)\b', words):
        value, noun = match.groups()
        kind = ('circle' if noun.startswith('kreis') else 'rect' if noun.startswith('rechteck')
                else 'triangle' if noun.startswith('dreieck') else 'line')
        count = int(value) if value.isdigit() else numbers[value]
        if any(c['kind']==kind and c['count']!=count for c in counts):
            raise DescriptionRejected('conflicting_object_counts')
        counts.append(dict(kind=kind, count=count))
    from src.iCCModules.imageCompositeConverterDualArrowBadge import looksLikeDualArrowDescriptionImpl
    heads = arrow_head_directions(normalized)
    # Assertions must survive contradictory directions too. Dispatch only
    # recognizes opposite heads; using dispatch here would silently drop claims.
    arrow_pair = (looksLikeDualArrowDescriptionImpl(words) or
                  ({side for side, _ in heads} == {'links', 'rechts'}
                   and bool(re.search(r'\b(?:pfeil|dreieck)', words))))
    if arrow_pair:
        if any(c['kind'] == 'triangle' and c['count'] != 2 for c in counts):
            raise DescriptionRejected('conflicting_object_counts')
        if not any(c['kind'] == 'triangle' for c in counts):
            counts.append(dict(kind='triangle', count=2))
    assertions = dict(counts=counts, no_text=no_text)
    from src.iCCModules.imageCompositeConverterPartitionedRhombus import partitioned_rhombus_spec
    partition = partitioned_rhombus_spec(normalized)
    if partition:
        assertions['partitioned_rhombus'] = partition
    from src.iCCModules.imageCompositeConverterThreeWingValve import three_wing_valve_spec
    if three_wing_valve_spec(normalized):
        assertions['three_wing_valve'] = True
    from src.iCCModules.imageCompositeConverterScopedPaint import scoped_paint_claims
    paint_claims, _ = scoped_paint_claims(words)
    if paint_claims:
        assertions['scoped_paint'] = paint_claims
    from src.iCCModules.imageCompositeConverterTwoWayValve import two_way_valve_spec
    valve = two_way_valve_spec(normalized)
    if valve:
        assertions['two_way_valve'] = valve
    from src.iCCModules.imageCompositeConverterSymmetricCircleLines import symmetric_circle_lines_spec
    symmetric_lines = symmetric_circle_lines_spec(normalized)
    if symmetric_lines:
        assertions['symmetric_circle_lines'] = symmetric_lines
    from src.iCCModules.imageCompositeConverterRelations import anchor_relations
    try:
        relations = anchor_relations(normalized)
    except ValueError as exc:
        raise DescriptionRejected(str(exc)) from exc
    if relations:
        assertions['anchor_relations'] = relations
    from src.iCCModules.imageCompositeConverterRepresentation import description_object_limits
    objects = description_object_limits(normalized)
    from src.iCCModules.imageCompositeConverterDiskArrow import disk_arrow_direction
    direction = disk_arrow_direction(normalized)
    if direction:
        assertions['disk_arrow_direction'] = direction
        # The shaft and head share one painted outline.
        objects.setdefault('circle', 1)
        objects.setdefault('polygon', 1)
    if label_claim:
        objects['text'] = len(set(labels))
        assertions['labels'] = sorted(set(labels))
    if arrow_pair:
        objects['triangle'] = 2
    if objects:
        assertions['objects'] = objects
        # The description is always the complete inventory. Pixel evidence
        # cannot authorize another object, even in a failed draft.
        assertions['objects_complete'] = True
        # Plus/minus are composite symbols, not additional full scene lines.
        # Their short native bars need not be encoded as opaque generic paths.
        symbol_strokes = 0
        for symbol, bars in (('plus', 2), ('minus', 1)):
            mentions = list(re.finditer(r'\b'+symbol+r'(?:zeichen)?\b', words))
            if any(not re.search(r'\b(?:kein[enrms]?|ohne)\s*$', words[:m.start()]) for m in mentions):
                symbol_strokes += bars
        if symbol_strokes:
            assertions['symbol_strokes'] = symbol_strokes
    from src.iCCModules.imageCompositeConverterHollowCrossPanel import hollow_cross_contract, central_outline
    if hollow_cross_contract(normalized):
        assertions['hollow_cross_panel'] = True
        assertions['hollow_cross_outline'] = central_outline(normalized)
        # These are owned parts of the two logical diagonals: one diagonal
        # consists of two rails. Its visible-structure validator checks both
        # rails and the other axis; a flat SVG-wide count would count three
        # strokes as three diagonals or confuse the rails with all scene lines.
        for kind in ('line',):
            assertions.get('objects', {}).pop(kind, None)
        assertions.setdefault('objects', {})['diagonal'] = 2
    # Global, positive claims only. Quoted labels and negative clauses must
    # never turn into an instruction to regularize the drawing.
    uniform = (r'\b(?:alle|sämtliche)\s+(?:linien|striche|konturen)\s+'
               r'(?:(?:sind|sollen|müssen)\s+(?:alle\s+)?(?:gleich\s+(?:breit|dick|stark)|gleichmässig\s+breit|gleichmäßig\s+breit)'
               r'|haben\s+(?:(?:die|eine)\s+)?(?:gleiche|einheitliche|identische)\s+(?:breite|dicke|strichstärke|linienstärke))\b'
               r'|\b(?:einheitliche|identische)\s+(?:strichstärke|linienstärke|linienbreite)\b')
    for clause in re.split(r'[.;!?\n]', words):
        for match in re.finditer(uniform, clause):
            if not re.search(r'\b(?:nicht|keine?|ohne)(?:\s+(?:eine?|unbedingt|zwingend))?\s*$',
                             clause[:match.start()]):
                if re.search(r'\b(?:außer|ausser|ausgenommen|bis auf|mit ausnahme)\b', clause[match.end():]):
                    raise DescriptionRejected('unsupported_line_width_exception')
                assertions['equal_stroke_width'] = True
    if arrow_pair:
        assertions['arrow_heads'] = []
        for side, direction in heads:
            colors = arrow_side_colors(normalized, side)
            if len(colors) > 1:
                raise DescriptionRejected('conflicting_arrow_colors:'+side)
            claim = dict(side='left' if side == 'links' else 'right',
                         direction='up' if direction == 'oben' else 'down')
            if colors:
                claim['color'] = colors.pop()
            assertions['arrow_heads'].append(claim)
        colors = horizontal_bar_colors(normalized)
        if len(colors) > 1:
            raise DescriptionRejected('conflicting_horizontal_bar_colors')
        if colors:
            assertions['horizontal_bar'] = colors.pop()
    if 'balken' in words and 'rechteck' in words:
        from src.iCCModules.imageCompositeConverterSprayPanel import spray_contract, _dashed_spray_rays
        ray_count = re.search(r'\b(\d+)\s+(?:sprüh)?strahlen\b', words)
        if ray_count and spray_contract(description) and _dashed_spray_rays(description):
            assertions['dashed_spray_rays'] = int(ray_count.group(1))
    if not objects:
        assertions['inventory_error'] = 'missing_described_object_inventory'
    elif unnamed_text:
        assertions['inventory_error'] = 'unresolved_described_label'
    # Unbounded additions must never be silently treated as an optional detail.
    if re.search(r'\b(?:weitere|zusätzliche|zusatzliche)\s+(?:objekte|elemente|formen)\b', words):
        if not re.search(r'\b(?:keine|ohne)\s+(?:weiteren?|zusätzlichen?)\s+(?:objekte|elemente|formen)\b', words):
            assertions['inventory_error'] = 'unresolved_described_object_inventory'
    from src.iCCModules.imageCompositeConverterSceneProgram import scene_program
    program = scene_program(normalized)
    if program is not None and program['relations']:
        assertions['primitive_program'] = program
    return assertions


def gradient_direction(text: str, direction: str) -> bool:
    """Bind orientation to the gradient, rather than an unrelated shaft/bar."""
    axes = set(re.findall(r'\b(waagerecht|senkrecht)\w*\s+(?:farb)?verlauf\b', text))
    axes.update(re.findall(r'\b(?:farb)?verlauf(?:\s+(?:der|des)\s+\w+)?\s+'
                          r'(?:(?:ist|verläuft)\s+)?(waagerecht|senkrecht)\w*\b', text))
    return axes == {direction}


def draft_assertions(assertions):
    result = dict(counts=[], no_text=assertions.get('no_text', False))
    for key in ('equal_stroke_width', 'objects', 'objects_complete', 'symbol_strokes', 'inventory_error',
                'svg_component_description', 'two_way_valve', 'three_wing_valve', 'primitive_program', 'scoped_paint',
                'partitioned_rhombus'):
        if assertions.get(key):
            result[key] = assertions[key]
    if result.get('objects'):
        result['objects_partial'] = True
    return result


def validate_svg_assertions(svg: str, assertions: dict | None) -> None:
    if assertions and assertions.get('partitioned_rhombus'):
        from src.iCCModules.imageCompositeConverterPartitionedRhombus import validate_partitioned_rhombus
        try:
            validate_partitioned_rhombus(svg, assertions['partitioned_rhombus'])
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions and assertions.get('three_wing_valve'):
        from src.iCCModules.imageCompositeConverterThreeWingValve import validate_three_wing_valve
        try:
            validate_three_wing_valve(svg)
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions and assertions.get('svg_component_description'):
        from src.iCCModules.imageCompositeConverterSvgComponents import validate_components
        validate_components(svg, assertions['svg_component_description'])
        return
    if assertions and assertions.get('inventory_error'):
        raise DescriptionRejected(assertions['inventory_error'])
    if assertions and assertions.get('scoped_paint'):
        from src.iCCModules.imageCompositeConverterScopedPaint import validate_scoped_paint
        try:
            validate_scoped_paint(svg, assertions['scoped_paint'])
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions and assertions.get('two_way_valve'):
        from src.iCCModules.imageCompositeConverterTwoWayValve import validate_two_way_valve
        try:
            validate_two_way_valve(svg, assertions['two_way_valve'])
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions and assertions.get('symmetric_circle_lines'):
        from src.iCCModules.imageCompositeConverterSymmetricCircleLines import validate_symmetric_circle_lines
        try:
            validate_symmetric_circle_lines(svg, assertions['symmetric_circle_lines'])
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if not assertions or not (assertions.get('counts') or assertions.get('no_text') or assertions.get('horizontal_bar')
                              or assertions.get('arrow_heads') or assertions.get('equal_stroke_width')
                              or assertions.get('dashed_spray_rays') or assertions.get('hollow_cross_panel')
                              or assertions.get('anchor_relations') or assertions.get('objects')):
        return
    if assertions.get('anchor_relations'):
        from src.iCCModules.imageCompositeConverterRelations import validate_anchor_relations
        try:
            validate_anchor_relations(svg, assertions['anchor_relations'])
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions.get('hollow_cross_panel'):
        from src.iCCModules.imageCompositeConverterHollowCrossPanel import validate_hollow_cross_panel
        try:
            validate_hollow_cross_panel(svg,assertions.get('hollow_cross_outline','diamond'))
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions.get('dashed_spray_rays'):
        from src.iCCModules.imageCompositeConverterSprayPanel import validate_dashed_spray_rays
        try:
            validate_dashed_spray_rays(svg, assertions['dashed_spray_rays'])
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions.get('equal_stroke_width'):
        from src.iCCModules.imageCompositeConverterStrokeConstraints import validate_equal_stroke_width
        try:
            validate_equal_stroke_width(svg)
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    root = ET.fromstring(svg)
    if root.get('data-primitive-scene') == '1' and assertions.get('primitive_program'):
        from src.iCCModules.imageCompositeConverterSceneProgram import validate_program_svg
        try:
            validate_program_svg(svg, assertions['primitive_program'])
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
    if assertions.get('objects_complete'):
        if any(node.tag.rsplit('}', 1)[-1] in {'image', 'use', 'foreignObject', 'script'} for node in root.iter()):
            raise DescriptionRejected('unsupported_inventory_element')
    if assertions.get('labels'):
        _validate_labels(root, assertions['labels'])
    excluded = {'defs', 'clipPath', 'mask', 'symbol', 'pattern', 'marker'}
    def visible_nodes(element):
        kind = element.tag.rsplit('}',1)[-1]
        if kind in excluded:
            return
        yield element
        for child in element:
            yield from visible_nodes(child)
    nodes = list(visible_nodes(root))
    if assertions.get('no_text') and any(e.tag.rsplit('}',1)[-1]=='text' and ''.join(e.itertext()).strip() for e in nodes):
        raise DescriptionRejected('unexpected_text_in_svg')
    # Only the native contract can prove an explicit count. Do not claim a
    # count of semantic circles from arbitrary paths, use instances or clipping.
    for assertion in assertions.get('counts', []):
        if assertion['kind'] == 'triangle':
            # Native, nondegenerate triangles prove the requested heads. A
            # circle, arbitrary path or four-sided polygon cannot stand in.
            def is_triangle(element):
                if element.tag.rsplit('}', 1)[-1] != 'polygon':
                    return False
                try:
                    values = [float(v) for v in re.split(r'[\s,]+', element.get('points', '').strip())]
                except ValueError:
                    return False
                if len(values) != 6 or not all(math.isfinite(v) for v in values):
                    return False
                ax, ay, bx, by, cx, cy = values
                return abs((bx-ax)*(cy-ay)-(by-ay)*(cx-ax)) > 1e-9
            actual = sum(is_triangle(e) for e in nodes)
        else:
            actual = sum(e.tag.rsplit('}',1)[-1] == assertion['kind'] for e in nodes)
        if actual != assertion['count']:
            raise DescriptionRejected(f"object_count:{assertion['kind']}:{assertion['count']}:{actual}")
    if assertions.get('arrow_heads'):
        from src.iCCModules.imageCompositeConverterArrowAssertions import validate_arrow_heads
        validate_arrow_heads(root, assertions['arrow_heads'])
    if assertions.get('horizontal_bar'):
        from PIL import ImageColor
        from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform

        def horizontal_bar(node, parent=(1., 0., 0., 1., 0., 0.), fill='black', stroke='none'):
            kind = node.tag.rsplit('}', 1)[-1]
            if kind in excluded:
                return False
            try:
                matrix = _compose(parent, _transform(node.get('transform', '')))
            except ValueError:
                return False
            a, b, c, d, _, _ = matrix
            fill, stroke = node.get('fill', fill), node.get('stroke', stroke)
            try:
                if kind == 'line':
                    x = float(node.get('x2', '0'))-float(node.get('x1', '0'))
                    y = float(node.get('y2', '0'))-float(node.get('y1', '0'))
                    dx, dy = abs(a*x+c*y), abs(b*x+d*y)
                    horizontal = math.isfinite(dx+dy) and dx > 0 and dy <= 1e-6
                    color = stroke
                elif kind == 'rect':
                    width = float(node.get('width', '0'))
                    height = float(node.get('height', '0'))
                    edges = [(a*width, b*width), (c*height, d*height)]
                    lengths = [math.hypot(x, y) for x, y in edges]
                    longest = 0 if lengths[0] >= lengths[1] else 1
                    dx, dy = map(abs, edges[longest])
                    horizontal = (math.isfinite(sum(lengths)) and min(width, height) > 0
                                  and dx > 3*lengths[1-longest] > 0 and dy <= 1e-6)
                    color = fill
                else:
                    horizontal, color = False, 'none'
                r, g, b = ImageColor.getrgb(color)
                color_matches = (r > g+30 and r > b+30 if assertions['horizontal_bar'] == 'red'
                                 else b > r+30 and b > g+15)
                if horizontal and color_matches:
                    return True
            except (ValueError, TypeError):
                pass
            return any(horizontal_bar(child, matrix, fill, stroke) for child in node)

        if not horizontal_bar(root):
            raise DescriptionRejected('missing_described_horizontal_bar')
    if assertions.get('disk_arrow_direction'):
        from src.iCCModules.imageCompositeConverterDiskArrow import validate_disk_arrow
        if not validate_disk_arrow(root, assertions['disk_arrow_direction']):
            raise DescriptionRejected('missing_described_disk_arrow')
    if assertions.get('objects'):
        from src.iCCModules.imageCompositeConverterRepresentation import validate_object_limits
        try:
            validate_object_limits(svg, assertions['objects'], partial=assertions.get('objects_partial', False),
                                   complete=assertions.get('objects_complete', False), symbol_strokes=assertions.get('symbol_strokes', 0),
                                   text_count=len(assertions['labels']) if assertions.get('labels') else None,
                                   diagonal_rails=bool(assertions.get('hollow_cross_panel')))
        except ValueError as exc:
            raise DescriptionRejected(str(exc)) from exc
