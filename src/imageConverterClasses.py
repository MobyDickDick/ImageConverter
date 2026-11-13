"""Geometric catalog taxonomy, independent of names and conversion verdicts.

This is reporting metadata, never a dispatch or acceptance rule. A class names
available representations; membership does not prove an entire image fits a
model's bounded contract. Visual annotations live separately and are hash bound.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import json
import re

SCHEMA = 'catalog_geometry_classes_v1'

# Paths name actual implementations, not promised coverage of every member.
CLASSES = {
    'disk_label': ('Kreis/Ellipse mit Text und optionalen Anschlüssen',
        ['SemanticBadgeRuntime', 'ShortLabelDisk', 'LabeledDisk'],
        'Kreis und Kurztext vorhanden; Ellipsen, beliebige Labels und Anbauten nur teilweise.'),
    'disk_triangle': ('Kreis mit Dreieck / Pumpe / Kompressor',
        ['Pump', 'GeometryIr/runtime'], 'Native Kreis-/Dreieckmodelle; Variantenvertrag einzeln prüfen.'),
    'disk_marks': ('Kreis mit Linien, Kreuz, Balken oder Pfeil',
        ['CircleLinework', 'DiagonalCrossDisk', 'FilledSymbols', 'DiskArrow'],
        'Mehrere konkrete Innenzeichen vorhanden; keine beliebige Kombination.'),
    'disk_spiral': ('Kreis mit Spirale oder gebogenen Innenlinien',
        ['SpiralDisk'], 'Begrenztes Spiralmodell; andere Kurvenkompositionen offen.'),
    'disk_radial': ('Kreis/Kugel mit radialem Verlauf',
        ['RadialDisk'], 'Radiales Kreismodell vorhanden; zusätzliche Zeichen gesondert prüfen.'),
    'disk_plain': ('Kreis/Ellipse, Füllung, Kontur oder Verlauf',
        ['FilledSymbols', 'LayeredScene', 'MixedGradientScene'],
        'Kreise in begrenzten Szenen vorhanden; Ellipsen und 3-D-Effekte teilweise.'),
    'valve': ('Ventil / Dreiecksflügel mit Stellglied',
        ['ThreeWayValve', 'MotorValve', 'GeometryIr/runtime'],
        'Zwei-/Dreiwegmodelle vorhanden; Quadratstellglieder und Kombinationen teilweise.'),
    'panel_marks': ('Rechteck mit Linien, Kreuz, Zeichen oder Anschluss',
        ['HeatPanel', 'CrossedGradientPanel', 'DiagonalCrossPanel', 'PairedLinePanel', 'ZigzagPanel', 'SquareStem'],
        'Mehrere native Panelmodelle; beliebige Innenzeichen/Gelenke nicht vollständig abgedeckt.'),
    'panel_plain': ('Rechteck/Quadrat mit Kontur, Füllung oder Verlauf',
        ['AxialPanel', 'FramedPanel', 'GradientScene', 'LayeredScene'],
        'Native Rechteckmodelle einschließlich Rundung; Verlaufsart und Beschreibung müssen passen.'),
    'panel_curves': ('Panel/Röhre mit Kurven oder räumlichem Effekt',
        ['ChevronPanel', 'ArcShaft', 'GeometryIr/runtime'],
        'Gerade V-Panels und einzelne Bögen vorhanden; allgemeine Kurvenflächen offen.'),
    'arrows_lines': ('Pfeile, Linien, Dreiecke und Verzweigungen',
        ['ArrowPair', 'GradientArrow', 'GradientJunction', 'ArcShaft', 'FilledSymbols'],
        'Native Grundformen, offene Bogenanschlüsse und Gruppen vorhanden; Topologie/Anzahl begrenzt.'),
    'diagram': ('Achsendiagramm / Stufen / Sinus',
        ['StepDiagram', 'SineDiagram', 'GeometryIr/runtime'],
        'Stufen- und Sinusmodelle vorhanden; andere Kurven und Beschriftungen teilweise.'),
    'geometric_scene': ('Mehrere geometrische Formen / Überdeckung / Verschachtelung',
        ['PrimitiveScene', 'LayeredScene', 'SceneVisibility', 'MixedGradientScene'],
        'Komposition vorhanden, aber Formvokabular, Anzahlen und Beschreibungsverträge begrenzt.'),
    'icon_geometric': ('Geometrisches Piktogramm / Button / Flagge / Haken',
        ['WarningDisk', 'HouseDisk', 'StripedPanelDisk', 'CheckboxCheckmark'],
        'Einige Piktogramme direkt vorhanden; Uhren, Flaggen und neue Kombinationen teilweise.'),
    'icon_curved': ('Kurviges Piktogramm / Flamme / Glocke / Tropfen / Werkzeug',
        ['FlameDisk', 'AlarmBell', 'SpiralDisk'],
        'Flamme/Glocke/Spirale teilweise vorhanden; freie Konturen und Kombinationen offen.'),
    'complex_photo': ('Foto / dichtes oder organisches Motiv', [],
        'Kein allgemeines natives Rekonstruktionsmodell; Vereinfachung oder neue Modelle nötig.'),
    'unresolved': ('Geometrie noch zu klären', [],
        'Keine belastbare Zuordnung; weder Komplexität noch Nichtkonvertierbarkeit behauptet.'),
    'reserved': ('Reservierter Prüfbestand', [], 'Keine neue Klassifikation oder Konvertierung.'),
}


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def description_issue(description):
    text = str(description or '').casefold().strip()
    if not text:
        return 'missing'
    if 'unzugeordnete wurzelform' in text or 'bis zur fachlichen zuordnung' in text:
        return 'placeholder'
    # A reference alone supplies no geometry. Resolved prose is used by callers.
    if not re.search(r'kreis|ellipse|rechteck|quadrat|dreieck|pfeil|linie|strich|kontur|'
                     r'fläche|form|symbol|ventil|kompressor|kopressor|kelle|verlauf|'
                     r'glocke|haken|diagramm|flamme|welle|photo|foto|button|flagge|'
                     r'werkzeug|schneeflock|tropfen|uhr|hintergrund|röhre|rohr', text):
        return 'reference_or_vague'
    return None


def _geometric_class(description):
    text = description.casefold()
    has = lambda pattern: bool(re.search(pattern, text))
    disk = has(r'kreis|ellipse|kugel|kelle|kreisscheibe')
    panel = has(r'rechteck|quadrat|viereck|panel|röhre|rohr')
    if has(r'\bphoto\b|\bfoto\b|photograph|fotograf|weltkugel|handform|hautfarbe|portrait'):
        return 'complex_photo', 'Foto, organisches Motiv oder dichte Darstellung beschrieben.'
    if has(r'ventil|ventilflügel|[23]-?weg'):
        return 'valve', 'Ventilflügel und Stellglied bzw. Ventil beschrieben.'
    if has(r'achsendiagramm|koordinatensystem|x-.*y-achse|diagrammlinie|sinuskurve|sinusdiagramm|stufendiagramm'):
        return 'diagram', 'Achsen und Diagrammgeometrie beschrieben.'
    if has(r'flamme|glocke|schrauben|schrabensch|werkzeug|wassertropf|öltropf|öltrop|hand mit|packman|sprechblase|wellen(?:symbol|form)|wellensymbol|wolke|wolcke|sonne|regentropf'):
        return 'icon_curved', 'Kurviges Piktogramm beschrieben.'
    if has(r'flagge|fahne|schneeflock|schneeflocken|haus|haken|checkbox|warn|ausrufezeichen|fragezeichen|info-button|kalender|\buhr\b|uhr:|play|pause|fast-left|halt-button|blitz|ok.zeichen'):
        return 'icon_geometric', 'Piktogramm aus geometrischen Elementen beschrieben.'
    if disk and has(r'spiral'):
        return 'disk_spiral', 'Kreis mit Spiral-/Kurveninnenzeichen beschrieben.'
    if disk and has(r'radial|kugelform'):
        return 'disk_radial', 'Radialer Verlauf beschrieben.'
    if has(r'pump|kompres|kopres') or (disk and has(r'dreieck')):
        return 'disk_triangle', 'Kreis mit Dreiecksgeometrie beschrieben.'
    if has(r'verschachtel|überdeck|überlapp|getrennt nebeneinander|getrennt untereinander|inneren formen|mehrere.*(?:kreise|rechtecke)'):
        return 'geometric_scene', 'Mehrere Instanzen und ihre Anordnung beschrieben.'
    # Consume negative label claims so "kein Text" cannot create a text class.
    positive = re.sub(r'(?:kein\w*|ohne)\s+(?:["„][^"“]*["“]\s*)?(?:text|schriftzeichen|beschriftung|buchstabe\w*)', '', text)
    if panel and disk and has(r'röhre|seitenansicht'):
        return 'geometric_scene', 'Panel-/Röhrenkörper mit angebautem Kreis oder Stellglied beschrieben.'
    if panel and disk and has(r'quadrat|viereck'):
        return 'panel_marks', 'Quadratischer Grundkörper mit Anbauten beschrieben.'
    if disk and re.search(r'buchstab|beschrift|text|\blabel\b|\blux\b|\bvoc\b|\bco.?2\b', positive):
        return 'disk_label', 'Kreis/Ellipse mit Beschriftung beschrieben.'
    if disk and has(r'linie|strich|balken|kreuz|pfeil|griff|stiel|schaft'):
        return 'disk_marks', 'Kreis und native Innen-/Anschlusslinien beschrieben.'
    if panel and has(r'geschwung|gebogen|bogen|wölb|seitenansicht|röhreneffekt'):
        return 'panel_curves', 'Panel/Röhre mit Kurven oder räumlichem Effekt beschrieben.'
    if panel and has(r'linie|strich|kreuz|diagonal|plus|minus|zeichen|griff|stiel|schaft|zickzack|\bdp\b|beschrift|text'):
        return 'panel_marks', 'Panel mit Innenzeichen oder Anbauten beschrieben.'
    if panel:
        return 'panel_plain', 'Rechteckige Grundfläche beschrieben.'
    if disk:
        return 'disk_plain', 'Runde Grundfläche beschrieben.'
    if has(r'pfeil|dreieck|linie|strich|diagonal|verzweig|band'):
        return 'arrows_lines', 'Gerade Linien-/Polygongeometrie beschrieben.'
    if has(r'hintergrund.*verlauf|verlauf.*hintergrund|farbverlauf|graustufenverlauf'):
        return 'panel_plain', 'Flächiger Verlauf beschrieben; genaue Begrenzung prüfen.'
    if has(r'button|symbol|zeichen'):
        return 'unresolved', 'Symbolname allein legt die Geometrie nicht fest.'
    return 'unresolved', 'Keine ausreichend konkrete Geometrie erkannt.'


def classify_description(description, *, visual=None, image_sha256=None, reserved=False, resolved_description=None):
    issue = description_issue(description)
    basis = 'description_rule'
    if reserved:
        key, reason, basis = 'reserved', 'Aktuelle Reservierung.', 'reservation'
    elif (visual and visual.get('image_sha256') == image_sha256
          and (visual.get('independent_of_description') is True
               or visual.get('description_sha256') == text_hash(description))):
        key, reason, basis = visual['class_id'], visual['observation'], 'visual_audit'
        if key not in CLASSES or key == 'reserved':
            raise ValueError('Unknown visual class: '+key)
    elif issue in {'missing', 'placeholder'}:
        key, reason = 'unresolved', 'Platzhalter-/fehlende Beschreibung ist keine Bildgeometrie.'
    else:
        key, reason = _geometric_class(resolved_description or description)
    title, models, limit = CLASSES[key]
    return dict(schema=SCHEMA, class_id=key, label=title, basis=basis, reason=reason,
                subclass_id=visual.get('subclass_id') if basis == 'visual_audit' else None,
                review_evidence=visual.get('review_evidence') if basis == 'visual_audit' else None,
                description_issue=issue, model_modules=models, model_limit=limit,
                model_scope='partial' if models else 'open', conversion_proven=False,
                review_status=('agent_visual_audit' if basis == 'visual_audit' else
                               'reserved' if basis == 'reservation' else 'automatic_proposal'))


def summarize(rows):
    catalog = [r for r in rows if r.get('role', 'catalog') == 'catalog']
    groups = {}
    for key, (label, models, limit) in CLASSES.items():
        members = [r for r in catalog if r['classification']['class_id'] == key]
        if members:
            groups[key] = dict(label=label, total=len(members),
                archived=sum(bool(r.get('archived')) for r in members),
                saved_pixel_pass=sum(r.get('status') == 'pixel_pass' for r in members),
                description_issues=dict(Counter(r['classification']['description_issue'] for r in members
                                               if r['classification']['description_issue'])),
                model_modules=models, model_limit=limit,
                examples=[r['filename'] for r in members[:3]])
    return dict(schema=SCHEMA, catalog_bitmaps=len(catalog), classes=groups,
                assigned=sum(r['classification']['class_id'] not in {'unresolved', 'reserved'} for r in catalog),
                unresolved=sum(r['classification']['class_id'] == 'unresolved' for r in catalog),
                reserved=sum(r['classification']['class_id'] == 'reserved' for r in catalog),
                visual_audited=sum(r['classification']['basis'] == 'visual_audit' for r in catalog),
                automatic_proposals=sum(r['classification']['basis'] == 'description_rule' for r in catalog),
                description_issues=dict(Counter(r['classification']['description_issue'] for r in catalog
                                               if r['classification']['description_issue'])),
                fresh_conversion_performed=False)


def annotate_rows(rows, reviews=None):
    """Attach metadata only; leave existing acceptance and measurement data intact."""
    reviews = reviews or {}
    for row in rows:
        row['classification'] = classify_description(row.get('description', ''),
            visual=reviews.get(row['filename'].casefold()), image_sha256=row.get('image_sha256'),
            reserved=row.get('status') == 'reserved', resolved_description=row.get('classification_description'))
    return summarize(rows)


def enrich_catalog(root, rows):
    """Use documented reference prose and optional pinned visual annotations.

    No vectors, raster detectors or conversion routines are read/run here.
    References affect reporting only and cannot change the conversion input.
    """
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    review_path = root/'config/catalog_class_visual_review.json'
    reviews = json.loads(review_path.read_text(encoding='utf-8')).get('cases', {}) if review_path.is_file() else {}
    source = root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
    mapping = loadDescriptionMappingImpl(str(source), get_base_name_from_file_fn=getBaseNameFromFileImpl) if source.is_file() else {}
    reference = re.compile(r'\b[A-Z][A-Z0-9_]*\d[A-Z0-9_]*\b', re.I)

    @lru_cache(maxsize=4096)
    def resolve(text, seen=()):
        if len(seen) >= 8 or description_issue(text) in {'missing', 'placeholder'}:
            return text
        additions = []
        for name in dict.fromkeys(m[0].upper() for m in reference.finditer(text)):
            extra = mapping.get(name, '')
            if name not in seen and extra and extra != text and description_issue(extra) not in {'missing', 'placeholder'}:
                additions.append(resolve(extra, (*seen, name)))
        return (text + (' '+ ' '.join(dict.fromkeys(additions)) if additions else ''))[:24000]

    for row in rows:
        # Never interpret sealed descriptions or use them as new class evidence.
        if row.get('status') != 'reserved':
            visual = reviews.get(row['filename'].casefold(), {})
            if (visual.get('image_sha256') == row.get('image_sha256')
                    and visual.get('independent_of_description') is True):
                row.pop('classification_description', None)
            else:
                row['classification_description'] = resolve(row.get('description', ''))
    return annotate_rows(rows, reviews)
