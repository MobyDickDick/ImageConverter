"""Summarize immutable PNG replays, native-render checks and retained searches."""
from pathlib import Path
import json
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.plan_b_workbench import provenance
from tools.run_plan_b_variations import LIMITS

folder = Path(__file__).resolve().parent
software = provenance()
reports = {}
for name, count in [('accepted_cli', 17), ('initial_wording_cli', 17), ('accepted_independent_cli', 6)]:
    data = json.loads((folder/name/'summary.json').read_text(encoding='utf-8'))
    assert len(data['cases']) == count
    assert data['provenance']['python_sources_sha256'] == software['python_sources_sha256']
    cases = []
    for case in data['cases']:
        result = case['after']
        assert result['satisfactory'] and case['independent_quality']['satisfactory']
        assert case['independent_profile']['passed']
        assert result['limits'] == LIMITS and not result.get('blocked_svg_reads')
        svg_path = folder/name/result['output_svg']
        svg = ET.fromstring(svg_path.read_text(encoding='utf-8'))
        assert len(svg.findall('{*}rect')) == 1 and len(svg.findall('.//{*}stop')) == 4
        assert not svg.findall('.//{*}image')
        log = svg_path.parents[1]/'reports'/'conversion_result_map.json'
        saved = next(iter(json.loads(log.read_text(encoding='utf-8')).values()))
        fit = saved['params']['framed_panel_registration']
        cases.append(dict(case_id=case['case_id'], input_sha256=result['input_sha256'],
                          before=case.get('before'), after=result['metrics'],
                          independent=case['independent_quality']['metrics'],
                          profile=case['independent_profile'],
                          elapsed_seconds=result['elapsed_seconds'],
                          registration_renderings=fit['evaluations'],
                          output_sha256=result['output_sha256']))
    reports[name] = dict(passed=count, required=count,
        before_passed=sum(bool(c.get('before', {}).get('satisfactory')) for c in data['cases']) if name=='accepted_cli' else None,
        cli_process_seconds=sum(c['elapsed_seconds'] for c in cases),
        registration_renderings=sum(c['registration_renderings'] for c in cases),
        max_mse=max(c['after']['normalized_mse'] for c in cases),
        min_edge=min(c['after']['edge_alignment'] for c in cases),
        min_iou=min(c['after']['foreground_iou'] for c in cases),
        max_native_profile_error=max(c['profile']['profile_error_p95'] for c in cases),
        max_native_highlight_error=max(c['profile']['highlight_error'] for c in cases),
        cases=cases)
summary = dict(schema_version='framed_grey_panel_recheck_v2', provenance=software,
               limits=LIMITS, frozen_seed=64217, iterations=64, timeout_seconds=60,
               independent_seed=816327, embedded_rasters=0, blocked_svg_reads=0,
               fixed_cli_checks=reports,
               limitations=['The frozen PNGs, not a newly rendered source SVG, are the reconstruction target.',
                            'This validates the framed-grey-gradient family, not arbitrary scenes or the entire catalogue.'])
(folder/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:{field:value for field,value in v.items() if field!='cases'} for k,v in reports.items()},indent=2))
