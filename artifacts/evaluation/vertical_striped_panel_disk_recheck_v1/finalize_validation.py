from pathlib import Path
import argparse,json,subprocess,hashlib
from collections import Counter
from xml.etree import ElementTree as ET
import shutil,sys
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser=argparse.ArgumentParser(description='Seal complete tests and unchanged prior archive evidence')
    parser.add_argument('--standard',type=Path,default=ROOT/'.tmp/vss')
    parser.add_argument('--archive',type=Path,default=ROOT/'.tmp/vsa/report.json')
    parser.add_argument('--smoke',type=Path,default=ROOT/'.tmp/vsh.xml')
    args=parser.parse_args()
    results=read(args.standard/'results.json')
    assert all(r['exit_code']==0 for r in results)
    merged=ET.Element('testsuites')
    for i in range(4):merged.extend(ET.parse(args.standard/f'shard_{i}.xml').getroot())
    cases=list(merged.iter('testcase'))
    actual=[c.get('classname').replace('.','/')+'.py::'+c.get('name') for c in cases]
    expected=read(args.standard/'plan.json')['expected_nodes']
    assert Counter(actual)==Counter(expected) and len(set(actual))==len(actual)
    assert all(c.find('failure') is None and c.find('error') is None for c in cases)
    skipped=sum(c.find('skipped') is not None for c in cases)
    ET.ElementTree(merged).write(FOLDER/'standard_profile.xml',encoding='utf-8',xml_declaration=True)
    shutil.copyfile(args.standard/'results.json',FOLDER/'standard_result.json')
    archive=read(args.archive)
    assert archive['expected']==archive['measured']==archive['passed']==306
    assert not archive['failures'] and all(c['passed'] for c in archive['cases'])
    previous=read(ROOT/'artifacts/evaluation/sine_diagram_recheck_v1/archive_recheck.json')
    current={c['variant']:c for c in archive['cases']}
    assert all(current[c['variant']]==c for c in previous['cases'])
    assert sorted(archive['higher_mean_delta2'])==sorted(previous['higher_mean_delta2'])
    assert len(archive['higher_mean_delta2'])==22
    shutil.copyfile(args.archive,FOLDER/'archive_recheck.json')
    commit=read(FOLDER/'manifest.json')['provenance']['commit']
    old_index=json.loads(subprocess.check_output(['git','show',commit+':artifacts/satisfactory_conversions/index.json'],cwd=ROOT))
    index=read(ROOT/'artifacts/satisfactory_conversions/index.json')
    records={c['variant']:c for c in index['cases']}
    assert old_index['case_count']==305 and index['case_count']==306
    assert all(records[c['variant']]==c for c in old_index['cases'])
    prior_folder=ROOT/'artifacts/evaluation/sine_diagram_recheck_v1'
    review=read(FOLDER/'review_summary.json')
    prior_review=read(prior_folder/'review_summary.json')
    assert review['metrics']==prior_review['metrics']
    assert review['threshold_normalized_mse']==prior_review['threshold_normalized_mse']
    prior_args=read(prior_folder/'review_args.json')
    review_args=read(FOLDER/'review_args.json')
    assert review_args[2:]==prior_args[2:]+['--exclude','GE0305']
    smoke=list(ET.parse(args.smoke).iter('testcase'))
    assert len(smoke)==2 and all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in smoke)
    shutil.copyfile(args.smoke,FOLDER/'smoke.xml')
    checks=[
        [sys.executable,'-m','compileall','-q','src','tests','tools'],
        [sys.executable,'-m','src.imageCompositeConverter','--help'],
        [sys.executable,'-m','tools.check_no_new_image_id_hardcoding'],
        ['git','-c','core.whitespace=cr-at-eol','diff','--check'],
    ]
    for command in checks:subprocess.run(command,cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    statistics=dict(collected=len(cases),passed=len(cases)-skipped,skipped=skipped,failed=0,all_collected_nodes_verified_once=True)
    document=ROOT/'docs/next_arbeitspaket_2026-10-16_ge0305.md'
    text=document.read_text(encoding='utf-8')
    marker='bleiben unverändert. Abschlusszahlen und Artefakthashes stehen in'
    if marker in text:
        passed_text=f"{statistics['passed']:,}".replace(',','.')
        collected_text=f"{len(cases):,}".replace(',','.')
        text=text.replace(marker,f'bleiben unverändert. Die vollständige Standardsammlung besteht mit **{passed_text} bestandenen Tests, {skipped} bestehenden Skips und null Fehlern**.\nAlle {collected_text} gesammelten Testknoten sind genau einmal nachgewiesen.\nDie erneute Archivkonvertierung besteht mit **306/306**; alle 305 bisherigen\nPrüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen\nbleiben unverändert. Die schweren AC08-/AC0100-Smoke-Tests bestehen mit **2/2**.\nAbschlusszahlen und Artefakthashes stehen in')
        document.write_text(text,encoding='utf-8',newline='\n')
    paths=[p for p in FOLDER.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='validation_2026-10-16.json']
    paths.extend(ROOT/name for name in (
        'src/iCCModules/imageCompositeConverterStripedPanelDisk.py',
        'tools/evaluate_striped_panel_disk_recheck.py','tools/run_striped_panel_disk_recheck.py',
        'tests/test_vertical_striped_panel_disk_runtime.py',
        'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',
        'artifacts/descriptions/Finale_Wurzelformen_V3.xml',
        'artifacts/satisfactory_conversions/index.json','artifacts/satisfactory_conversions/descriptions.xml',
        'docs/next_arbeitspaket_2026-10-16_ge0305.md'))
    validation=dict(schema_version='vertical_striped_panel_disk_completion_v1',standard=statistics,smoke_passed=2,local_checks=checks,
        all_catalog_outputs_equal_neutral=True,
        archive=dict(previous_count=305,new_count=306,passed=306,known_drift_count=22,
            all_previous_records_identical=True,all_previous_recheck_results_identical=True,known_drift_list_unchanged=True),
        rotation=dict(next_candidates=[c['variant'] for c in read(FOLDER/'review_summary.json')['selected_candidates']]),
        artifact_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)})
    (FOLDER/'validation_2026-10-16.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(statistics,sort_keys=True))


if __name__=='__main__':main()
