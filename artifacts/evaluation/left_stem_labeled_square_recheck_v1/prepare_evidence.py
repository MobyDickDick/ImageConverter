"""Freeze original inputs before implementing the left-handle registration."""
from pathlib import Path
import hashlib
import json
import subprocess
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
if (FOLDER/'manifest.json').exists():
    raise ValueError('Frozen inputs already exist; do not overwrite the original baseline')
description = ('Kelle mit einem gefüllten Quadrat mit Kontur und mittigem waagerechtem Griff nach links. '
               'Im Quadrat steht der horizontale Text "M". Weißer Hintergrund. '
               'Lage, Abmessungen, Strichbreiten, Schriftgröße und Farben ergeben sich aus dem Bild.')
source = ROOT/'artifacts/images_to_convert/SE0082.jpg'
originals = {}
for catalog in ('artifacts/descriptions/Finale_Wurzelformen_V3.xml',
                'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'):
    entry = next(e for e in ET.parse(ROOT/catalog).iter('entry') if e.get('key') == source.stem)
    originals[catalog] = entry.findtext('beschreibung')
manifest = dict(label='M', stem_direction='left', description=description,
    provenance=dict(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                    seed=0, toolchain='local Python 3.10 venv; real guarded CLI; deterministic order',
                    baseline_kind='frozen unmodified runtime and original description'),
    cases=[dict(case_id='anonymous_symbol_00', source=source.name, image='../../images_to_convert/'+source.name,
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                baseline_description=next(iter(originals.values())), description=description)],
    original_descriptions=originals)
(FOLDER/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(FOLDER/'description.txt').write_text(description+'\n', encoding='utf-8')
# Independent geometry, palette, label and canvas; reference only used by the test driver.
(FOLDER/'independent.svg').write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="86" height="62">'
    '<path d="M 34 29 L 7 29" fill="none" stroke="#65738a" stroke-width="2.2"/>'
    '<rect x="34" y="10" width="38" height="38" fill="#e7ceaa" stroke="#486279" stroke-width="1.8"/>'
    '<text x="53" y="38" font-size="24" font-weight="600" font-family="Arial, Helvetica, sans-serif" '
    'text-anchor="middle" fill="#3a4f72">P</text></svg>', encoding='utf-8')
(FOLDER/'independent.txt').write_text(description.replace('"M"', '"P"'), encoding='utf-8')
(FOLDER/'frozen_source_hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (ROOT/'src').rglob('*.py')}, indent=2)+'\n', encoding='utf-8')
