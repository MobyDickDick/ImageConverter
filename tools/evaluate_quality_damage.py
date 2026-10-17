"""Controlled SVG damage experiment; measures gates, never runs a converter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tools.evaluate_primitive_scene import check_objects
from tools.run_plan_b_variations import measure_quality, render, sha256


def evaluate(folder):
    folder.mkdir(parents=True,exist_ok=False)
    prefix = '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160">'
    bg = '<rect width="240" height="160" fill="white"/>'
    rectangle = '<rect x="20" y="25" width="120" height="105" fill="none" stroke="#333333" stroke-width="4"/>'

    def circle(radius, dx=0):
        return f'<circle cx="{190+dx}" cy="78" r="{radius}" fill="none" stroke="#333333" stroke-width="2"/>'

    rows = []
    for kind,parameter in [('delete_circle',r) for r in (2,3,4,5,6,8,10,12,14,16,18,20,24)] + [('move_circle',dx) for dx in (1,2,3,4,6,10,20)]:
        radius = parameter if kind == 'delete_circle' else 5
        reference = prefix+bg+rectangle+circle(radius)+'</svg>'
        output = prefix+bg+rectangle+('' if kind == 'delete_circle' else circle(radius,parameter))+'</svg>'
        case_id = f'{kind}_{parameter:02d}'
        (folder/(case_id+'_reference.svg')).write_text(reference,encoding='utf-8')
        (folder/(case_id+'_damaged.svg')).write_text(output,encoding='utf-8')
        a,b = render(reference,240,160),render(output,240,160)
        expected = [dict(bbox=[18,23,124,109]),dict(bbox=[189-radius,77-radius,2*radius+2,2*radius+2])]
        measured = measure_quality(a,output)
        ref_mask = np.max(255-a.astype(float),axis=2)>25
        out_mask = np.max(255-b.astype(float),axis=2)>25
        lost = float(np.count_nonzero(ref_mask & ~out_mask)/np.count_nonzero(ref_mask))
        # Independently apply the existing gate to a padded object ROI. The
        # displaced candidate must remain inside it, so include the union.
        left,top = 185-radius,73-radius
        right,bottom = 195+radius+(parameter if kind == 'move_circle' else 0),83+radius
        cropped = f'<svg xmlns="http://www.w3.org/2000/svg" width="{right-left}" height="{bottom-top}" viewBox="{left} {top} {right-left} {bottom-top}">'+bg+rectangle+('' if kind == 'delete_circle' else circle(radius,parameter))+'</svg>'
        local = measure_quality(a[top:bottom,left:right],cropped)
        rows.append(dict(case_id=case_id,damage=kind,parameter_px=parameter,metrics=measured['metrics'],
                         pixel_gate_passed=measured['satisfactory'],failures=measured['failures'],
                         object_check=check_objects(b,expected),reference_foreground_lost_fraction=lost,
                         local_gate_passed=local['satisfactory'],local_metrics=local['metrics'],
                         reference_sha256=sha256(reference.encode()),damaged_sha256=sha256(output.encode())))
    missed = [r for r in rows if r['damage']=='delete_circle' and r['pixel_gate_passed']]
    report = dict(evidence_kind='controlled_damage_not_converter_output',executes_converter=False,
                  case_count=len(rows),cases=rows,
                  deletions_passing_pixel_gate=len(missed),deletions_tested=13,
                  largest_deleted_radius_passing_px=max(r['parameter_px'] for r in missed),
                  max_foreground_loss_passing=max(r['reference_foreground_lost_fraction'] for r in missed),
                  local_gate_detects_every_deletion=all(not r['local_gate_passed'] for r in rows if r['damage']=='delete_circle'),
                  limitation='A fixed analytic layout and 20 deliberately modified SVGs; no catalog false-positive rate can be inferred.')
    (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    report=evaluate(parser.parse_args().output)
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
