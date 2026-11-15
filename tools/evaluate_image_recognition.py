"""Reproduce a bounded retrieval check; this is not an unseen-family benchmark.

Run: python -m tools.evaluate_image_recognition --output artifacts/evaluation/image_recognition_v1
Only eligible, non-reserved measured pairs are opened. Reference SVGs supply
structure/provenance, never conversion geometry or a quality exemption.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

from PIL import Image

from src.imageConverterRecognition import ImageRecognition, rgb_image
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl


def evaluate(root, limit=24):
    recognizer = ImageRecognition(root)
    started = time.perf_counter()
    recognizer.refresh()
    cold = time.perf_counter()-started
    references = recognizer.references.copy()
    selected, families = [], set()
    # Choose whole families deterministically; don't inflate the count with sizes.
    for ref in sorted(references, key=lambda ref: hashlib.sha256(ref['filename'].encode()).hexdigest()):
        family = getBaseNameFromFileImpl(ref['filename'])
        if family in families:
            continue
        selected.append(ref)
        families.add(family)
        if len(selected) >= limit:
            break
    cases = []
    for ref in selected:
        image = rgb_image(Path(root)/ref['image'])
        for kind, query in (
            ('decoded_identity', image),
            ('resized_125_percent', image.resize((max(18, round(image.width*1.25)), max(18, round(image.height*1.25))), Image.Resampling.LANCZOS)),
        ):
            before = time.perf_counter()
            result = recognizer.recognize(query)
            expected = getBaseNameFromFileImpl(ref['filename'])
            matches = [getBaseNameFromFileImpl(match['filename']) for match in result['matches']]
            automatic = result['automatic']
            cases.append(dict(filename=ref['filename'], image_sha256=ref['image_sha256'],
                svg_sha256=ref['svg_sha256'], kind=kind, top3_family_hit=expected in matches,
                automatic_kind=automatic['kind'] if automatic else None,
                automatic_description_matches_reference=automatic['description'] == ref['description'] if automatic else None,
                matched_files=[match['filename'] for match in result['matches']],
                seconds=round(time.perf_counter()-before, 4)))
    return dict(schema='image_recognition_evaluation_v1', reference_count=len(references), skipped=dict(recognizer.skipped),
        cold_index_seconds=round(cold, 4), families=len(families), cases=cases,
        results={kind: dict(cases=len(group), top3_family_hits=sum(case['top3_family_hit'] for case in group),
                           automatic_kinds=dict(Counter(case['automatic_kind'] or 'abstain' for case in group)))
                 for kind in ('decoded_identity', 'resized_125_percent')
                 for group in [[case for case in cases if case['kind'] == kind]]},
        limitation='Known-reference retrieval and resizing only. No claim of recognition accuracy on unseen families, OCR, or conversion success.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=24)
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        parser.error('--limit must be between 1 and 200')
    result = evaluate(Path(__file__).resolve().parents[1], args.limit)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'cases'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
