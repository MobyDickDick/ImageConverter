"""Local, conservative image recognition using pixels and measured reference pairs.

Similarity is a retrieval distance, never a probability or a quality verdict.
Only identical decoded pixels or a bounded plain-shape detector supply an
automatic description. Other neighbours require an explicit user selection.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import threading
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image, ImageOps


VERSION = 'local_image_recognition_v1'


def rgb_image(source):
    with Image.open(io.BytesIO(source) if isinstance(source, bytes) else source) as image:
        image = ImageOps.exif_transpose(image).convert('RGBA')
        background = Image.new('RGB', image.size, 'white')
        background.paste(image, mask=image.getchannel('A'))
        return background


def pixel_digest(image):
    return hashlib.sha256(f'{image.width}x{image.height}:'.encode()+image.tobytes()).hexdigest()


def descriptor(image):
    """Keep colour, inner marks and aspect; normalize only canvas resolution."""
    pixels = np.asarray(image.resize((40, 40), Image.Resampling.LANCZOS), dtype=np.float32)/255
    gray = cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY)
    edges = cv2.Sobel(gray, cv2.CV_32F, 1, 0)**2 + cv2.Sobel(gray, cv2.CV_32F, 0, 1)**2
    return pixels, np.minimum(np.sqrt(edges), 1), float(np.log(image.width/image.height))


def distance(left, right):
    rgb, edge, aspect = left
    other, other_edge, other_aspect = right
    # White margins must not swamp a small symbol or its internal marks.
    foreground = (np.min(rgb, axis=2) < .94) | (np.min(other, axis=2) < .94)
    color = float(np.mean(abs(rgb[foreground]-other[foreground]))) if foreground.any() else 1.
    return color*.65 + float(np.mean(abs(edge-other_edge)))*.25 + min(1., abs(aspect-other_aspect))*.1


_COLORS = {
    'schwarz': (0, 0, 0), 'dunkelgrau': (70, 70, 70), 'grau': (135, 135, 135),
    'hellgrau': (205, 205, 205), 'weiss': (255, 255, 255), 'rot': (230, 30, 30),
    'grün': (30, 160, 30), 'blau': (30, 60, 225), 'gelb': (245, 225, 25),
    'orange': (245, 145, 25), 'violett': (150, 45, 180), 'braun': (135, 80, 40),
}


def color_name(rgb):
    name = min(_COLORS, key=lambda key: np.linalg.norm(np.asarray(_COLORS[key])-rgb))
    return name if np.linalg.norm(np.asarray(_COLORS[name])-rgb) <= 90 else None


def adjective(color, ending):
    return color+ending[1:] if color == 'orange' else color+ending


def plain_shape(image):
    """Recognize one unclipped, flat circle/rectangle/triangle on a flat canvas.

    Reject gradients, text, attachments, extra components and irregular contours.
    The output is a description proposal, not a reconstructed or accepted SVG.
    """
    # Large downsampling could erase tiny text and turn a scene into a plain disk.
    if min(image.size) < 18 or max(image.size) > 1024:
        return None
    pixels = np.asarray(image, dtype=np.float32)
    height, width = pixels.shape[:2]
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    background = np.median(border, axis=0)
    if np.max(abs(border-background)) > 12:
        return None
    mask = (np.max(abs(pixels-background), axis=2) > 24).astype('uint8')
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if len(contours) != 1:
        return None
    contour = contours[0]
    x, y, w, h = cv2.boundingRect(contour)
    if min(w, h) < 12 or x < 2 or y < 2 or x+w > width-2 or y+h > height-2:
        return None
    silhouette = np.zeros_like(mask)
    cv2.drawContours(silhouette, [contour], -1, 1, -1)
    depth = cv2.distanceTransform(silhouette, cv2.DIST_L2, 5)
    core = depth > min(w, h)*.22
    if core.sum() < 12:
        return None
    fill = np.median(pixels[core], axis=0)
    if np.max(abs(pixels[core]-fill)) > 18:
        return None
    # Every interior pixel must belong to flat fill or a uniform thin rim.
    interior = depth > 1.5
    different = interior & (np.max(abs(pixels-fill), axis=2) > 24)
    rim = None
    if different.any():
        rim = np.median(pixels[different], axis=0)
        if (np.max(depth[different]) > max(3, min(w, h)*.16)
                or np.max(abs(pixels[different]-rim)) > 24):
            return None
        # A short extra stroke near the rim must not be swallowed by its colour.
        rim_depth = float(np.median(depth[different]))
        if np.max(depth[different]) > 2*rim_depth-.5+1.25:
            return None
        # A rim must surround the shape, not describe a small internal mark.
        band = interior & (depth < max(2.5, rim_depth))
        if band.sum() < 8 or np.mean(np.max(abs(pixels[band]-rim), axis=1) < 30) < .90:
            return None
    perimeter = cv2.arcLength(contour, True)
    vertices = cv2.approxPolyDP(contour, perimeter*.012, True)
    expected = np.zeros_like(mask)
    shape = None
    if len(vertices) == 4 and cv2.isContourConvex(vertices):
        corners = vertices.reshape(-1, 2)
        if all(min(abs(px-x), abs(px-(x+w-1))) <= 1 and
               min(abs(py-y), abs(py-(y+h-1))) <= 1 for px, py in corners):
            shape = 'Quadrat' if abs(w-h) <= 1 else 'Rechteck'
            cv2.rectangle(expected, (x, y), (x+w-1, y+h-1), 1, -1)
    elif len(vertices) == 3 and cv2.isContourConvex(vertices):
        shape = 'Dreieck'
        cv2.drawContours(expected, [vertices], -1, 1, -1)
    elif len(contour) >= 8 and abs(w-h) <= max(1, .025*max(w, h)):
        (cx, cy), (ew, eh), angle = cv2.fitEllipse(contour)
        if abs(ew-eh) <= max(1, .025*max(ew, eh)):
            shape = 'Kreis'
            cv2.ellipse(expected, ((cx, cy), (ew, eh), angle), 1, -1)
    if shape is None:
        return None
    # Boundary rasterization may differ by one pixel; structural protrusions may not.
    kernel = np.ones((3, 3), np.uint8)
    if (np.any(silhouette > cv2.dilate(expected, kernel)) or
            np.any(expected > cv2.dilate(silhouette, kernel))):
        return None
    # Background and interior checks run at the original resolution.
    exterior = cv2.dilate(silhouette, kernel) == 0
    if np.any(exterior) and np.max(abs(pixels[exterior]-background)) > 18:
        return None
    color, background_color = color_name(fill), color_name(background)
    rim_color = color_name(rim) if rim is not None else None
    if color is None or background_color is None or (rim is not None and rim_color is None):
        return None
    ending = 'er' if shape == 'Kreis' else 'es'
    description = f'Ein {adjective(color, ending)} {shape}'
    if rim is not None:
        description += f' mit {adjective(rim_color, "em")} Rand'
    description += f'. Hintergrund: {background_color}.'
    return dict(kind='plain_shape', shape=shape, description=description,
                fill_color=color, background_color=background_color, rim_color=rim_color,
                fill_rgb=fill.tolist(), background_rgb=background.tolist(),
                rim_rgb=rim.tolist() if rim is not None else None,
                message=f'Einfache Grundform erkannt: {shape}. Bitte am Original prüfen.')


class ImageRecognition:
    def __init__(self, root, payload_loader=None):
        self.root = Path(root).resolve()
        self.payload_loader = payload_loader
        self.lock = threading.RLock()
        self._stamp = None
        self.references = []
        self.skipped = Counter()

    def _inside(self, value):
        path = (self.root/value).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError('Reference outside project')
        return path

    def _payload(self):
        if self.payload_loader:
            return self.payload_loader()
        from src.iCCModules.imageCompositeConverterDescriptions import loadCatalogDescriptionMappingImpl
        from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
        from src.imageConverterCatalog import read_json
        directory = self.root/'artifacts/gui/catalog-quality'
        pointer = read_json(directory/'current.json', {}).get('id', '')
        folder = self.root/'artifacts/catalog_inventory'
        if len(pointer) == 32 and all(c in '0123456789abcdef' for c in pointer):
            current = directory/pointer/'report'
            if (current/'manifest.json').is_file():
                folder = current
        payload = read_json(folder/'manifest.json', dict(rows=[]))
        reserved = set()
        for path in (self.root/'config').glob('real_composition_holdout*.json'):
            policy = read_json(path, {})
            if policy.get('evaluation_policy', {}).get('status') == 'sealed_unrun':
                for case in policy.get('cases', []):
                    reserved.update(name.casefold() for name in [case['file'], *case.get('family_members', [])])
        mapping = {key.casefold(): text for key, text in loadCatalogDescriptionMappingImpl(self.root).items()}
        for row in payload['rows']:
            if row['filename'].casefold() in reserved:
                row['status'] = 'reserved'
            if mapping:
                keys = (row['filename'], Path(row['filename']).stem, getBaseNameFromFileImpl(row['filename']))
                row['description'] = next((mapping[key.casefold()] for key in keys if key.casefold() in mapping), '')
        return payload

    def refresh(self):
        payload = self._payload()
        rows = [row for row in payload.get('rows', []) if row.get('role') == 'catalog'
                and row.get('status') == 'pixel_pass' and not row.get('source_conflict')]
        def stamp(row):
            values = [row.get('description', ''), row.get('image_sha256'), (row.get('selected') or {}).get('svg_sha256'),
                      json.dumps((row.get('selected') or {}).get('measurement', {}).get('renderers', {}), sort_keys=True)]
            for value in (row.get('image', ''), (row.get('selected') or {}).get('svg', '')):
                try:
                    path = self._inside(value)
                    stat = path.stat()
                    values.extend((str(path), stat.st_mtime_ns, stat.st_size))
                except (OSError, ValueError):
                    values.append(None)
            return tuple(values)
        current = tuple(stamp(row) for row in rows)
        if current == self._stamp:
            return
        references, skipped = [], Counter()
        mapping = {r['filename']: r.get('description', '') for r in payload.get('rows', [])
                   if r.get('status') != 'reserved'}
        for row in rows:
            try:
                selected = row.get('selected') or {}
                checks = selected.get('measurement', {}).get('renderers', {})
                if not all(checks.get(renderer, {}).get('satisfactory') is True for renderer in ('mupdf', 'librsvg')):
                    skipped['unconfirmed_pair'] += 1
                    continue
                source, svg = self._inside(row['image']), self._inside(selected['svg'])
                source_data, svg_data = source.read_bytes(), svg.read_bytes()
                if (hashlib.sha256(source_data).hexdigest() != row['image_sha256'] or
                        hashlib.sha256(svg_data).hexdigest() != selected['svg_sha256']):
                    skipped['changed_pair'] += 1
                    continue
                tree = ET.fromstring(svg_data)
                tags = Counter(node.tag.rsplit('}', 1)[-1] for node in tree.iter())
                if tags['image'] or tags['script'] or tags['foreignObject']:
                    skipped['non_native_svg'] += 1
                    continue
                from src.imageConverterClasses import description_issue
                from src.iCCModules.imageCompositeConverterSimilarity import resolve_similarity_description
                from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
                text = row.get('description', '').strip()
                if description_issue(text):
                    skipped['missing_description'] += 1
                    continue
                text = resolve_similarity_description(text, mapping, base_name=getBaseNameFromFileImpl).text
                image = rgb_image(source_data)
                token = hashlib.sha256(source_data+svg_data).hexdigest()
                references.append(dict(token=token, filename=row['filename'], description=text,
                    image=row['image'], svg=selected['svg'], pixel_sha256=pixel_digest(image),
                    image_sha256=row['image_sha256'], svg_sha256=selected['svg_sha256'],
                    structure={k: v for k, v in tags.items() if k in {'circle', 'ellipse', 'rect', 'path', 'line', 'polygon', 'polyline', 'text'}},
                    features=descriptor(image)))
            except (OSError, ValueError, KeyError, ET.ParseError):
                skipped['unreadable_pair'] += 1
        self.references, self.skipped, self._stamp = references, skipped, current

    def recognize(self, image):
        with self.lock:
            self.refresh()
            digest, features = pixel_digest(image), descriptor(image)
            ranked = sorted(((distance(features, ref['features']), ref) for ref in self.references), key=lambda pair: pair[0])
            exact = [ref for _, ref in ranked if ref['pixel_sha256'] == digest]
            # Duplicate pixels can carry contradictory catalog descriptions.
            descriptions = {ref['description'] for ref in exact}
            automatic = None
            if len(descriptions) == 1:
                automatic = dict(kind='exact_reference', description=exact[0]['description'],
                    message=f"Bildinhalt wiedererkannt: {exact[0]['filename']} (identische Bildpunkte).")
            if not exact:
                automatic = plain_shape(image)
            matches, seen = [], set()
            for score, ref in ranked:
                if len(matches) == 3 or score > .22:
                    break
                if ref['description'] in seen:
                    continue
                seen.add(ref['description'])
                match = {key: ref[key] for key in ('token', 'filename', 'description', 'structure')}
                match.update(distance=round(score, 5), exact=ref['pixel_sha256'] == digest,
                             source_url=f"/api/recognition/reference/{ref['token']}/source",
                             svg_url=f"/api/recognition/reference/{ref['token']}/svg")
                matches.append(match)
            message = (automatic['message'] if automatic else
                       'Identische Bildpunkte haben unterschiedliche Beschreibungen. Bitte eine Beschreibung prüfen.' if len(descriptions) > 1 else
                       'Ähnliche geprüfte Bilder gefunden. Unterschiede und Beschriftungen bitte prüfen.' if matches else
                       'Keine sichere Erkennung. Bitte die Bildbeschreibung ergänzen.')
            return dict(version=VERSION, reference_count=len(self.references), skipped=dict(self.skipped),
                        automatic=automatic, matches=matches, message=message)

    def asset(self, token, kind):
        with self.lock:
            self.refresh()
            reference = next((ref for ref in self.references if ref['token'] == token), None)
            if reference is None:
                return None
            return self._inside(reference['image' if kind == 'source' else 'svg'])
