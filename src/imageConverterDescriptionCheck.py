"""Bounded description checks against independent raster observations.

Catalog text and nearest neighbours are deliberately not evidence. Supported
German statements are checked individually; agreement never certifies free text.
"""
from __future__ import annotations

import re

import cv2
import numpy as np

from src.imageConverterRecognition import _COLORS, color_name, pixel_digest, plain_shape


VERSION = 'raster_description_check_v1'
COLOR = r'(?:(?:schwarz|dunkelgrau|hellgrau|grau|weiss|weiß|rot|grün|blau|gelb|violett|braun)(?:e[nrms]?)?|orange[nrms]?)'
SHAPE = r'(?:kreis(?:scheibe)?|scheibe|quadrat|rechteck|dreieck)'
ATTRIBUTES = r'(?:(?:einfarbig|gefüllt|rund|gerahmt|hochgestellt)(?:e[nrms]?)?\s+)*'


def _color(word):
    word = word.replace('weiß', 'weiss')
    if re.fullmatch(r'orange[nrms]?', word):
        return 'orange'
    return next((name for name in _COLORS if re.fullmatch(re.escape(name)+r'(?:e[nrms]?)?', word)), None)


def _shape(word):
    if word in {'kreis', 'kreisscheibe', 'scheibe'}:
        return 'Kreis'
    return word.capitalize()


def _primary_outline(image):
    """Observe a complete outer silhouette, allowing gradients and inner marks.

    This supplies no fill/rim/text evidence and is never an automatic caption.
    Padding permits tangent circles in tightly cropped icons, but the fitted
    ellipse must still be completely visible in the original canvas.
    """
    if min(image.size) < 18 or max(image.size) > 1024:
        return None
    pixels = np.asarray(image, dtype=np.float32)
    h, w = pixels.shape[:2]
    corners = np.array([pixels[0, 0], pixels[0, -1], pixels[-1, 0], pixels[-1, -1]])
    background = np.median(corners, axis=0)
    if np.max(abs(corners-background)) > 12:
        return None
    mask = (np.max(abs(pixels-background), axis=2) > 24).astype('uint8')
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if len(contours) != 1:
        return None
    contour = contours[0]
    x, y, bw, bh = cv2.boundingRect(contour)
    if min(bw, bh) < 12:
        return None
    silhouette = np.zeros_like(mask)
    cv2.drawContours(silhouette, [contour], -1, 1, -1)
    vertices = cv2.approxPolyDP(contour, cv2.arcLength(contour, True)*.012, True)
    expected = np.zeros_like(mask)
    shape = None
    if len(vertices) in (3, 4) and cv2.isContourConvex(vertices):
        if len(vertices) == 3 and x > 0 and y > 0 and x+bw < w and y+bh < h:
            shape = 'Dreieck'
            cv2.drawContours(expected, [vertices], -1, 1, -1)
        elif len(vertices) == 4 and x > 0 and y > 0 and x+bw < w and y+bh < h:
            if all(min(abs(px-x), abs(px-(x+bw-1))) <= 1 and
                   min(abs(py-y), abs(py-(y+bh-1))) <= 1 for px, py in vertices.reshape(-1, 2)):
                shape = 'Quadrat' if abs(bw-bh) <= 1 else 'Rechteck'
                cv2.rectangle(expected, (x, y), (x+bw-1, y+bh-1), 1, -1)
    elif len(contour) >= 8 and abs(bw-bh) <= max(1, .025*max(bw, bh)):
        (cx, cy), (ew, eh), angle = cv2.fitEllipse(contour)
        radius = max(ew, eh)/2
        if (abs(ew-eh) <= max(1, .025*max(ew, eh)) and
                cx-radius >= -.75 and cy-radius >= -.75 and
                cx+radius <= w-.25 and cy+radius <= h-.25):
            shape = 'Kreis'
            cv2.ellipse(expected, ((cx, cy), (ew, eh), angle), 1, -1)
    if shape is None:
        return None
    union = np.count_nonzero(silhouette | expected)
    if not union or np.count_nonzero(silhouette & expected)/union < .97:
        return None
    kernel = np.ones((3, 3), np.uint8)
    if np.any(silhouette > cv2.dilate(expected, kernel)) or np.any(expected > cv2.dilate(silhouette, kernel)):
        return None
    return dict(kind='primary_outline', shape=shape,
                description=f'Äussere Grundform: {shape}. Innere Details sind nicht geprüft.',
                fill_color=None, rim_color=None, background_color=color_name(background),
                background_rgb=background.tolist())


