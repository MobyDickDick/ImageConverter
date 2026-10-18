"""Compare the parent and current letter-disk runtime with the archive's seed."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import types

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--_worker':
        if sys.argv[2] == 'before':
            name = 'src.iCCModules.imageCompositeConverterLabeledDisk'
            module = types.ModuleType(name)
            source = FOLDER/'parent_labeled_disk.py.txt'
            module.__file__ = str(source)
            exec(compile(source.read_text(encoding='utf-8'), str(source), 'exec'), module.__dict__)
            sys.modules[name] = module
        from tools.run_plan_b_variations import converter_worker
        return converter_worker(sys.argv[3:])
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = json.loads((archive/'index.json').read_text(encoding='utf-8'))
    cases = [c for c in index['cases'] if c['variant'].startswith('AC0910_')]
    assert len(cases) == 3
    paths = [str(ROOT), str(Path(np.__file__).resolve().parents[1]), *sys.path]
    bootstrap = 'import sys,runpy;sys.path[:0]='+repr(paths)+';runpy.run_path('+repr(str(Path(__file__).resolve()))+",run_name='__main__')"
    env = dict(os.environ, TINY_ICC_OUTPUT_VARIATION='0', PYTHONHASHSEED='0',
               IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_FORCE_RECONVERT='1', ICC_SEARCH_SEED='0')
    accesses = {}
    for mode in ('before', 'after'):
        inputs = output/('inputs_'+mode)
        inputs.mkdir()
        for case in cases:
            shutil.copyfile(archive/case['image'], inputs/Path(case['image']).name)
        with (output/(mode+'.log')).open('w', encoding='utf-8') as log:
            subprocess.run([sys.executable,'-I','-c',bootstrap,'--_worker',mode,str(output/mode),
                str(inputs),'--descriptions-path',str(archive/'descriptions.xml'),'--output-dir',str(output/mode),
                '--execution-mode','semantic-only','--start','AC0910','--end','AC0910','--deterministic-order'],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
        accesses[mode] = json.loads((output/'reference_access.json').read_text())
        assert not accesses[mode]['blocked_svg_reads']
        for case in cases:
            name = case['variant']+'.svg'
            matches = list((output/mode/'converted_svgs').glob(name))+list((output/mode/'converted_svg_failed').glob(name))
            assert len(matches) == 1
            shutil.copyfile(matches[0],output/mode/name)
    for case in cases:
        name = case['variant']+'.svg'
        assert (output/'before'/name).read_bytes() == (output/'after'/name).read_bytes(), name
    report = dict(parent_commit='8c0d2ab66', search_seed=0, runtime_module='imageCompositeConverterLabeledDisk',
                  parent_module_sha256=hashlib.sha256((FOLDER/'parent_labeled_disk.py.txt').read_bytes()).hexdigest(),
                  byte_equal_variants=[c['variant'] for c in cases], reference_access=accesses)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS: parent/current archive-seed CLI outputs byte equal for all three label disks')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
