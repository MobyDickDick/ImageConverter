"""Run the entire freshly collected default suite in isolated file groups."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent

def main():
    checks=FOLDER/'checks'
    checks.mkdir(exist_ok=True)
    env=dict(os.environ,PYTHONIOENCODING='utf-8',ICC_SEARCH_SEED='20261018')
    collected=subprocess.run([sys.executable,'-m','pytest','--collect-only','-q'],cwd=ROOT,
        env=env,encoding='utf-8',capture_output=True,check=True).stdout
    nodes=[s.strip() for s in collected.splitlines() if s.startswith('tests/') and '::' in s]
    assert nodes and len(nodes)==len(set(nodes))
    groups=[[] for _ in range(4)]
    files={}
    for node in nodes:
        files.setdefault(node.split('::')[0],[]).append(node)
    for file,items in sorted(files.items(),key=lambda kv:-len(kv[1])):
        group=min(groups,key=len)
        group.extend(items)
    (checks/'plan.json').write_text(json.dumps(dict(expected_nodes=nodes,groups=groups),indent=2)+'\n',encoding='utf-8')
    def run(index):
        selected=list(dict.fromkeys(n.split('::')[0] for n in groups[index]))
        command=[sys.executable,'-m','pytest','-q',*selected,'--basetemp',str(ROOT/f'.tmp/motor-suite-{index}'),
                 '--junitxml',str(checks/f'group_{index}.xml')]
        with (checks/f'group_{index}.log').open('w',encoding='utf-8') as log:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        return dict(group=index,returncode=result.returncode)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(run,range(4)))
    cases=[]
    for index in range(4):
        cases.extend(ET.parse(checks/f'group_{index}.xml').iter('testcase'))
    def node_id(case):
        parts=case.get('classname').split('.')
        for cut in range(len(parts),0,-1):
            path='/'.join(parts[:cut])+'.py'
            if (ROOT/path).exists():
                return '::'.join([path,*parts[cut:],case.get('name')])
        raise ValueError(case.attrib)
    actual=[node_id(c) for c in cases]
    failed=sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
    skipped=sum(c.find('skipped') is not None for c in cases)
    summary=dict(collected=len(nodes),measured=len(cases),passed=len(cases)-skipped-failed,
        skipped=skipped,failed=failed,exact_node_coverage=len(actual)==len(set(actual)) and set(actual)==set(nodes),groups=results)
    (checks/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(summary,flush=True)
    return 0 if not failed and summary['exact_node_coverage'] and all(r['returncode']==0 for r in results) else 1

if __name__=='__main__':
    raise SystemExit(main())
