"""Resolve simple embedded SVG style rules for the private MuPDF input.

MuPDF ignores stylesheet classes. Support the element/class/id compound
selectors used by exported drawings; leave unsupported stylesheets intact.
No source or saved conversion is rewritten.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET


def inline_simple_svg_styles(svg: str) -> str:
    if '<style' not in svg and ':style' not in svg and not re.search(r'\bstyle\s*=', svg):
        return svg
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg
    rules = []
    styles = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'style']
    selector_pattern = r'(?:[a-zA-Z_][\w-]*|\*)?(?:[.#][a-zA-Z_][\w-]*)*'

    def declarations(text):
        result = []
        for declaration in text.split(';'):
            if ':' not in declaration:
                continue
            key, value = declaration.split(':', 1)
            value = value.strip()
            important = bool(re.search(r'\s*!important\s*$', value, re.I))
            result.append((key.strip().lower(), re.sub(r'\s*!important\s*$', '', value, flags=re.I), important))
        return result

    for style in styles:
        css = re.sub(r'/\*.*?\*/', '', ''.join(style.itertext()), flags=re.S)
        cursor = 0
        for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            if css[cursor:match.start()].strip():
                return svg
            selectors = [s.strip() for s in match[1].split(',')]
            if any(not s or not re.fullmatch(selector_pattern, s) for s in selectors):
                return svg
            for selector in selectors:
                tokens = re.findall(r'[.#][\w-]+', selector)
                tag = re.split(r'[.#]', selector, maxsplit=1)[0]
                specificity = (sum(t.startswith('#') for t in tokens),
                               sum(t.startswith('.') for t in tokens), int(tag not in ('', '*')))
                rules.append((tag, tokens, specificity, declarations(match[2])))
            cursor = match.end()
        if css[cursor:].strip():
            return svg

    for element in root.iter():
        winners = {}
        classes = element.get('class', '').split()
        for order, (tag, tokens, specificity, values) in enumerate(rules):
            if tag not in ('', '*', element.tag.rsplit('}', 1)[-1]):
                continue
            if not all(t[1:] in classes if t[0] == '.' else element.get('id') == t[1:] for t in tokens):
                continue
            for key, value, important in values:
                rank = (important, 0, *specificity, order)
                if key not in winners or rank >= winners[key][0]:
                    winners[key] = (rank, value)
        for order, (key, value, important) in enumerate(declarations(element.get('style', ''))):
            rank = (important, 1, 0, 0, 0, order)
            if key not in winners or rank >= winners[key][0]:
                winners[key] = (rank, value)
        for key, (_, value) in winners.items():
            element.set(key, value)
        if winners:
            element.attrib.pop('style', None)
    parents = {child: parent for parent in root.iter() for child in parent}
    for style in styles:
        if style in parents:
            parents[style].remove(style)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ET.tostring(root, encoding='unicode')
