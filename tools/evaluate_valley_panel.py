"""Unrelated chevrons and catalog JPEGs through the real reference-blocked CLI."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2

from tools.run_plan_b_variations import run_case, write_cases

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Rechteckiges Feld mit dünnem grauem Rahmen und vertikalem grünem Farbverlauf. '
               'Eine weiße offene V-Linie besteht aus zwei geraden Schenkeln, die sich unten in einer Spitze treffen.')


def independent_cases():
    for width,height in ((100,60),(150,90)):
        for index,(paint,color,light) in enumerate((('grünem','#357947','#9ed0ad'),
                                  ('blauem','#285ba0','#8ca8ce'),
                                  ('rotem','#b94030','#d58c82'))):
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 100 60">'
                   '<defs><linearGradient id="unrelated_paint" x1="0" y1="0" x2="0" y2="1">'
                   f'<stop offset="0" stop-color="{color}"/><stop offset=".4" stop-color="{light}"/>'
                   f'<stop offset="1" stop-color="{color}"/></linearGradient></defs>'
                   '<rect x="8" y="6" width="84" height="48" fill="url(#unrelated_paint)" stroke="#999999" stroke-width="1.2"/>'
                   '<polyline points="8,28 47,51 92,28" fill="none" stroke="#ffffff" stroke-width="2.5"/></svg>')
            yield dict(case_id=f'foreign_{index}_{width}',svg=svg,
                       description=DESCRIPTION.replace('grünem',paint),width=width,height=height)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(argv)
    output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=False)
    cases=list(independent_cases())
    write_cases(cases,output)
    for size in ('L','M','S'):
        name=f'unrelated_jpeg_{size}'
        source=ROOT/f'artifacts/images_to_convert/AC0552_2_{size}.jpg'
        image=cv2.imread(str(source))
        folder=output/name/'input'
        folder.mkdir(parents=True)
        path=folder/f'{name}.png'
        assert cv2.imwrite(str(path),image)
        # Match the explicit image-to-description schema used by write_cases.
        doc=ET.Element('wurzelformen')
        entry=ET.SubElement(doc,'entry',key=name)
        ET.SubElement(entry,'beschreibung').text=DESCRIPTION
        ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=f'{name}.png'
        ET.ElementTree(doc).write(folder/'descriptions.xml',encoding='utf-8',xml_declaration=True)
        cases.append(dict(case_id=name,description=DESCRIPTION,width=image.shape[1],height=image.shape[0],
                          source_jpeg=source.relative_to(ROOT).as_posix(),
                          source_jpeg_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                          input_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    results=[]
    for case in cases:
        result=run_case(case,output,timeout=60,iterations=64)
        results.append(result)
        (output/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(case['case_id'],result['satisfactory'],flush=True)
    return 0 if all(r['satisfactory'] for r in results) else 1


if __name__=='__main__':
    raise SystemExit(main())
