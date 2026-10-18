"""Freeze source descriptions, hashes and the previous satisfactory archive."""
from pathlib import Path
import hashlib
import json
import subprocess
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
DESCRIPTION = ('Ein 3-Wege-Ventil mit drei spitzen Dreiecken links, oben und unten, '
    'die sich in einer gemeinsamen Spitze treffen. Die Dreiecke haben einen '
    'diagonalen Grauverlauf von dunkel links unten nach hell rechts oben und eine graue Randkontur. '
    'Von der gemeinsamen Spitze führt ein waagerechter gerader Griff nach rechts '
    'zur linken Seite einer hellen Kreisscheibe mit dunkler Randkontur. '
    'Darin steht der einzelne dunkle Großbuchstabe "M" aufrecht in fetter serifenloser Schrift. '
    'Weißer Hintergrund. Keine weiteren Objekte. Maße und Farben ergeben sich aus dem Bild.')

def main():
    if (FOLDER/'manifest.json').exists():
        raise SystemExit('The original baseline already exists; use run_evidence.py for replay.')
    table = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml')
    cases = []
    for number, size in enumerate(('M', 'L', 'S')):
        source = f'AC0232_{size}.jpg'
        entry = next(e for e in table.iter('entry') if source in [p.text for p in e.findall('bilder/bild')])
        cases.append(dict(case_id=f'anonymous_motor_valve_{number:02}', source=source,
            image='../../images_to_convert/'+source,
            source_sha256=hashlib.sha256((ROOT/'artifacts/images_to_convert'/source).read_bytes()).hexdigest(),
            baseline_description=entry.findtext('beschreibung'), description=DESCRIPTION))
    manifest = dict(schema_version='motor_valve_recheck_v1', cases=cases, description=DESCRIPTION,
        provenance=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            seed=0, search_seed=20261018, toolchain='CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7'))
    (FOLDER/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = json.loads((archive/'index.json').read_text(encoding='utf-8'))
    safety = {c['variant']:hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest() for c in index['cases']}
    (FOLDER/'archive_safety.json').write_text(json.dumps(safety,indent=2)+'\n',encoding='utf-8')

if __name__ == '__main__':
    main()
