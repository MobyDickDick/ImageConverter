"""Resolve explicit, aspect-scoped references through description text only.

References suggest vocabulary, never stored geometry or reference SVGs. The
normal raster fit and quality gates still determine whether a candidate works.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Callable, Mapping
from pathlib import Path


class SimilarityReferenceError(ValueError):
    """A reference cannot be resolved unambiguously."""


_QUOTED = re.compile(r'"[^"\n]*"|„[^“\n]*“')
_NAME = r'[\w-]+(?:\.(?:svg|jpe?g|png|bmp|webp|tiff?))?'
_REFERENCE = re.compile(
    r'\b(?P<aspect>form(?:en)?\s+und\s+farbe[n]?|form(?:en)?|geometrie|'
    r'farbverlauf|farbgebung|farbe[n]?)\s*(?::\s*)?(?:(?:ist|sind)\s+)?'
    r'(?:(?:ähnlich|aehnlich|gleich)\s+)?wie\s+(?:(?:in|bei|bild)\s+)?'
    r'(?P<name>'+_NAME+r')(?![\w/\\-]|\.\w)', re.I)
_ALIAS = re.compile(r'^\s*wie\s+(?P<name>'+_NAME+r')\s*[,.:;]?\s*', re.I)
_COLOR = re.compile(
    r'(?<!\w)(?:#[0-9a-f]{6}\b|(?:hell|dunkel)?(?:grau|blau|grün|gruen|rot|gelb|'
    r'braun|violett|schwarz|weiß|weiss)(?:e[nrms]?)?\b|rosa\b|orange(?:n|s|r|m)?\b)', re.I)
_SHAPE = re.compile(r'\b(kreis(?:scheibe)?|rechteck|quadrat|dreieck|ellipse|polygon)\b', re.I)
_CONNECTOR = r'(?:griff\w*|anschluss\w*|anschlüsse|stiel\w*)'
_NO_CONNECTOR = re.compile(r'\b(?:ohne|kein\w*)\s+'+_CONNECTOR+r'\b', re.I)
_NO_TEXT = re.compile(r'\b(?:ohne|kein\w*)\s+(?:text|beschriftung|schriftzeichen)\b', re.I)


@dataclass(frozen=True)
class SimilarityDescription:
    text: str
    references: tuple[dict[str, str], ...] = ()


def _outside_quotes(text: str) -> str:
    return _QUOTED.sub(lambda m: ' '*len(m[0]), text)


def _unquoted_sub(pattern, replacement, text: str) -> str:
    parts = re.split(r'("[^"\n]*"|„[^“\n]*“)', text)
    return ''.join(part if i % 2 else re.sub(pattern, replacement, part, flags=re.I)
                   for i, part in enumerate(parts))


def _space(text: str) -> str:
    return _unquoted_sub(r'\s+', ' ', text).strip()


def _clauses(text: str, *, commas: bool = False) -> list[str]:
    pattern = r'(?<=[.;!?])\s+' + (r'|,\s*' if commas else '')
    result, start = [], 0
    for match in re.finditer(pattern, _outside_quotes(text)):
        result.append(text[start:match.start()])
        start = match.end()
    return [*result, text[start:]]


def _color_base(word: str) -> str:
    if word.startswith('#'):
        return word
    word = word.casefold()
    match = re.fullmatch(r'((?:hell|dunkel)?(?:grau|blau|grün|gruen|rot|gelb|braun|violett|schwarz|weiß|weiss))(?:e[nrms]?)?', word)
    return match[1] if match else 'orange' if word.startswith('orange') else word


def _adjective(color: str, ending: str) -> str:
    return color if color.startswith('#') or color in {'rosa', 'orange'} else color+ending


def _paint(text: str) -> dict[str, str]:
    """Project palette roles and gradient vocabulary without donor objects/text."""
    result = {}
    fill_colors = []
    gradient_colors = []
    for clause in re.split(r'[.;!?]', _outside_quotes(text)):
        clause = re.sub(r'\b(?:nicht|ohne|kein\w*)\b[^,;.!?]*', '', clause, flags=re.I)
        for match in _COLOR.finditer(clause):
            after = clause[match.end():].casefold()
            before = clause[:match.start()].casefold()
            noun = re.match(r'\s+(?:(?:dünn\w*|dick\w*|horizontal\w*|vertikal\w*)\s+)?(\w+)', after)
            role_word = noun[1] if noun else ''
            role = ('background' if role_word.startswith('hintergrund') else
                    'stroke' if role_word.startswith(('rand', 'kontur', 'umrand', 'umriss')) else
                    'text' if role_word.startswith(('text', 'beschrift', 'schrift')) else 'fill')
            if re.search(r'hintergrund\s*(?:ist|:)\s*$', before):
                role = 'background'
            elif re.search(r'(?:kontur|rand|umrandung)\s*(?:ist|:)\s*$', before):
                role = 'stroke'
            # An explicit fill/outline/background phrase is stronger than a
            # color decorating an unrelated donor object.
            if role_word.startswith(('füllung', 'fuellung')) or role != 'fill':
                result[role] = _color_base(match[0])
            else:
                result.setdefault(role, _color_base(match[0]))
            if role == 'fill':
                fill_colors.append(_color_base(match[0]))
        if re.search(r'farbverlauf|helligkeitsverlauf|graustufenverlauf|gradient', clause, re.I):
            gradient_colors.extend(_color_base(m[0]) for m in _COLOR.finditer(clause))
            axis = re.search(r'\b(horizontal|waagerecht|waagrecht|vertikal|senkrecht|radial)\w*', clause, re.I)
            result['gradient'] = ('horizontal' if axis and axis[1].casefold().startswith(('horizontal', 'waag')) else
                                  'vertikal' if axis and axis[1].casefold().startswith(('vertikal', 'senkrecht')) else
                                  'radial' if axis else '')
            if 'dunkel-hell-dunkel' in clause.casefold():
                result['zones'] = 'dunkel-hell-dunkel'
    colors = list(dict.fromkeys(gradient_colors or fill_colors))
    if gradient_colors:
        result['fill'] = gradient_colors[0]
    if len(colors) > 1:
        result['palette'] = ', '.join(colors)
    return result


def _shape_text(text: str) -> str:
    # Standalone paint sentences may contain arbitrary donor-only explanations.
    # Legacy handle prose has a paint-only parenthesis. Canonical geometry
    # vocabulary keeps the raster-backed handle fitter available without paint.
    text = _unquoted_sub(r'\bkelle,\s*ohne text kreis oben,\s*griff nach (links|rechts|oben|unten)(?:\s*\([^)]*\))?',
                         r'Ein unbeschrifteter Kreis mit einem geraden Griff nach \1', text)
    clauses = []
    for clause in _clauses(text):
        visible = _outside_quotes(clause)
        if re.search(r'füllung|hintergrund|farbverlauf|helligkeitsverlauf|gradient', visible, re.I) and not _SHAPE.search(visible):
            continue
        original_shapes = [m[0].casefold() for m in _SHAPE.finditer(visible)]
        clause = _unquoted_sub(r'\s+mit\s+(?:(?:einem|einer)\s+)?[^.;,]*?(?:farbverlauf|helligkeitsverlauf|gradient)[^.;]*', '', clause)
        if original_shapes != [m[0].casefold() for m in _SHAPE.finditer(_outside_quotes(clause))]:
            raise SimilarityReferenceError('Form und Farbverlauf der Referenz sind nicht eindeutig trennbar. Bitte den gewünschten Aufbau konkret beschreiben.')
        clause = _unquoted_sub(_COLOR.pattern, '', clause)
        clause = _unquoted_sub(r'\s+(?:und|auf|vor)\s+(?:(?:einem|einen)\s+)?\s*hintergrund\b', '', clause)
        clause = _unquoted_sub(r'\beinfarbig\w*\s*', '', clause)
        clauses.append(clause)
    return _space(' '.join(clauses))


def _exceptions(inherited: str, own: str) -> str:
    """Remove inherited claims contradicted by explicit absence/label edits."""
    no_text = bool(_NO_TEXT.search(_outside_quotes(own)))
    label = bool(re.search(r'\b(?:text|beschriftung|aufschrift)\b[^.;]*["„]', own, re.I))
    no_connector = bool(_NO_CONNECTOR.search(_outside_quotes(own)))
    if not (no_text or label or no_connector):
        return inherited
    clauses = []
    for clause in _clauses(inherited, commas=True):
        original_shapes = [m[0].casefold() for m in _SHAPE.finditer(_outside_quotes(clause))]
        if no_connector and re.search(_CONNECTOR, _outside_quotes(clause), re.I):
            # Inline attachments are removed from their introducer onward;
            # independent head geometry in the same clause is retained.
            clause = re.split(r'\s+(?:mit|und)\s+(?=[^.;]*'+_CONNECTOR+r')', clause, maxsplit=1, flags=re.I)[0] if _SHAPE.search(clause) else ''
        if no_text or label:
            if re.search(r'\b(?:text|beschriftung|aufschrift|buchstabe\w*)\b', clause, re.I) and not _NO_TEXT.search(clause):
                clause = re.split(r'\b(?:mit\s+)?(?:text|beschriftung|aufschrift|buchstabe\w*)\b', clause, maxsplit=1, flags=re.I)[0] if _SHAPE.search(clause) else ''
            if label:
                clause = _NO_TEXT.sub('', clause)
        remaining_shapes = [m[0].casefold() for m in _SHAPE.finditer(_outside_quotes(clause))]
        if original_shapes != remaining_shapes:
            raise SimilarityReferenceError('Die Ausnahme lässt sich nicht eindeutig von weiteren Formen trennen. Bitte den gewünschten Aufbau konkret beschreiben.')
        if clause.strip(' .;'):
            clauses.append(clause.strip(' .;'))
    result = '. '.join(clauses)
    # A head left over from a handle-shaped motif is an ordinary disk.
    if no_connector:
        result = _unquoted_sub(r'\bkelle\b[,.]?\s*', '', result)
        result = _unquoted_sub(r'\bkreis\s+oben\b', 'Kreis', result)
    return result


def _apply_paint(text: str, palette: dict[str, str], own_palette: dict[str, str]) -> str:
    for role, noun_pattern, ending in (
        ('fill', _SHAPE.pattern, 'er'),
        ('stroke', r'\b(rand|kontur|umrandung|umriss)\b', 'em'),
        ('background', r'\b(hintergrund)\b', 'em'),
    ):
        if role not in palette or role in own_palette:
            continue
        if role == 'fill' and ('gradient' in palette or 'palette' in palette):
            continue  # The gradient sentence carries the fill role itself.
        match = re.search(noun_pattern, _outside_quotes(text), re.I)
        if match:
            noun = match[0].casefold()
            suffix = ('er' if noun in {'kontur', 'umrandung'} else
                      'es' if noun in {'rechteck', 'quadrat', 'dreieck', 'polygon'} else
                      'e' if noun in {'ellipse', 'kreisscheibe'} else ending)
            text = text[:match.start()]+_adjective(palette[role], suffix)+' '+text[match.start():]
        elif role == 'background':
            if re.fullmatch(r'\s*(?:ein\s+)?(?:\w+\s+)?kreis mit (?:\w+\s+)?(?:rand|kontur)\.?\s*', text, re.I):
                text = text.rstrip(' .')+' und '+_adjective(palette[role], 'em')+' Hintergrund.'
            else:
                text = text.rstrip(' .')+'. Hintergrund: '+palette[role]+'.'
    if 'gradient' in palette and 'gradient' not in own_palette:
        axis = palette['gradient']
        fill = _adjective(palette.get('fill', ''), 'e') if palette.get('fill') else ''
        gradient = f'Die {fill} Füllung hat einen {axis+"en" if axis else ""} Farbverlauf'
        if palette.get('zones'):
            gradient += ': '+palette['zones']
        elif palette.get('palette'):
            gradient += ': '+palette['palette']
        text = text.rstrip(' .;')+'. '+' '.join(gradient.split())+'.'
    elif 'palette' in palette and 'fill' not in own_palette:
        text = text.rstrip(' .;')+'. Farbpalette: '+palette['palette']+'.'
    return text


def resolve_similarity_description(
    text: str, descriptions: Mapping[str, str], *,
    base_name: Callable[[str], str] | None = None,
    _visited: tuple[str, ...] = (), _legacy: bool = False,
) -> SimilarityDescription:
    """Expand scoped references; leave existing unscoped user aliases unchanged.

    Exact variant names win over a family fallback. Resolution has a hard depth
    and size bound, preserves quoted labels, and never accesses image files.
    """
    matches = list(_REFERENCE.finditer(_outside_quotes(text)))
    alias = _ALIAS.match(_outside_quotes(text)) if _legacy else None
    if not matches and not alias:
        return SimilarityDescription(text)
    if len(_visited) >= 16 or len(text) > 48000:
        raise SimilarityReferenceError('Die Bildreferenzen sind zu tief verschachtelt oder zu lang.')
    lookup = {key.casefold(): (key, value) for key, value in descriptions.items()}
    refs = []
    sources = {}
    own = text
    if alias and not matches:
        matches = [alias]
    for match in reversed(matches):
        prefix = _outside_quotes(text[:match.start()])
        if re.search(r'\b(?:nicht|keine?)\s*$', prefix, re.I):
            raise SimilarityReferenceError('Bitte eine positive Form- oder Farbreferenz angeben; Unterschiede danach beschreiben.')
        requested = match['name']
        stem = re.sub(r'\.(?:svg|jpe?g|png|bmp|webp|tiff?)$', '', requested, flags=re.I)
        found = lookup.get(requested.casefold()) or lookup.get(stem.casefold())
        if found is None and base_name:
            found = lookup.get(base_name(stem).casefold())
        if found is None or not found[1].strip():
            raise SimilarityReferenceError(f'Keine hinterlegte Bildbeschreibung für Referenz „{requested}“ gefunden.')
        key, donor = found
        if key.casefold() in _visited:
            raise SimilarityReferenceError(f'Zyklische Bildreferenz bei „{key}“.')
        resolved = resolve_similarity_description(donor, descriptions, base_name=base_name,
            _visited=(*_visited, key.casefold()), _legacy=True)
        aspect = match.groupdict().get('aspect', 'Form und Farben').casefold()
        aspects = ('shape', 'color') if ' und ' in aspect else ('shape',) if aspect.startswith(('form', 'geometrie')) else ('gradient',) if aspect == 'farbverlauf' else ('color',)
        for dimension in aspects:
            if dimension in sources and sources[dimension][0] != key:
                raise SimilarityReferenceError('Bitte pro Form bzw. Farbe nur eine Referenz angeben.')
            sources[dimension] = (key, resolved.text)
            refs.append(dict(aspect=dimension, requested=requested, key=key, description=resolved.text))
        refs.extend(resolved.references)
        if len(refs) > 64:
            raise SimilarityReferenceError('Die Beschreibung enthält zu viele verschachtelte Bildreferenzen (maximal 64).')
        own = own[:match.start()]+own[match.end():]
    own = re.sub(r'^[\s,.;:]*(?:(?:aber|jedoch)\s+)?', '', own, flags=re.I).strip(' ;,')
    own = re.sub(r'[.;,]\s*[.;,]+', '.', own).strip(' ;,.')
    shape = _exceptions(_shape_text(sources['shape'][1]), own) if 'shape' in sources else ''
    if 'shape' in sources and not shape.strip(' .;,'):
        raise SimilarityReferenceError('Die Formreferenz ergibt nach den Ausnahmen keine Formbeschreibung. Bitte die gewünschte Form konkret beschreiben.')
    # Caller paint always wins, including per-role overrides.
    own_palette = _paint(own)
    palette = _paint(sources['color'][1]) if 'color' in sources else {}
    if 'gradient' in sources:
        gradient = _paint(sources['gradient'][1])
        if 'gradient' not in gradient:
            raise SimilarityReferenceError(f'Die Referenz „{sources["gradient"][0]}“ beschreibt keinen Farbverlauf.')
        palette.update(gradient)
    if ('color' in sources or 'gradient' in sources) and not palette:
        raise SimilarityReferenceError('Die Farbreferenz enthält keine erkennbaren Farbangaben.')
    # Add caller paint to an inherited, color-free shape. Existing caller prose
    # is retained verbatim, so extra objects and negations cannot disappear.
    combined_palette = {**palette, **own_palette}
    if 'fill' in own_palette and 'palette' not in own_palette:
        combined_palette.pop('palette', None)
    shape = _apply_paint(shape, combined_palette, {}) if shape else ''
    if shape and _COLOR.fullmatch(own):
        own = ''  # A bare caller color has already replaced the inherited fill.
    if not shape:
        own = _apply_paint(own, combined_palette, own_palette)
    effective = '. '.join(part.strip(' .;,') for part in (shape, own) if part.strip(' .;,'))+'.'
    effective = _space(effective)
    if len(effective) > 48000:
        raise SimilarityReferenceError('Die aufgelöste Bildbeschreibung ist zu lang.')
    return SimilarityDescription(effective, tuple(reversed(refs)))


def resolve_catalog_similarity_description(text: str, root: Path) -> SimilarityDescription:
    """Resolve at standalone input boundaries; ordinary prose needs no catalog."""
    if not _REFERENCE.search(_outside_quotes(text)):
        return SimilarityDescription(text)
    from src.iCCModules.imageCompositeConverterDescriptions import loadCatalogDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    return resolve_similarity_description(text, loadCatalogDescriptionMappingImpl(root),
                                          base_name=getBaseNameFromFileImpl)
