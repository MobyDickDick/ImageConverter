"""Bounded proposal-only study on sealed synthetic curve inputs.

This measures the existing group generator after the independent oracle has
been frozen. It does not run a catalogue, change production, or grant release.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import time
from xml.etree import ElementTree as ET

from tools.check_curve_scene import check_scene
from tools.evaluate_curve_checker import EVIDENCE, ROOT, digest, verify, write_json


def probe(output, evidence=EVIDENCE):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
    from src.iCCModules.imageCompositeConverterFallbackGroups import group_proposals
    from tools.run_plan_b_variations import render

    manifest = verify(evidence)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for case in manifest['cases']:
        image = render(case['svg'], *case['annotation']['size'])
        session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
        proposals = []
        start = time.monotonic()
        with image_search(session):
            for svg, family in group_proposals(image, session):
                if session.time_reason() or len(proposals) >= 32:
                    break
                path = output/(case['case_id']+f'-{len(proposals):02d}.svg')
                path.write_text(svg, encoding='utf-8')
                proposals.append(dict(file=path.name, sha256=digest(path), family=family,
                    path_count=sum(n.tag.endswith('}path') for n in ET.fromstring(svg).iter()),
                    check=check_scene(svg, case['annotation'])))
        rows.append(dict(case_id=case['case_id'], proposals=proposals, elapsed_seconds=time.monotonic()-start,
                         stop_reason=session.time_reason(), model_confirmed=bool(session.validated)))
    sources = ['imageCompositeConverterFallbackGroups.py', 'imageCompositeConverterFallbackStructure.py',
               'imageCompositeConverterFallbackComposition.py', 'imageCompositeConverterAdaptiveSearch.py']
    report = dict(schema='curve_group_proposal_study_v1', cases=rows, seconds=5, max_proposals=32,
                  checker_seal_sha256=digest(evidence/'seal.json'), study_sha256=digest(Path(__file__)),
                  runtime_sha256={name:digest(ROOT/'src/iCCModules'/name) for name in sources},
                  converter_executions=0, real_reserves_executed=False, model_promotions=0)
    write_json(output/'summary.json', report)
    print(f"{len(rows)} synthetic inputs; {sum(len(r['proposals']) for r in rows)} group proposals; "
          f"{sum(p['check']['complete'] for r in rows for p in r['proposals'])} complete curve inventories")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    args = parser.parse_args()
    probe(args.output, args.evidence)


if __name__ == '__main__':
    main()
