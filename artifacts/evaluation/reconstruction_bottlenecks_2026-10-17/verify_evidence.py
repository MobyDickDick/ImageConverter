"""Re-render the saved diagnostic outputs; verify replay and baseline provenance."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import cv2
from tools.run_plan_b_variations import measure_quality,render


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder=Path(__file__).resolve().parent/'evidence'
    report=json.loads((folder/'report.json').read_text(encoding='utf-8'))
    replay=json.loads((folder/'replay_identity.json').read_text(encoding='utf-8'))
    assert len(report['cases'])==6
    assert not report['production_fusion_calls']
    assert all(sum(c['output_kinds'].values())==1 and c['input_candidates']==2 for c in report['oracle_merge_probes'])
    for path,expected in report['source_sha256'].items():
        original=subprocess.check_output(['git','show',report['commit']+':'+path],cwd=ROOT)
        assert hashlib.sha256(original).hexdigest()==expected,path
    for case in report['cases']:
        name=case['case_id']
        source=folder/case['reference_svg'];output=folder/case['output_svg']
        assert digest(source)==case['reference_svg_sha256']
        assert digest(output)==case['output_sha256']
        assert digest(folder/name/'input'/(name+'.png'))==case['input_sha256']
        image=render(source.read_text(encoding='utf-8'),case['width'],case['height'])
        measured=measure_quality(image,output.read_text(encoding='utf-8'))
        for key in ['metrics','satisfactory','failures','complexity']:
            assert measured[key]==case[key],(name,key)
        assert not case['blocked_svg_reads'] and case['returncode']==0
        for key in ['input_sha256','output_sha256','metrics','satisfactory','failures']:
            assert replay[name][key]==case[key],(name,key)
        actual=[]
        for log in (folder/name/'conversion').rglob('*validation*.log'):
            actual.extend(line for line in log.read_text(encoding='utf-8',errors='replace').splitlines()
                          if line.startswith(('status=','selection_reason=')))
        assert actual==case['validation_status']
    by_name={c['case_id']:c for c in report['cases']}
    assert by_name['junction_control']['input_sha256']==by_name['junction_paraphrase']['input_sha256']
    assert by_name['junction_control']['satisfactory'] and not by_name['junction_paraphrase']['satisfactory']
    assert by_name['one_circle']['output_sha256']==by_name['two_circles']['output_sha256']
    assert by_name['two_rectangles']['detected_kinds']['rectangle']==2
    assert by_name['two_rectangles']['seeded_ir_kinds']['RectBorder']==1
    for name in ['contract_ablation.json','contract_acceptance.json']:
        fixture=json.loads((folder/name).read_text(encoding='utf-8'))
        assert fixture['evidence_kind']=='contract_fixture'
        assert fixture['executes_converter'] is False and fixture['measures_raster_quality'] is False
    print('Six real CLI outputs, two-run identity, provenance and explicit fixture labels verified')


if __name__=='__main__':
    main()
