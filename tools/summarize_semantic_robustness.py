"""Recheck the full paired wording experiment before publishing compact evidence."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
from xml.etree import ElementTree as ET
import zipfile

from tools import evaluate_semantic_robustness as evaluation
from tools.prepare_practical_benchmark import ROOT, digest, write_json
from tools.run_anytime_benchmark import archive_snapshot


def deletion_controls(work: Path) -> list[dict]:
    import cv2
    prepared=work/'frozen-dev'
    output=work/('replayed-after-dev' if (work/'replayed-after-dev/report.json').exists() else 'accepted-after-dev')
    manifest=evaluation.verify_inputs(prepared)
    report=json.loads((output/'report.json').read_text(encoding='utf-8'))
    controls=[]
    for family,indices in [('flame_disk',[5,6]),('house_disk',[5,6,7]),
                           ('warning_disk',[5]),('labeled_disk',[])]:
        row=next(r for r in report['records'] if r['family']==family and r['case_id'].endswith('p0'))
        case=next(c for c in manifest['cases'] if c['case_id']==row['case_id'])
        path=output/row['raw']['output_svg']
        root=ET.fromstring(path.read_text(encoding='utf-8'))
        if family=='labeled_disk':
            for parent in root.iter():
                for child in list(parent):
                    if child.tag.rsplit('}',1)[-1]=='text':
                        parent.remove(child)
        else:
            for index in sorted(indices,reverse=True):
                root.remove(list(root)[index])
        check=evaluation.check_output(case,cv2.imread(str(prepared/case['image'])),
            ET.tostring(root,encoding='unicode'),manifest['region_limits'])
        failed_regions=[r['name'] for r in check['regions'] if not r['passed']]
        if check['passed'] or not failed_regions:
            raise ValueError('Deleted detail escaped independent check: '+family)
        controls.append(dict(family=family,original_svg_sha256=digest(path),
                             rejected=True,failed_regions=failed_regions))
    return controls


def summarize(work: Path) -> dict:
    archive_bytes=subprocess.check_output(['git','archive','--format=zip','7ed646e5f','src','config'],cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        baseline={i.filename:hashlib.sha256(archive.read(i)).hexdigest() for i in archive.infolist()
                  if not i.is_dir() and '__pycache__' not in i.filename and not i.filename.endswith('.pyc')}
    current=evaluation.source_hashes()
    groups={}
    proofs={}
    replayed=(work/'replayed-after-dev/report.json').exists()
    for split,inputs,count in [('dev','frozen-dev',80),('holdout','final-inputs',50)]:
        for mode in ('before','after'):
            name=f'final-before-{split}' if mode=='before' else f'accepted-after-{split}'
            if mode=='after' and split=='dev' and replayed:
                name='replayed-after-dev'
            output=work/name
            checked=evaluation.verify(work/inputs,output)
            report=json.loads((output/'report.json').read_text(encoding='utf-8'))
            if report['runtime_sha256'] != (baseline if mode=='before' else current):
                raise ValueError('Runtime provenance differs: '+name)
            if checked['attempts'] != count or report['budget_seconds'] != 10.:
                raise ValueError('Incomplete final paired study')
            if mode=='after' and checked['accepted_families'] != 10:
                raise ValueError('Current runtime has unresolved wording failures')
            groups[name]=checked
            proofs[name]=dict(report_sha256=digest(output/'report.json'),
                              freeze_sha256=digest(work/inputs/'freeze.json'))
    repetitions=[]
    if replayed:
        path=work/'accepted-after-dev'
        checked=evaluation.verify(work/'frozen-dev',path)
        report=json.loads((path/'report.json').read_text(encoding='utf-8'))
        if report['runtime_sha256']!=current or checked['attempts']!=80 or report['budget_seconds']!=10.:
            raise ValueError('Earlier repetition has different runtime or protocol')
        failed=[]
        for row in report['records']:
            if row['passed']:
                continue
            control=json.loads((path/row['case_id']/'conversion/reports'/
                               (row['case_id']+'_deadline.json')).read_text(encoding='utf-8'))
            failed.append(dict(case_id=row['case_id'],kind=row['kind'],control=control,
                no_evaluation_overrun=control.get('candidate_evaluations')==0 and control.get('elapsed_seconds',0)>40,
                cause_diagnosed=False))
        repetitions.append(dict(name='accepted-after-dev',summary=checked,failures=failed,
                                report_sha256=digest(path/'report.json')))
    after_groups=[s for name,s in groups.items() if not name.startswith('final-before')]
    after_groups += [r['summary'] for r in repetitions]
    after_totals={key:sum(s[key] for s in after_groups) for key in
                  ('attempts','positives','positive_passes','negatives','safe_rejections')}
    regression=ET.parse(work/'accepted-regressions.xml').getroot()
    suites=regression.findall('testsuite') if regression.tag=='testsuites' else [regression]
    tests={key:sum(int(s.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    if not tests['tests'] or tests['failures'] or tests['errors']:
        raise ValueError('Regression suite did not pass')
    boundary_root=ET.parse(work/'boundaries-latest.xml').getroot()
    boundary_suites=boundary_root.findall('testsuite') if boundary_root.tag=='testsuites' else [boundary_root]
    boundaries={key:sum(int(s.get(key,0)) for s in boundary_suites) for key in ('tests','failures','errors','skipped')}
    if boundaries['tests'] < 33 or boundaries['failures'] or boundaries['errors']:
        raise ValueError('Final boundary checks did not pass')
    distinct_tests=len({(t.get('classname'),t.get('name')) for document in (regression,boundary_root)
                        for t in document.iter('testcase')})
    archive=json.loads((work/'archive-recheck/report.json').read_text(encoding='utf-8'))
    if archive['case_count'] != 377 or archive['passed'] != 377:
        raise ValueError('Archive quality regression')
    snapshot=archive_snapshot()
    if snapshot != json.loads((work/'archive-before.json').read_text(encoding='utf-8')):
        raise ValueError('Stored archive changed')
    return dict(schema='semantic_robustness_evidence_v1', task='SEMANTIC-ROBUSTNESS-01',
        scope='Ten known real topologies; bounded German vocabulary; agent-authored annotations and wording, no independent human language audit.',
        family_count=10, cli_attempts=260+sum(r['summary']['attempts'] for r in repetitions),
        paired_endpoint_attempts=260, additional_repetitions=repetitions,
        all_final_runtime_attempts=after_totals,
        requested_iterations=64, search_seed=17,
        fixed_image_budget_seconds=10, groups=groups, proofs=proofs,
        deletion_controls=deletion_controls(work),
        regression_tests=tests, regression_xml_sha256=digest(work/'accepted-regressions.xml'),
        final_boundary_tests=boundaries, boundary_xml_sha256=digest(work/'boundaries-latest.xml'),
        distinct_test_ids=distinct_tests,
        archive=dict(cases=377,passed=377,unchanged=True,index_sha256=snapshot['index_sha256'],
                     reconversion_report_sha256=digest(work/'archive-recheck/report.json'),
                     higher_than_historical_best=len(archive.get('higher_mean_delta2',[]))),
        runtime_sha256=current, baseline_ref='7ed646e5f',
        toolchain=dict(python=platform.python_version(),platform=platform.platform()),
        full_evidence_required=True, remote_ci_started=False)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=ROOT/'.tmp/semantic01')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/evaluation/semantic_robustness_v1')
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    summary=summarize(args.work)
    path=args.output/'summary.json'
    if args.verify_only:
        if json.loads(path.read_text(encoding='utf-8')) != summary:
            raise ValueError('Compact summary differs from full evidence')
    else:
        args.output.mkdir(parents=True,exist_ok=True)
        if path.exists():
            raise FileExistsError('Never overwrite an existing study summary')
        write_json(path,summary)
    print(f"Verified {summary['cli_attempts']} CLI attempts, regression tests and 377 archived cases")
    return 0


if __name__=='__main__':
    raise SystemExit(main())
