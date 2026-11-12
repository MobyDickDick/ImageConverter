"""Inspect saved Plan-B results without changing converter code or acceptance."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
from PIL import Image, ImageDraw
from tools.plan_b_workbench import provenance
from src.iCCModules.imageCompositeConverterFramedPanel import panel_contract

folder = Path(__file__).resolve().parent
report = json.loads((folder / 'report.json').read_text(encoding='utf-8'))
assert report['status'] == 'completed' and len(report['cases']) == 17
rows = []
sheet = Image.new('RGB', (1120, 17 * 146 + 50), 'white')
draw = ImageDraw.Draw(sheet)
draw.text((10, 8), 'Case / original raster / reconstructed SVG / absolute difference (x4)', fill='black')
for index, case in enumerate(report['cases']):
    name = case['case_id']
    target = cv2.imread(str(folder / name / 'input' / (name + '.png')))
    output = cv2.imread(str(folder / name / 'output.png'))
    if output is None:
        rows.append(dict(case_id=name, failures=case['failures']))
        continue
    h, w = target.shape[:2]
    # The middle strip excludes the side contours; report photometric error
    # separately from the unchanged global acceptance decision.
    a = np.median(target[:, w//3:2*w//3], axis=1).mean(axis=1)
    b = np.median(output[:, w//3:2*w//3], axis=1).mean(axis=1)
    core = slice(2, h-2)
    row = dict(case_id=name, satisfactory=case['satisfactory'],
               failures=case['failures'], metrics=case.get('metrics'),
               central_profile_error_p95=float(np.percentile(abs(a[core]-b[core]), 95)),
               source_highlight_row=int(np.argmax(a[core]))+2,
               output_highlight_row=int(np.argmax(b[core]))+2,
               highlight_error=float(abs(a[core].max()-b[core].max())),
               blocked_svg_reads=case.get('blocked_svg_reads', []))
    rows.append(row)
    top = 42 + index*146
    draw.text((10, top), f"{name} {'PASS' if case['satisfactory'] else 'FAIL'}", fill='black')
    for column, image in enumerate([target, output, np.minimum(cv2.absdiff(target, output).astype(int)*4, 255).astype('uint8')]):
        tile = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).resize((300, 120))
        sheet.paste(tile, (160 + 315*column, top))
sheet.save(folder / 'overview.png')
audit = dict(seed=report['seed'], summary=report['summary'],
             git_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
             provenance_after_run=provenance(),
             converter_changes_during_run='Only the independent upload validator and its tests were changed; conversion and rendering code were unchanged.',
             precise_panel_contract_accepts_description=panel_contract(report['source_description']) is not None,
             cases=rows)
(folder / 'analysis.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(summary=report['summary'], failed=[r['case_id'] for r in rows if not r.get('satisfactory')]), indent=2))
