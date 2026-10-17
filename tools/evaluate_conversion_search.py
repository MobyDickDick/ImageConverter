"""Run real guarded CLI conversions on frozen raster/description pairs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

import cv2

from tools.run_plan_b_variations import run_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, action='append', required=True)
    parser.add_argument('--description-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--portfolio', action='store_true')
    parser.add_argument('--seed', type=int, default=20261017)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    description = args.description_file.read_text(encoding='utf-8').strip()
    os.environ['IMAGE_CONVERTER_ISOLATE_SVG_RENDER'] = '0'
    os.environ['ICC_SEARCH_MODE'] = 'portfolio' if args.portfolio else 'legacy'
    os.environ['ICC_SEARCH_SEED'] = str(args.seed)
    report = dict(evidence_kind='real_cli', portfolio=args.portfolio, seed=args.seed,
                  commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('src').rglob('*.py')},
                  description=description, cases=[])
    for index, source in enumerate(args.image):
        name = f'probe_{index:02d}'
        inputs = args.output/name/'input'
        inputs.mkdir(parents=True)
        image = cv2.imread(str(source))
        if image is None:
            raise ValueError(f'Unreadable image: {source}')
        cv2.imwrite(str(inputs/(name+'.png')), image)
        root = ET.Element('root')
        entry = ET.SubElement(root, 'entry', kind='wurzelform', key=name)
        ET.SubElement(entry, 'beschreibung').text = description
        ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = name+'.png'
        ET.ElementTree(root).write(inputs/'descriptions.xml', encoding='utf-8', xml_declaration=True)
        case = dict(case_id=name, width=image.shape[1], height=image.shape[0],
                    description=description, source=str(source),
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        result = run_case(case, args.output, timeout=120, iterations=64)
        report['cases'].append(result)
        (args.output/'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        print(name, result['satisfactory'], result.get('metrics'), flush=True)
    return 0 if all(c['satisfactory'] for c in report['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
