"""Audit changed description guards; this deliberately does not convert images."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from src.iCCModules.imageCompositeConverterPrimitiveScene import description_counts

BASELINE='daaa5c0a0'
SOURCE='src/iCCModules/imageCompositeConverterGradientJunction.py'


def eligibility(source):
    tree=ast.parse(source)
    fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit_gradient_junction'))
    body=[]
    for node in fn.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='arr' for t in node.targets):
            break
        body.append(node)
    fn.body=body+[ast.Return(value=ast.Constant(True))]
    tree=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
    namespace={'re':re}
    exec(compile(tree,'description-guard-audit','exec'),namespace)
    return lambda d:bool(namespace['fit_gradient_junction'](1,1,description=d,image=None,render_fn=None,error_fn=None))


def main():
    before=subprocess.check_output(['git','show',BASELINE+':'+SOURCE],cwd=ROOT)
    after=(ROOT/SOURCE).read_bytes()
    old,new=eligibility(before.decode()),eligibility(after.decode())
    archive=ROOT/'artifacts/satisfactory_conversions/index.json'
    records=[dict(variant=c['variant'],new_scene_eligible=description_counts(c['description']) is not None,
                  old_junction_eligible=old(c['description']),new_junction_eligible=new(c['description']))
             for c in json.loads(archive.read_text(encoding='utf-8'))['cases']]
    assert all(not c['new_scene_eligible'] and c['old_junction_eligible']==c['new_junction_eligible'] for c in records)
    report=dict(evidence_kind='description_gate_audit_not_conversion',case_count=len(records),
        baseline_commit=BASELINE,archive_index_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        old_source_sha256=hashlib.sha256(before).hexdigest(),new_source_sha256=hashlib.sha256(after).hexdigest(),
        changed_routes=0,cases=records)
    Path(__file__).with_name('archive_route_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'{len(records)} archive descriptions preserve their prior fitter eligibility')


if __name__=='__main__':
    main()
