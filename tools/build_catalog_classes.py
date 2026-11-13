"""Rebuild geometric classes from today's complete catalog without conversion."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.parse import quote

from src.imageConverterClasses import enrich_catalog
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
from tools.build_catalog_inventory import discover, digest, relative, read_json

ROOT = Path(__file__).resolve().parents[1]


def build_classes(root, quality_path=None):
    root = root.resolve()
    desc_path, descriptions, names, copies, _, archive, _, reserved = discover(root)
    quality_path = quality_path or root/'artifacts/catalog_inventory/manifest.json'
    quality = read_json(quality_path, {})
    old_rows = {r['filename'].casefold(): r for r in quality.get('rows', [])}
    rows = []
    for name, paths in sorted(copies.items()):
        source = paths[0]
        variant = source.stem
        key = next((k for k in (source.name, variant, variant.upper(), variant.lower(),
                    getBaseNameFromFileImpl(variant), getBaseNameFromFileImpl(variant).upper()) if descriptions.get(k)), None)
        description = descriptions.get(key, '')
        hashes = [digest(p.read_bytes()) for p in paths]
        old = old_rows.get(name, {})
        same = old.get('image_sha256') == hashes[0] and old.get('description') == description
        status = 'reserved' if name in reserved else 'source_conflict' if len(set(hashes)) > 1 else old.get('status', 'unmeasured') if same else 'unmeasured'
        row = dict(filename=source.name, variant=variant, image=relative(root, source),
                   image_sha256=hashes[0], description=description,
                   role='auxiliary' if source.suffix.lower() == '.gif' and name not in names else 'catalog',
                   archived=variant.casefold() in archive, status=status,
                   quality_evidence_matches_current_input=same and status not in {'reserved','source_conflict'},
                   selected_svg=(old.get('selected') or {}).get('svg') if same and status != 'reserved' else None)
        rows.append(row)
    summary = enrich_catalog(root, rows)
    summary.update(generated_at=datetime.now(timezone.utc).isoformat(),
                   quality_snapshot_generated_at=quality.get('summary', {}).get('generated_at'),
                   quality_snapshot=relative(root, quality_path),
                   descriptions_sha256=digest(desc_path.read_bytes()),
                   quality_snapshot_sha256=digest(quality_path.read_bytes()) if quality_path.is_file() else None,
                   classification_source_sha256=digest((ROOT/'src/imageConverterClasses.py').read_bytes()),
                   builder_source_sha256=digest(Path(__file__).read_bytes()),
                   visual_review_sha256=digest((root/'config/catalog_class_visual_review.json').read_bytes())
                       if (root/'config/catalog_class_visual_review.json').is_file() else None,
                   statuses=dict(Counter(r['status'] for r in rows if r['role'] == 'catalog')),
                   interpretation='Geometric assignment and existing partial model availability; not full model-contract or conversion acceptance.')
    return rows, summary


def write_classes(root, output, rows, summary):
    output.mkdir(parents=True, exist_ok=True)
    payload = dict(summary=summary, rows=rows)
    (output/'manifest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    fields = ['filename','class_id','subclass_id','class_label','basis','description_issue','status','archived',
              'model_modules','model_limit','reason','image','description']
    with (output/'classes.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fields, delimiter=';')
        writer.writeheader()
        for r in rows:
            c = r['classification']
            writer.writerow(dict(filename=r['filename'], class_id=c['class_id'], subclass_id=c.get('subclass_id'), class_label=c['label'],
                basis=c['basis'], description_issue=c['description_issue'], status=r['status'], archived=r['archived'],
                model_modules=', '.join(c['model_modules']), model_limit=c['model_limit'], reason=c['reason'],
                image=r['image'], description=r['description']))
    groups = summary['classes']
    table = '\n'.join(f'| {v["label"]} | {v["total"]} | {v["saved_pixel_pass"]} | {v["archived"]} |'
                      for v in groups.values())
    markdown = f'''# Geometrische Klassen des gesamten Bildkatalogs

{summary['catalog_bitmaps']} Katalogbilder: {summary['assigned']} geometrisch zugeordnet,
{summary['unresolved']} zu klären, {summary['reserved']} reserviert.
{summary['visual_audited']} Zuordnungen sind durch Sichtprüfung der Quellbilder ergänzt.
{summary['automatic_proposals']} Zuordnungen sind noch automatische Vorschläge aus Beschreibungen.

| Klasse | Bilder | Vorhandenes SVG mit Rasterpass | Historisch archiviert |
| --- | ---: | ---: | ---: |
{table}

## Einordnung

Die Klassen gruppieren Geometrie und Komposition, nicht Bildnummern. Zu jeder
Zuordnung stehen vorhandene native Modelle und deren Grenzen in der Gesamtliste.
Die Modelle decken Teile der Klasse ab; die Mitgliedschaft beweist weder einen
passenden vollständigen Modellvertrag noch eine erfolgreiche Konvertierung.
Ein Pixel-Fehlschlag ist kein Nachweis grundsätzlicher Nichtkonvertierbarkeit.
Die {summary['visual_audited']} Sichtzuordnungen werden eigens markiert. Sie beruhen
auf den sichtbaren Formen jedes einzelnen Bildes einschließlich der Größenvarianten.
Die beobachteten Unterformen und Anbauten stehen bei der jeweiligen Zuordnung.
Die verbleibenden {summary['automatic_proposals']} beschreibungsbasierten Vorschläge
sind noch nicht an den Originalbildern geprüft.

Die Qualitätszahlen stammen aus dem vorhandenen Snapshot
`{summary['quality_snapshot_generated_at']}` und werden nur bei identischen
Bildbytes und Beschreibungen übernommen. Es wurde keine neue Konvertierung
oder Rastermessung durchgeführt. Archiv und Rasterpass überlappen.
Reservierte Bilder bleiben ohne neue geometrische Zuordnung.

Beschreibungsprobleme: `{json.dumps(summary['description_issues'], ensure_ascii=False)}`.
Platzhalter mit Vorschlagslisten (Kreis/Ellipse/Rechteck/Polygon) zählen nicht als
Beobachtung dieser Formen. Sichtzuordnungen sind an die Bildbytes gebunden;
der damalige Beschreibungshash bleibt als Herkunft dokumentiert. Eine reine
Textkorrektur verwirft eine bildunabhängig geprüfte Zuordnung nicht. Veränderte
Bildbytes verwerfen sie. Die Zuordnung ist keine menschliche fachliche Freigabe.

## Dateien und Wiederholung

- [Durchsuchbare Gesamtliste](index.html), mit Originalbildern und Klassenauswahl.
- [Alle Zuordnungen als CSV](classes.csv).
- [Vollständige Zuordnungen und Herkunft als JSON](manifest.json).
- [Bilanz und Prüfsummen](summary.json).

Im Projektverzeichnis: `.venv/Scripts/python.exe -m tools.build_catalog_classes`.
Die Konvertierungsqualität im lokalen Webserver zeigt dieselben Klassen.
'''
    if (output/'review_summary.json').is_file():
        markdown += ('\n## Vollständige Sichtprüfung\n\n'
                     '- [Bilanz und Vollständigkeitsprüfungen](review_summary.json).\n'
                     '- [Geänderte Klassenzuordnungen als CSV](review_changes.csv).\n'
                     '- [Quelldateien und Zellen der geprüften Kontaktbögen](review_manifest.json).\n')
    (output/'README.md').write_text(markdown, encoding='utf-8')
    h = lambda value: escape(str(value or ''), quote=True)
    options = ''.join(f'<option value="{h(k)}">{h(v["label"])} ({v["total"]})</option>' for k,v in groups.items())
    from tools.build_catalog_inventory import LABELS
    bases = dict(description_rule='Automatischer Vorschlag aus der Beschreibung',
                 visual_audit='Zuordnung durch Codex-Sichtprüfung', reservation='Reserviert')
    html_rows = []
    for r in rows:
        c = r['classification']
        url = quote(os.path.relpath(root/r['image'], output).replace('\\', '/'), safe='/')
        thumbnail = '' if c['class_id'] == 'reserved' else f'<a href="{h(url)}"><img loading="lazy" src="{h(url)}" alt="{h(r["filename"])}"></a>'
        html_rows.append(f'<tr data-class="{h(c["class_id"])}"><td>{h(r["filename"])}<br>{thumbnail}</td>'
            f'<td><strong>{h(c["label"])}</strong><p>{h(c["reason"])}</p><small>{h(bases[c["basis"]])}</small></td>'
            f'<td>{h(", ".join(c["model_modules"]))}<p>{h(c["model_limit"])}</p></td>'
            f'<td>{h(LABELS.get(r["status"], "Keine passende vorhandene Messung"))}<br>Archiv: {"ja" if r["archived"] else "nein"}</td>'
            f'<td>{h(r["description"])}<p>Beschreibungsproblem: {h(c["description_issue"] or "keines erkannt")}</p></td></tr>')
    html = f'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Geometrische Bildklassen</title><style>
body{{font:15px system-ui;margin:2rem;color:#172e40;background:#f7fafc}} h1{{font-size:1.8rem}}
table{{border-collapse:collapse;width:100%;background:white}}td,th{{border:1px solid #cbd6df;padding:12px;text-align:left;vertical-align:top}}
td:first-child{{min-width:160px}}img{{max-width:140px;max-height:110px;margin-top:8px}}small{{color:#526779}}
input,select{{padding:10px;margin:10px 10px 20px 0;max-width:95%}}input{{width:300px}}[hidden]{{display:none!important}}</style>
<h1>Geometrische Bildklassen</h1><p>{summary['assigned']} von {summary['catalog_bitmaps']} Bildern zugeordnet · {summary['unresolved']} zu klären · {summary['reserved']} reserviert</p>
<p>Vorhandene Modelle decken Teile einer Klasse ab. Die Zuordnung ist keine Konvertierungszusage.
{summary['visual_audited']} Bilder sind am Original geprüft; {summary['automatic_proposals']} Zuordnungen sind noch automatische Vorschläge.
Qualitätswerte stammen aus dem vorhandenen Snapshot; keine neue Konvertierung.</p>
<p><a href="classes.csv">CSV herunterladen</a> · <a href="manifest.json">JSON</a> · <a href="README.md">Bilanz und Grenzen</a></p>
<label>Suche <input id="search" placeholder="Datei, Geometrie oder Modell"></label>
<label>Klasse <select id="classes"><option value="">Alle Klassen</option>{options}</select></label>
<span id="count">{len(rows)} Bilder</span>
<table><thead><tr><th>Original</th><th>Geometrische Klasse</th><th>Vorhandene Modelle und Grenzen</th><th>Gespeicherte Qualität</th><th>Beschreibung</th></tr></thead>
<tbody>{''.join(html_rows)}</tbody></table>
<script>const rows=[...document.querySelectorAll('tbody tr')];function filter(){{const q=document.querySelector('#search').value.toLocaleLowerCase('de'),c=document.querySelector('#classes').value;let n=0;for(const r of rows){{r.hidden=!!((c&&r.dataset.class!==c)||(q&&!r.textContent.toLocaleLowerCase('de').includes(q)));if(!r.hidden)n++;}}document.querySelector('#count').textContent=n+' Bilder';}}document.querySelector('#search').oninput=filter;document.querySelector('#classes').onchange=filter;</script></html>'''
    (output/'index.html').write_text(html, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/catalog_classes')
    parser.add_argument('--quality-manifest', type=Path)
    args = parser.parse_args()
    rows, summary = build_classes(args.root, args.quality_manifest)
    write_classes(args.root, args.output, rows, summary)
    print(json.dumps({k:summary[k] for k in ('catalog_bitmaps','assigned','unresolved','reserved','visual_audited','description_issues')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
