"""Compare the actual filename/full catalogs with a clean baseline source export."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((FOLDER/'manifest.json').read_text(encoding='utf-8'))
    commit = manifest['provenance']['commit']
    baseline = output/'baseline_source'
    baseline.mkdir()
    archive = subprocess.check_output(['git', 'archive', '--format=zip', commit, 'src', 'tools', 'config'], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        source.extractall(baseline)
    # Match the repository's dependency discovery without copying binaries.
    (baseline/'.venv/Lib/site-packages').mkdir(parents=True)
    catalog = 'artifacts/descriptions/Finale_Wurzelformen_V3.xml'
    original = subprocess.check_output(['git', 'show', commit+':'+catalog], cwd=ROOT)
    (output/'original.xml').write_bytes(original)
    results = []
    for name, project, table in (
        ('baseline', baseline, output/'original.xml'),
        ('old_catalog_current_runtime', ROOT, output/'original.xml'),
        ('final', ROOT, ROOT/catalog),
    ):
        inputs = output/name/'input'
        inputs.mkdir(parents=True)
        image = ROOT/'artifacts/images_to_convert/SE0082.jpg'
        shutil.copyfile(image, inputs/image.name)
        conversion = output/name/'conversion'
        paths = [str(Path(np.__file__).resolve().parents[1]), str(project)]
        command = [sys.executable, '-I', '-c', 'import sys,runpy;sys.path[:0]='+repr(paths)+
                   ";runpy.run_module('tools.run_plan_b_variations',run_name='__main__')", '--_worker',
                   str(conversion), str(inputs), '--descriptions-path', str(table), '--output-dir', str(conversion),
                   '--start', 'SE0082', '--end', 'SE0082', '--iterations', '64',
                   '--execution-mode', 'semantic-only', '--deterministic-order']
        env = dict(os.environ, IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', PYTHONHASHSEED='0',
                   TINY_ICC_OUTPUT_VARIATION='0', ICC_FORCE_RECONVERT='1', ICC_SEARCH_SEED='0',
                   PYTHONIOENCODING='utf-8')
        with (output/(name+'.log')).open('w', encoding='utf-8') as log:
            subprocess.run(command, cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT,
                           timeout=120, check=True)
        access = json.loads((output/name/'reference_access.json').read_text())
        assert access['blocked_svg_reads'] == []
        matches = [p for folder in ('converted_svgs', 'converted_svg_failed')
                   for p in (conversion/folder).glob('*.svg') if p.stem.casefold() == 'se0082']
        assert len(matches) == 1
        saved = output/(name+'.svg')
        shutil.copyfile(matches[0], saved)
        results.append(dict(context=name, runtime_commit=commit if project == baseline else 'working_tree',
                            catalog_sha256=hashlib.sha256(table.read_bytes()).hexdigest(),
                            svg=saved.name, output_sha256=hashlib.sha256(saved.read_bytes()).hexdigest(),
                            blocked_svg_reads=[]))
    assert results[0]['output_sha256'] == results[1]['output_sha256']
    (output/'report.json').write_text(json.dumps(dict(cases=results), indent=2)+'\n', encoding='utf-8')
    print('PASS: actual filename, full old/new catalogs, exported baseline runtime')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
