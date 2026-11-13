"""Apply explicitly inspected contact-sheet assignments, with byte provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.imageConverterClasses import CLASSES, text_hash
from tools.prepare_catalog_class_review import reserved_names

ROOT = Path(__file__).resolve().parents[1]


def apply(root, sheets, decisions_path, *, complete=False):
    manifest = json.loads((sheets/'manifest.json').read_text(encoding='utf-8'))
    decisions = json.loads(decisions_path.read_text(encoding='utf-8'))
    target = root/'config/catalog_class_visual_review.json'
    review = json.loads(target.read_text(encoding='utf-8'))
    reserved = reserved_names(root)
    additions = {}
    for page_number, spans in decisions['pages'].items():
        page = manifest['pages'][int(page_number)]
        if hashlib.sha256((sheets/page['sheet']).read_bytes()).hexdigest() != page['sheet_sha256']:
            raise ValueError('Contact sheet changed')
        assigned = {}
        for start, end, class_id, subtype, observation in spans:
            if class_id not in CLASSES or class_id in {'reserved','unresolved'}:
                raise ValueError('Invalid final class')
            if not 0 <= start <= end < len(page['rows']):
                raise ValueError('Invalid span')
            for index in range(start, end+1):
                if index in assigned:
                    raise ValueError('Duplicate reviewed cell')
                row = page['rows'][index]
                if row['filename'].casefold() in reserved:
                    raise ValueError('Source is now reserved: '+row['filename'])
                path = (root/row['image']).resolve()
                if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != row['image_sha256']:
                    raise ValueError('Reviewed input changed: '+row['filename'])
                assigned[index] = dict(class_id=class_id, subclass_id=subtype, observation=observation,
                    independent_of_description=True,
                    image_sha256=row['image_sha256'], description_sha256=text_hash(row['description']),
                    review_evidence=dict(batch='full_catalog_2026-11-13', sheet=page['sheet'],
                        sheet_sha256=page['sheet_sha256'], cell=index))
                additions[row['filename'].casefold()] = assigned[index]
        if len(assigned) != len(page['rows']):
            raise ValueError('Incomplete reviewed sheet: '+page_number)
    if complete and (len(decisions['pages']) != len(manifest['pages']) or len(additions) != manifest['count']):
        raise ValueError('Full catalog review is incomplete')
    review['cases'].update(additions)
    review['schema'] = 'catalog_class_visual_review_v2'
    review['scope'] = ('Geometric assignments from individually inspected source contact-sheet cells; '
                       'no inference from descriptions, no propagation to unviewed size variants, '
                       'no human semantic approval or conversion claim.')
    review['full_catalog_review'] = dict(complete=complete, newly_inspected=len(additions),
        total_visual_assignments=len(review['cases']), sheet_manifest_sha256=hashlib.sha256((sheets/'manifest.json').read_bytes()).hexdigest(),
        decisions_sha256=hashlib.sha256(decisions_path.read_bytes()).hexdigest())
    target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(additions)} newly inspected inputs; {len(review["cases"])} total visual assignments')
    return review


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sheets',type=Path,default=ROOT/'.tmp/catalog-full-visual-review')
    parser.add_argument('--decisions',type=Path,default=ROOT/'config/catalog_class_review_decisions.json')
    parser.add_argument('--complete',action='store_true')
    args=parser.parse_args()
    apply(ROOT,args.sheets,args.decisions,complete=args.complete)