def check_description(image, description):
    result = dict(version=VERSION, description=description, image_sha256=pixel_digest(image),
                  status='unknown', checks=[], observations=None,
                  limitations='Geprüft werden einzelne deutsche Angaben zu einfachen Grundformen, '
                  'Flächenfarbe, Rand und Hintergrund. Freitext, Schriftinhalt, Anordnung und '
                  'komplexe Motive sind nicht vollständig prüfbar. Keine Konvertierungsfreigabe.')
    if not description.strip():
        return dict(result, status='missing', message='Keine Beschreibung zum Prüfen vorhanden.')
    observed = plain_shape(image) or _primary_outline(image)
    if observed is None:
        return dict(result, message='Nicht sicher prüfbar: Das Motiv liegt ausserhalb der lokalen Grundformerkennung.')
    result['observations'] = observed
    checks = result['checks']

    def check(field, claim, actual, agrees):
        checks.append(dict(field=field, claimed=claim, observed=actual,
                           status='agrees' if agrees else 'mismatch',
                           message=f'{field}: beschrieben „{claim}“, im Bild erkannt „{actual}“.'))

    def color_check(field, claim, actual, rgb):
        name = _color(claim)
        # Generic grey includes light/dark grey. Near colour boundaries we
        # abstain rather than manufacture a contradiction from a colour name.
        agrees = name == actual or (name == 'grau' and actual in {'hellgrau', 'dunkelgrau'})
        if agrees or np.linalg.norm(np.asarray(_COLORS[name])-rgb) > 125:
            check(field, name, actual, agrees)

    # Do not interpret quotations, comparisons, alternatives, conditions,
    # negated subjects or a noun belonging to a different object as assertions.
    words = re.sub(r'"[^"\n]*"|„[^“\n]*“|»[^«\n]*«', ' ', description.casefold())
    clauses = re.split(r'[.;!?\n]+', words)
    for clause in clauses:
        clause = clause.strip()
        if not clause or re.search(r'\b(?:nicht|kein\w*|oder|ähnlich|wie|falls|wenn|eventuell|vielleicht|statt|anstatt|beispiel|fehlt|fehlen|soll\w*|könnte\w*|wäre\w*)\b', clause):
            continue
        subject = re.match(r'(?P<outer>(?:die )?(?:äussere|äußere) grundform\s*(?::|ist)\s*)?'
                           r'(?:(?:das bild|das motiv) (?:zeigt|enthält) )?'
                           r'(?:ein(?:e[nrms]?)? |der |das |die )?'
                           +ATTRIBUTES+r'(?:(?P<color>'+COLOR+r') )?'+ATTRIBUTES+
                           r'(?P<shape>'+SHAPE+r')\b', clause)
        if subject and clause[subject.end():] and not re.match(
                r'\s+(?:mit|ohne|auf|vor)\b', clause[subject.end():]):
            subject = None
        if subject:
            shape = _shape(subject['shape'])
            # A square is also a rectangle, so that broader description is valid.
            agrees = shape == observed['shape'] or (shape == 'Rechteck' and observed['shape'] == 'Quadrat')
            # Inner marks may contain the named shape. An outer silhouette
            # alone cannot disprove an unspecified inner object in free text.
            if agrees or observed['kind'] == 'plain_shape' or subject['outer']:
                check('Grundform', shape, observed['shape'], agrees)
            if subject['color'] and observed['fill_color'] is not None:
                color_check('Flächenfarbe', subject['color'], observed['fill_color'], observed['fill_rgb'])
            tail = clause[subject.end():]
            rim = re.fullmatch(r'\s+mit (?:einem )?('+COLOR+r') (?:rand|kontur|umrandung)', tail)
            if rim and observed['kind'] == 'plain_shape':
                if observed['rim_color'] is None:
                    check('Rand', _color(rim[1]), 'kein sichtbarer Rand', False)
                else:
                    color_check('Randfarbe', rim[1], observed['rim_color'], observed['rim_rgb'])
            if observed['kind'] == 'plain_shape' and re.fullmatch(r'\s+ohne (?:rand|kontur|umrandung)', tail):
                check('Rand', 'ohne Rand', observed['rim_color'] or 'ohne Rand', observed['rim_color'] is None)
        background = re.fullmatch(r'(?:hintergrund\s*:\s*|(?:der )?hintergrund ist )('+COLOR+r')', clause)
        if background and observed['background_color'] is not None:
            color_check('Hintergrund', background[1], observed['background_color'], observed['background_rgb'])
        # Handle a background attached to the supported single-shape subject.
        background = re.fullmatch(r'\s+(?:auf|vor) (?:einem )?('+COLOR+r') hintergrund',
                                  clause[subject.end():]) if subject else None
        if background and observed['background_color'] is not None:
            color_check('Hintergrund', background[1], observed['background_color'], observed['background_rgb'])
    if any(check['status'] == 'mismatch' for check in checks):
        result.update(status='mismatch', message='Abweichung zwischen Bild und Beschreibung erkannt. Bitte die markierten Angaben prüfen.')
    elif checks:
        result.update(status='partial', message='Die prüfbaren Angaben stimmen mit der erkannten Grundform überein. Die gesamte Beschreibung ist damit nicht bestätigt.')
    else:
        result.update(message='Grundform erkannt, aber keine sicher auswertbare Aussage in der Beschreibung gefunden.')
    return result
