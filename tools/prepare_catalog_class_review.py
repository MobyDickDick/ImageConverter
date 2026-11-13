"""Prepare numbered source-only contact sheets for a complete visual class audit.

No proposals, descriptions or saved vectors appear beside the source images.
Sealed families are excluded before decoding. Every sheet has a frozen manifest
of exact input bytes so a recorded review can be replayed and invalidated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def reserved_names(root):
    """Apply current seals before any source decoding or review application."""
    reserved = set()
    for path in (root/'config').glob('real_composition_holdout*.json'):
        policy = json.loads(path.read_text(encoding='utf-8'))
        if policy.get('evaluation_policy', {}).get('status') == 'sealed_unrun':
            for case in policy.get('cases', []):
                reserved.update(name.casefold() for name in [case['file'], *case.get('family_members', [])])
    return reserved


def prepare(root, manifest_path, output, *, columns=10, page_size=120, replay=None):
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    reserved = reserved_names(root)
    rows = [r for r in payload['rows'] if r.get('role') == 'catalog'
            and r['filename'].casefold() not in reserved
            and r['classification']['basis'] != 'visual_audit']
    frozen = json.loads(replay.read_text(encoding='utf-8')) if replay else None
    if frozen:
        rows = [r for page in frozen['pages'] for r in page['rows']]
        if any(r['filename'].casefold() in reserved for r in rows):
            raise ValueError('Replay contains a currently reserved source')
    output.mkdir(parents=True, exist_ok=False)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 13)
    except OSError:
        font = ImageFont.load_default()
    pages = []
    for page in range((len(rows)+page_size-1)//page_size):
        members = rows[page*page_size:(page+1)*page_size]
        sheet = Image.new('RGB', (columns*160, ((len(members)+columns-1)//columns)*132), '#e5e8eb')
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(members):
            path = (root/row['image']).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError('Source leaves repository')
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != row['image_sha256']:
                raise ValueError('Source changed: '+row['filename'])
            image = ImageOps.contain(Image.open(path).convert('RGB'), (148, 99))
            x, y = index%columns*160, index//columns*132
            draw.rectangle((x+2,y+2,x+157,y+129), fill='white')
            sheet.paste(image, (x+(160-image.width)//2,y+3+(99-image.height)//2))
            draw.text((x+5,y+104), f'{index:03} '+row['filename'], font=font, fill='black')
        name = f'page_{page:02}.png'
        sheet.save(output/name)
        pages.append(dict(sheet=name, sheet_sha256=hashlib.sha256((output/name).read_bytes()).hexdigest(),
                          rows=[dict(index=i, filename=r['filename'], image=r['image'],
                                     image_sha256=r['image_sha256'], description=r['description'])
                                for i,r in enumerate(members)]))
    result = dict(schema='catalog_visual_class_review_sheets_v1', count=len(rows),
                  excluded_reserved=sorted(reserved), columns=columns, page_size=page_size, pages=pages)
    (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} images on {len(pages)} sheets: {output}')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.tmp/catalog-full-visual-review')
    parser.add_argument('--replay-manifest',type=Path)
    args=parser.parse_args()
    prepare(ROOT,ROOT/'artifacts/catalog_classes/manifest.json',args.output,replay=args.replay_manifest)
