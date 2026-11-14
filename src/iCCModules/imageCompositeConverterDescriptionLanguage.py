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
            # Bounded repeated-letter typos in head directions, never labels.
            (r'\b(spitze\s+nach\s+)u+n+t+e+n+\b', r'\1unten'),
            (r'\b(spitze\s+nach\s+)o+b+e+n+\b', r'\1oben'),
            (r'\bminnus\b', 'Minus'),
            (r'\bhorizonal(e|er|en|em|es)?\b', r'horizontal\1'),
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


def description_assertions(description: str) -> dict:
    normalized = normalize_description(description)
    labels = re.findall(r'["„]([^"“\n]+)["“]', normalized)
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', normalized).casefold()
    no_text = bool(re.search(r'\b(?:keine schriftzeichen|ohne text|ohne schriftzeichen)\b', words))
    label_claim = bool(labels and re.search(
        r'\b(?:beschriftung|aufschrift|text|buchstabe[n]?|label|ziffer[n]?)\b[^.?!]{0,100}["„]|'
        r'["“][^.?!]{0,100}\bals\b[^.?!]{0,40}\b(?:beschriftung|aufschrift|text|label)\b', normalized,
        flags=re.IGNORECASE))
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
    arrow_pair = looksLikeDualArrowDescriptionImpl(words)
    if arrow_pair:
        if any(c['kind'] == 'triangle' and c['count'] != 2 for c in counts):
            raise DescriptionRejected('conflicting_object_counts')
        if not any(c['kind'] == 'triangle' for c in counts):
            counts.append(dict(kind='triangle', count=2))
    assertions = dict(counts=counts, no_text=no_text)
    if arrow_pair:
        bar = re.search(r'\b(rot\w*|blau\w*)\s+(?:horizontal\w*|waagerecht\w*)\s+linie\b', words)
        if bar:
            assertions['horizontal_bar'] = 'red' if bar[1].startswith('rot') else 'blue'
    return assertions


def gradient_direction(text: str, direction: str) -> bool:
    """Bind orientation to the gradient, rather than an unrelated shaft/bar."""
    axes = set(re.findall(r'\b(waagerecht|senkrecht)\w*\s+(?:farb)?verlauf\b', text))
    axes.update(re.findall(r'\b(?:farb)?verlauf(?:\s+(?:der|des)\s+\w+)?\s+'
                          r'(?:(?:ist|verläuft)\s+)?(waagerecht|senkrecht)\w*\b', text))
    return axes == {direction}


def validate_svg_assertions(svg: str, assertions: dict | None) -> None:
    if not assertions or not (assertions.get('counts') or assertions.get('no_text') or assertions.get('horizontal_bar')):
        return
    root = ET.fromstring(svg)
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
    for assertion in assertions['counts']:
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
    if assertions.get('horizontal_bar'):
        from PIL import ImageColor
        from src.iCCModules.imageCompositeConverterRendering import _axis_svg_transform

        def horizontal_bar(node, sx=1., sy=1., fill='black', stroke='none'):
            kind = node.tag.rsplit('}', 1)[-1]
            if kind in excluded:
                return False
            # Translation and axis scaling preserve horizontality. Other
            # transforms cannot certify it from local coordinates alone.
            try:
                ax, ay, _, _ = _axis_svg_transform(node.get('transform', ''))
                sx, sy = sx*ax, sy*ay
            except ValueError:
                return False
            fill, stroke = node.get('fill', fill), node.get('stroke', stroke)
            try:
                if kind == 'line':
                    dx = abs(float(node.get('x2', '0'))-float(node.get('x1', '0')))*sx
                    dy = abs(float(node.get('y2', '0'))-float(node.get('y1', '0')))*sy
                    horizontal = math.isfinite(dx+dy) and dx > 0 and dy <= 1e-6
                    color = stroke
                elif kind == 'rect':
                    width = float(node.get('width', '0'))*sx
                    height = float(node.get('height', '0'))*sy
                    horizontal = math.isfinite(width+height) and width > 3*height > 0
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
            return any(horizontal_bar(child, sx, sy, fill, stroke) for child in node)

        if not horizontal_bar(root):
            raise DescriptionRejected('missing_described_horizontal_bar')
