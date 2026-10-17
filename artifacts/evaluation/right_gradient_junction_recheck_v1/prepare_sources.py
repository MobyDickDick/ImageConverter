"""Freeze the next catalog family before changing its text or runtime."""
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import cv2

FOLDER = Path(__file__).resolve().parent
DESCRIPTION = ('Eine T-Verzweigung aus einem senkrechten rechteckigen Balken und '
    'einem mittig nach rechts anschließenden waagerechten rechteckigen Schaft. '
    'Beide Arme sind verbunden und haben quer zu ihrer Längsrichtung einen '
    'Farbverlauf mit heller Mitte und dunkleren Rändern. Der Übergang ist auf '
    'Gehrung verbunden. Weißer Hintergrund, keine Schriftzeichen. Lage, '
    'Abmessungen und Farben ergeben sich aus dem Bild.')


def main():
    catalog = ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
    entry = next(e for e in ET.parse(catalog).iter('entry') if e.get('key') == 'GE9032')
    original = entry.findtext('beschreibung')
    names = sorted(e.text for e in entry.findall('./bilder/bild'))
    names.remove('GE9032_6M.jpg')
    names.insert(0, 'GE9032_6M.jpg')
    manifest = dict(description=DESCRIPTION, direction='right', baseline_description=original,
        provenance=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
            seed=0, execution_mode='semantic-only',
            baseline_mode='fresh original-description CLI frozen before runtime changes',
            toolchain='repository virtualenv: NumPy, OpenCV, PyMuPDF'), cases=[])
    inventory = dict(original_description=original, images=[])
    for index, name in enumerate(names):
        image = ROOT/'artifacts/images_to_convert'/name
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        height, width = cv2.imread(str(image)).shape[:2]
        inventory['images'].append(dict(source=name, sha256=digest, width=width, height=height))
        manifest['cases'].append(dict(case_id=f'anonymous_right_junction_{index:02}', source=name,
            image='../../images_to_convert/'+name, source_sha256=digest,
            role='target' if index == 0 else 'color/size holdout', description=DESCRIPTION,
            before_svg=f'before/anonymous_right_junction_{index:02}.svg',
            after_svg=f'after/anonymous_right_junction_{index:02}.svg'))
    for name, data in [('manifest.json', manifest), ('source_inventory.json', inventory)]:
        target = FOLDER/name
        if target.exists():
            raise ValueError(f'Already frozen: {target}')
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
