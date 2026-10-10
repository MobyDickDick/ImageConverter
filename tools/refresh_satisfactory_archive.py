"""Collect proven satisfactory raster/SVG pairs in a browsable regression archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl

from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.review_conversion_quality import DEFAULT_THRESHOLD, IMAGE_DIRS, SVG_DIRS, _first_existing

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path('artifacts/satisfactory_conversions')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidates(root: Path):
    """Use explicit acceptance decisions; technical completion alone is insufficient."""
    catalog=root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
    descriptions=loadDescriptionMappingImpl(str(catalog),get_base_name_from_file_fn=getBaseNameFromFileImpl) if catalog.exists() else {}
    for manifest_path in sorted((root/'artifacts/evaluation').glob('*/manifest.json')):
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for report_path in sorted(manifest_path.parent.glob('*.json')):
            report = json.loads(report_path.read_text(encoding='utf-8'))
            if not isinstance(report, dict):
                continue
            gate = report.get('satisfaction_gate', {})
            accepted = {c['case_id'] for c in gate.get('cases', []) if c.get('satisfactory') is True}
            if not accepted:
                continue
            evidence = {c['case_id']:c for c in report.get('evidence', [])}
            for case in manifest.get('cases', []):
                if case['case_id'] not in accepted or not case.get('image'):
                    continue
                image = (manifest_path.parent/case['image']).resolve()
                variant = Path(case.get('source') or case.get('catalog_variant') or case.get('variant') or case['image']).stem
                # Only catalog inputs belong to this overview. Synthetic
                # calibration/stress cases retain their own evidence folders.
                catalog_image = _first_existing(root, IMAGE_DIRS, variant+'.jpg')
                if catalog_image is None or not image.exists() or digest(image) != digest(catalog_image):
                    continue
                expected_image=case.get('source_sha256') or evidence.get(case['case_id'],{}).get('input_sha256')
                if expected_image and digest(image)!=expected_image:
                    raise ValueError(f'Accepted source hash mismatch: {image}')
                svg_name = case.get('after_svg') or evidence.get(case['case_id'],{}).get('after_svg')
                svg = manifest_path.parent/svg_name if svg_name else None
                if svg is None or not svg.exists():
                    continue
                expected = evidence.get(case['case_id'],{}).get('after_svg_sha256')
                if expected and digest(svg) != expected:
                    # Git line-ending normalization may change bytes without
                    # changing the accepted XML. A mismatch otherwise fails.
                    normalized = hashlib.sha256(svg.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                    if normalized != expected:
                        raise ValueError(f'Accepted SVG hash mismatch: {svg}')
                description=case.get('description') or manifest.get('description')
                if not description:
                    continue
                yield variant, catalog_image, svg, 'semantic-only', report_path, description
    marked = root/'successed_conversions.txt'
    if marked.exists():
        for variant in marked.read_text(encoding='utf-8').splitlines():
            variant = variant.strip()
            if not variant or variant.startswith('#'):
                continue
            image = _first_existing(root,IMAGE_DIRS,variant+'.jpg')
            svg = _first_existing(root,SVG_DIRS,variant+'.svg')
            description=descriptions.get(variant) or descriptions.get(getBaseNameFromFileImpl(variant))
            if image is not None and svg is not None and description:
                yield variant,image,svg,'standard',marked,description
    # Subsequent ordinary batches already mark accepted sources by placing
    # them in this folder. Re-measure the pair before admitting it to the
    # overview, even when it has no separate development-package report.
    accepted_dir=root/'artifacts/images_to_convert/succesessfulConvertedImages'
    if accepted_dir.exists():
        for image in sorted(accepted_dir.iterdir()):
            if image.suffix.lower() not in {'.jpg','.jpeg','.png','.bmp','.gif','.tif','.tiff','.webp'}:
                continue
            variant=image.stem
            svg=_first_existing(root,SVG_DIRS,variant.upper()+'.svg')
            description=descriptions.get(variant) or descriptions.get(variant.upper()) or descriptions.get(getBaseNameFromFileImpl(variant))
            if svg is not None and description:
                yield variant,image,svg,'standard',accepted_dir,description


def refresh(root: Path = ROOT, output: Path | None = None) -> dict:
    output = output or root/ARCHIVE
    chosen = {}
    for variant,image,svg,mode,evidence,description in candidates(root):
        measured = measure(image,svg)
        mse = measured['metrics']['error_per_pixel']
        if not math.isfinite(mse) or mse > DEFAULT_THRESHOLD or '<image' in measured['svg'].lower():
            continue
        old = chosen.get(variant)
        if old and old['mean_delta2'] <= measured['mean_delta2']:
            continue
        chosen[variant] = dict(variant=variant,source=image,svg_source=svg,execution_mode=mode,
            evidence=evidence.relative_to(root).as_posix(),mean_delta2=measured['mean_delta2'],
            metrics={k:v for k,v in measured['metrics'].items() if k!='semantic_score'},description=description)
    for directory in ('images','svgs'):
        (output/directory).mkdir(parents=True,exist_ok=True)
    records=[]
    for variant,row in sorted(chosen.items()):
        image,svg=row.pop('source'),row.pop('svg_source')
        image_target=output/'images'/image.name
        svg_target=output/'svgs'/(variant+'.svg')
        shutil.copyfile(image,image_target)
        shutil.copyfile(svg,svg_target)
        records.append({**row,'image':image_target.relative_to(output).as_posix(),
            'svg':svg_target.relative_to(output).as_posix(),'image_sha256':digest(image_target),
            'svg_sha256':digest(svg_target)})
    report={'schema_version':'satisfactory_archive_v1','case_count':len(records),'cases':records}
    (output/'index.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    table=ET.Element('root')
    for case in records:
        entry=ET.SubElement(table,'entry',kind='wurzelform',key=case['variant'])
        ET.SubElement(entry,'beschreibung').text=case['description']
        ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=Path(case['image']).name
    ET.ElementTree(table).write(output/'descriptions.xml',encoding='utf-8',xml_declaration=True)
    lines=['# Zufriedenstellende Konvertierungen','',
           f'{len(records)} geprüfte Bild-/SVG-Paare. Originalbilder liegen in `images/`, Vektoren in `svgs/`.',
           '','Die erweiterten Tests konvertieren alle Einträge aus `index.json` erneut aus Bild und Beschreibung.',
           '','| Bild | SVG | Mean-Delta² | Prüfung |','|---|---|---:|---|']
    lines.extend(f"| [{r['variant']}]({r['image']}) | [SVG]({r['svg']}) | {r['mean_delta2']:.6f} | {r['execution_mode']} |" for r in records)
    (output/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return report


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/ARCHIVE)
    args=parser.parse_args()
    print(f"Archived satisfactory pairs: {refresh(output=args.output_dir)['case_count']}")
    return 0


if __name__=='__main__':
    raise SystemExit(main())
