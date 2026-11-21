"""Audit persisted failed deliverables without changing inputs or conversion history.

Run from the repository root with --output artifacts/evaluation/<new-audit>.
Exact duplicates disprove universal diversity. A different hash alone does not
prove a meaningful difference, generalization, or useful conversion quality.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.imageConverterDiversity import geometry_hash, foreground_similarity


def digest(data):
    return hashlib.sha256(data).hexdigest()


def discover(artifacts):
    entries, missing, errors = {}, [], []
    jobs = {}
    for path in sorted((artifacts/'gui').glob('*/job.json')):
        try:
            job = json.loads(path.read_text(encoding='utf-8'))
            jobs[path.parent] = job
            if job.get('status') in {'ready', 'running'} or job.get('quality') == 'passed':
                continue
            result = path.parent/'result.svg'
            if result.is_file():
                entries[result.resolve()] = dict(path=result, job=job, source=path.parent/'source.png')
            else:
                missing.append(str(path))
        except (OSError, ValueError) as exc:
            errors.append(dict(path=str(path), error=str(exc)))
    for folder in sorted(artifacts.rglob('converted_svg_failed')):
        for path in sorted(folder.glob('*.svg')):
            job_folder = next((parent for parent in path.parents if parent in jobs), None)
            job = jobs.get(job_folder, {})
            entries.setdefault(path.resolve(), dict(path=path, job=job,
                source=job_folder/'source.png' if job_folder else None))
    return list(entries.values()), missing, errors


def duplicate_groups(records, field):
    groups = defaultdict(list)
    for row in records:
        if row.get(field):
            groups[row[field]].append(row['id'])
    return [ids for ids in groups.values() if len(ids) > 1]


def audit(artifacts, output):
    from src.imageConverterSample import render_svg
    entries, missing, errors = discover(artifacts)
    output.mkdir(parents=True, exist_ok=True)
    records, rasters, source_cache = [], {}, {}
    for index, entry in enumerate(entries):
        path, job, source = entry['path'], entry['job'], entry['source']
        row = dict(id=len(records), path=str(path.resolve()), name=job.get('name', path.stem),
                   seed=job.get('search_seed'), description=job.get('description'),
                   quality=job.get('quality', 'failed_directory'),
                   recovery=bool(job.get('recovery')), previous_job_id=job.get('previous_job_id'))
        records.append(row)
        try:
            svg = path.read_text(encoding='utf-8-sig')
            row['file_sha256'] = digest(svg.encode('utf-8'))
            row['geometry_sha256'] = geometry_hash(svg)
            if any(e.tag.rsplit('}', 1)[-1] in {'image', 'foreignObject'} for e in ET.fromstring(svg).iter()):
                row['render_excluded'] = 'embedded_raster_or_foreign_object'
                continue
            raster = render_svg(svg, 96, 96)
            row['raster_sha256'] = digest(raster.tobytes())
            row['foreground_pixels'] = int((raster.min(axis=2) < 245).sum())
            rasters[row['id']] = raster
            if source and source.is_file():
                key = digest(source.read_bytes())
                if key not in source_cache:
                    with Image.open(source) as image:
                        rgb = np.asarray(image.convert('RGB'))
                    source_cache[key] = digest(str(rgb.shape).encode()+rgb.tobytes())
                row['source_sha256'] = source_cache[key]
                row['description_sha256'] = digest((job.get('description') or '').encode('utf-8'))
        except (OSError, ValueError, SyntaxError, RuntimeError) as exc:
            row['error'] = str(exc)
        if (index+1) % 200 == 0:
            print(f'Geprüft: {index+1}/{len(entries)}', flush=True)
    groups = defaultdict(list)
    for row in records:
        if row.get('source_sha256') and row['id'] in rasters:
            groups[row['source_sha256'], row['description_sha256']].append(row)
    pairs = []
    for rows in groups.values():
        for i, a in enumerate(rows):
            for b in rows[i+1:]:
                # A GUI result and its own CLI artifact are one conversion.
                if Path(a['path']).parents[0] in Path(b['path']).parents or Path(b['path']).parents[0] in Path(a['path']).parents:
                    continue
                similarity = foreground_similarity(rasters[a['id']], rasters[b['id']])
                pairs.append(dict(a=a['id'], b=b['id'], foreground_similarity=similarity,
                                  exact_raster=a['raster_sha256'] == b['raster_sha256'],
                                  exact_file=a['file_sha256'] == b['file_sha256'],
                                  exact_geometry=a['geometry_sha256'] == b['geometry_sha256'],
                                  same_seed=a['seed'] == b['seed']))
    duplicates = duplicate_groups(records, 'raster_sha256')
    geometry_duplicates = duplicate_groups(records, 'geometry_sha256')
    report = dict(scope='All persisted GUI failures and all converted_svg_failed directories under artifacts; final artifacts, not every internal search candidate.',
        measurement='Render at 96x96 RGB. Similarity = 1 - mean absolute RGB difference / 255 over the union of foreground pixels (<245). No quality or generalization claim.',
        records=len(records), rendered=len(rasters), missing_result_jobs=len(missing),
        errors=errors, missing_result_job_paths=missing,
        geometry_duplicate_groups=geometry_duplicates, raster_duplicate_groups=duplicates,
        repeat_pairs=len(pairs), identical_repeat_pairs=sum(p['exact_raster'] for p in pairs),
        byte_identical_repeat_pairs=sum(p['exact_file'] for p in pairs),
        byte_identical_different_seed_pairs=sum(p['exact_file'] and not p['same_seed'] for p in pairs),
        near_identical_repeat_pairs_99=sum(p['foreground_similarity'] >= .99 for p in pairs),
        different_seed_repeat_pairs=sum(not p['same_seed'] for p in pairs),
        identical_different_seed_pairs=sum(p['exact_raster'] and not p['same_seed'] for p in pairs),
        universal_diversity_proven=False,
        universal_distinctness_disproved=bool(duplicates or geometry_duplicates),
        interpretation='Exact duplicates refute the claim that all failures differ. Nonidentical results alone do not establish useful independent reconstruction.',
        entries=records, comparisons=pairs)
    (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    examples = sorted(pairs, key=lambda p: (not p['same_seed'], p['exact_file'], p['foreground_similarity']), reverse=True)[:8]
    if examples:
        sheet = Image.new('RGB', (600, 150*len(examples)), 'white')
        draw = ImageDraw.Draw(sheet)
        for i, pair in enumerate(examples):
            for column, key in enumerate(('a', 'b')):
                row = records[pair[key]]
                sheet.paste(Image.fromarray(rasters[row['id']]), (column*300, i*150+40))
                draw.text((column*300, i*150+4), f"#{row['id']} {row['name']}"[:46], fill='black')
            draw.text((105, i*150+65), f"{pair['foreground_similarity']:.6%}", fill='black')
        sheet.save(output/'comparison.png')
    summary = {k: report[k] for k in ('records', 'rendered', 'missing_result_jobs', 'repeat_pairs',
        'identical_repeat_pairs', 'near_identical_repeat_pairs_99', 'different_seed_repeat_pairs',
        'identical_different_seed_pairs', 'universal_distinctness_disproved')}
    summary['raster_duplicate_groups'] = len(duplicates)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, default=ROOT/'artifacts')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.artifacts, args.output)
