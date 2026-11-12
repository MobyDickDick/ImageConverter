"""Independent grey panels: unrelated sizes, paints, axes and clipped sides."""
from pathlib import Path
import sys
import json
import shutil
import subprocess
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')
import cv2
import numpy as np
from tools import run_plan_b_variations as battery
from tools.plan_b_workbench import provenance
from src.iCCModules.imageCompositeConverterFramedPanel import profile_quality, fit_framed_panel

folder = Path(sys.argv[sys.argv.index('--output-dir')+1]) if '--output-dir' in sys.argv else ROOT/'artifacts/evaluation/framed_panel_recheck_v2/independent_cli'
folder.mkdir(parents=True, exist_ok=False)
rows = []
software = provenance()
for index, (w, h, axis, x, y, pw, ph, stroke) in enumerate([
    (92, 46, 1, -1.2, 2.1, 89.4, 45.2, 1.4),
    (108, 54, 1, 2.8, -1.3, 108.2, 53.1, 1.8),
    (46, 92, 0, 2.1, -1.2, 45.2, 89.4, 1.4),
    (54, 108, 0, -1.3, 2.8, 53.1, 108.2, 1.8),
    (84, 42, 1, 3.4, 2.6, 76.1, 36.2, 1.2),
    (42, 84, 0, 2.6, 3.4, 36.2, 76.1, 1.2),
]):
    name = f'holdout_{index:02d}'
    start, end = (y, y+ph) if axis else (x, x+pw)
    coords = f'x1="0" x2="0" y1="{start}" y2="{end}"' if axis else f'y1="0" y2="0" x1="{start}" x2="{end}"'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
           f'<defs><linearGradient id="novelPaint" gradientUnits="userSpaceOnUse" {coords}>'
           '<stop offset="0" stop-color="#a7a7a7"/><stop offset=".26" stop-color="#ededed"/>'
           '<stop offset=".41" stop-color="#f1f1f1"/><stop offset="1" stop-color="#b3b3b3"/>'
           f'</linearGradient></defs><rect x="{x}" y="{y}" width="{pw}" height="{ph}" '
           f'fill="url(#novelPaint)" stroke="#858585" stroke-width="{stroke}"/></svg>')
    description = (f'Ein {"liegendes" if w>h else "stehendes"} Rechteck mit grauer Umrandung. '
                   f'Es gibt einen {"vertikalen" if axis else "horizontalen"} Graustufenübergang. '
                   'Das hellste Band liegt im Inneren, das dunkelste Grau ist heller als der Rand.')
    case = dict(case_id=name, width=w, height=h, svg=svg, description=description, variation={})
    battery.write_cases([case], folder)
    if '--direct' in sys.argv:
        target = cv2.imread(str(folder/name/'input'/(name+'.png')))
        fitted = fit_framed_panel(w, h, description=description, image=target, render_fn=battery.render,
            error_fn=lambda a,b: float(np.mean((a.astype(float)-b)**2)))
        row = dict(case_id=name, fitted=fitted is not None)
        if fitted:
            row['quality'] = battery.measure_quality(target, fitted['svg'])
    else:
        result = battery.run_case(case, folder, iterations=64, timeout=60, keep_debug_artifacts=True,
                                 extra_cli_args=('--search-seed', '816327'))
        row = dict(case_id=name, after=result)
        if result.get('output_svg'):
            svg_path = folder/result['output_svg']
            native = folder/name/'native.png'
            subprocess.run([shutil.which('rsvg-convert'), '-w', str(w), '-h', str(h), '-b', 'white',
                            '-o', str(native), str(svg_path)], check=True, timeout=15)
            target = cv2.imread(str(folder/name/'input'/(name+'.png')))
            rendered = cv2.imread(str(native))
            row['independent_quality'] = battery.measure_quality(target, svg_path.read_text(encoding='utf-8'), render_fn=lambda *args: rendered)
            yy,xx = np.nonzero(target.min(axis=2)<235)
            bounds = (int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1)
            row['independent_profile'] = profile_quality(target,rendered,axis,bounds)
    rows.append(row)
    (folder/'summary.json').write_text(json.dumps(dict(provenance=software,cases=rows),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(case_id=name, after=row.get('after',{}).get('satisfactory'),
                          independent=row.get('independent_quality',{}).get('satisfactory'),
                          profile=row.get('independent_profile'))),flush=True)
