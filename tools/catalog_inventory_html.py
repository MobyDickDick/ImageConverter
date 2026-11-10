"""Render the complete inventory before optional JavaScript enhancement."""
from datetime import datetime, timezone
from html import escape
import math
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _text(value):
    return escape(str(value), quote=True)


def _number(value):
    return f'{value:,}'.replace(',', '’')


def _link(label, url):
    # Report links are relative paths created by the inventory writer.
    if not url or urlsplit(url).scheme or urlsplit(url).netloc:
        return _text(label)
    return f'<a href="{_text(url)}" target="_blank" rel="noopener">{_text(label)}</a>'


def _metric(value):
    return f'{value:.5f}' if isinstance(value, (int, float)) and math.isfinite(value) else '–'


def _row(row, labels):
    name = _link(row['filename'], row['image_url'])
    if row['status'] != 'reserved':
        name += f'<br><img src="{_text(row["image_url"])}" alt="{_text(row["filename"])}" loading="lazy">'
    description = _text(row['description'] or 'Keine Beschreibung hinterlegt')
    archive = row.get('archive')
    if archive and not archive['description_matches_catalog']:
        description += ('<details><summary>Abweichende Archivbeschreibung</summary><p>'
                        +_text(archive['description'])+'</p></details>')
    admission = 'Historisch archiviert' if row['archived'] else 'Keine Archivabnahme'
    if archive:
        intact = all(archive[k] for k in ('source_matches', 'image_hash_matches', 'svg_hash_matches'))
        admission += '<p>'+('Bild-/SVG-Prüfsummen stimmen' if intact else 'Prüfsumme oder Quellzuordnung abweichend')+'</p>'
        if not archive['description_matches_catalog']:
            admission += '<p class="note">Beschreibung abweichend</p>'
        admission += (_link('Abnahmebeleg', row['evidence_url']) if row.get('evidence_url')
                      else '<p class="note">Belegdatei fehlt</p>')
    quality = f'<div class="status {_text(row["status"])}">{_text(labels[row["status"]])}</div>'
    selected = row['selected']
    if selected:
        measurement = selected['measurement']
        for renderer, check in measurement.get('renderers', {}).items():
            verdict = 'Messfehler' if check.get('error') else 'bestanden' if check['satisfactory'] else 'Grenzen verfehlt'
            metrics = check.get('metrics', {})
            detail = check.get('error') or ('MSE '+_metric(metrics.get('normalized_mse'))
                +' · FG-MSE '+_metric(metrics.get('foreground_mse'))
                +' · IoU '+_metric(metrics.get('foreground_iou'))
                +' · Kanten '+_metric(metrics.get('edge_alignment')))
            quality += ('<details><summary>'+_text(renderer+': '+verdict)+'</summary><p>'+_text(detail)+'</p>'
                        +('<p>'+_text(', '.join(check['failures']))+'</p>' if check.get('failures') else '')+'</details>')
        if measurement.get('error'):
            quality += '<p>'+_text(measurement['error'])+'</p>'
    output = 'Messung gesperrt' if row['status'] == 'reserved' else 'Kein ausgewertetes SVG'
    if row.get('svg_url'):
        output = (_link('SVG öffnen', row['svg_url'])+'<small>'+_text(selected['svg'])+'</small>'
                  +f'<p>{len(row["candidates"])} unterschiedliche gespeicherte Ausgabe(n)</p>')
        if archive:
            output += ('<details><summary>Historischer Archivwert</summary><p>MSE '
                       +_metric(archive['historical_metrics'].get('error_per_pixel'))+'</p></details>')
    return ('<tr><td>'+name+'</td><td class="desc">'+description+'</td><td>'+admission
            +'</td><td>'+quality+'</td><td class="links">'+output+'</td></tr>')


def render_catalog_html(template, payload):
    import json

    template = re.sub(r'<!-- CATALOG_TEMPLATE_NOTICE_START -->.*?<!-- CATALOG_TEMPLATE_NOTICE_END -->\n?',
                      '', template, flags=re.S)
    summary = payload['summary']
    total = summary['catalog_bitmaps']
    cards = [
        (total, 'Katalogbitmaps', f'plus {summary["auxiliary_bitmaps"]} Hilfsgrafiken'),
        (summary['archived'], 'Historisch archiviert', f'{100*summary["archived"]/total:.1f} % des Katalogs' if total else '0 % des Katalogs'),
        (summary['catalog_statuses'].get('pixel_pass', 0), 'Aktuelle Rastergates erfüllt', 'gespeicherte SVGs, beide Renderer'),
        (summary['catalog_statuses'].get('no_svg', 0), 'Ohne gespeichertes SVG', 'Konvertierbarkeit noch offen'),
        (summary['descriptions_present'], 'Mit Katalogbeschreibung', f'{len(summary["missing_descriptions"])} Beschreibung(en) fehlen'),
    ]
    stamp = datetime.fromisoformat(summary['generated_at'])
    try:
        stamp = stamp.astimezone(ZoneInfo('Europe/Zurich'))
    except ZoneInfoNotFoundError:
        stamp = stamp.astimezone(timezone.utc)
    replacements = dict(
        __CATALOG_STAMP__=_text('Bestandsaufnahme '+stamp.strftime('%d.%m.%Y %H:%M %Z')+' · ImageConverter'),
        __CATALOG_CARDS__=''.join('<div class="card"><strong>'+_number(n)+'</strong><div>'+_text(title)
                                +'</div><small>'+_text(sub)+'</small></div>' for n, title, sub in cards),
        __CATALOG_COUNT__=_number(len(payload['rows'])),
        __CATALOG_ROWS__='\n'.join(_row(row, payload['labels']) for row in payload['rows']),
        __CATALOG_DATA__=json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c'),
    )
    # One substitution pass: literal marker text inside descriptions stays text.
    return re.sub(r'__CATALOG_[A-Z]+__', lambda match: replacements[match[0]], template)
