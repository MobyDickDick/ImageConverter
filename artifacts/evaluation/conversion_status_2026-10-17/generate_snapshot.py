"""Reconcile catalog coverage, accepted pairs, older review and manual samples."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
REVIEW = ROOT/'artifacts/evaluation/oriented_circle_linework_recheck_v1/conversion_quality_records_v2.csv'
ARCHIVE = ROOT/'artifacts/satisfactory_conversions'
THRESHOLD = 0.045945679012345676


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    index = json.loads((ARCHIVE/'index.json').read_text(encoding='utf-8'))
    accepted = {c['variant'].casefold(): c for c in index['cases']}
    assert index['case_count'] == len(accepted)
    for c in accepted.values():
        for key in ('image', 'svg'):
            assert digest(ARCHIVE/c[key]) == c[key+'_sha256']
    catalog = defaultdict(list)
    for path in sorted((ROOT/'artifacts/images_to_convert').rglob('*')):
        if path.suffix.lower() == '.jpg' and 'samples' not in path.parts:
            catalog[path.stem.casefold()].append(path.relative_to(ROOT).as_posix())
    assert not accepted.keys()-catalog.keys(), 'Accepted case outside catalog inventory'
    review = list(csv.DictReader(REVIEW.open(encoding='utf-8', newline='')))
    reviewed = {}
    for case in review:
        name = case['variant'].casefold()
        if name in reviewed:
            assert all(reviewed[name][key] == case[key] for key in case if key != 'source')
        reviewed[name] = case
    samples = {p.stem.casefold() for p in (ROOT/'artifacts/samples').glob('*.svg')}
    rows = []
    for name, paths in sorted(catalog.items()):
        case, old = accepted.get(name), reviewed.get(name)
        state = ('accepted' if case else 'older_review_missing_pair' if old and old['status'] != 'ok'
                 else 'older_review_above_threshold' if old and float(old['normalized_mse']) > THRESHOLD
                 else 'older_review_below_threshold' if old else 'not_in_review')
        rows.append(dict(variant=case['variant'] if case else Path(paths[0]).stem,
            status=state, image=paths[0], all_source_paths=' | '.join(paths),
            accepted_svg=('artifacts/satisfactory_conversions/'+case['svg']) if case else '',
            accepted_mean_delta2=case['mean_delta2'] if case else '',
            evidence=case['evidence'] if case else '',
            older_review_mean_delta2=old['mean_delta2'] if old else '',
            same_name_sample_present=name in samples))
    counts = dict(Counter(row['status'] for row in rows))
    base_commit = json.loads((ROOT/'artifacts/evaluation/down_gradient_junction_recheck_v1/manifest.json').read_text(encoding='utf-8'))['provenance']['commit']
    previous = json.loads(subprocess.check_output(['git','show',base_commit+':artifacts/satisfactory_conversions/index.json'],cwd=ROOT))
    previous_names = {c['variant'].casefold() for c in previous['cases']}
    bad = {c['variant'].casefold() for c in review if c['status'] == 'ok' and float(c['normalized_mse']) > THRESHOLD}
    snapshot = dict(schema_version='conversion_status_snapshot_v1', date='2026-10-17',
        base_commit=base_commit, catalog_distinct_jpg_names=len(catalog),
        accepted_before_package=previous['case_count'], accepted_after_package=len(accepted),
        not_explicitly_accepted=len(catalog)-len(accepted), classifications=counts,
        older_review=dict(records=len(review), distinct_variants=len(reviewed),
            duplicate_records=len(review)-len(reviewed), renderable=sum(c['status']=='ok' for c in review),
            above_threshold=len(bad), below_threshold=sum(c['status']=='ok' and float(c['normalized_mse'])<=THRESHOLD for c in review),
            above_threshold_already_accepted_before=len(bad & previous_names),
            above_threshold_remaining_before=len(bad-previous_names),
            above_threshold_remaining_after=len(bad-accepted.keys()),
            missing_pair=sum(c['status']!='ok' for c in review), threshold_normalized_mse=THRESHOLD),
        samples=dict(svg_files=len(samples),accepted_with_same_name=sum(name in samples for name in accepted),
            accepted_without_same_name=sum(name not in samples for name in accepted),
            manual_approval_tracked=False),
        limitations=['No fresh full-catalog conversion: absence from archive is not a proven failure.',
            'Older review contains stale outputs; pixel threshold alone is not package acceptance.',
            'Sample filename presence does not establish manual approval or content equality.'],
        input_sha256={REVIEW.relative_to(ROOT).as_posix():digest(REVIEW),
            (ARCHIVE/'index.json').relative_to(ROOT).as_posix():digest(ARCHIVE/'index.json')})
    for filename, records in [('catalog_status.csv',rows),('manual_review_queue.csv',
            sorted((r for r in rows if r['status']=='accepted'),key=lambda r:-r['accepted_mean_delta2']))]:
        fields=list(rows[0])
        if filename == 'manual_review_queue.csv':
            fields.extend(['manual_decision','notes'])
            records=[dict(row,manual_decision='',notes='') for row in records]
        with (FOLDER/filename).open('w',encoding='utf-8-sig',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=fields,delimiter=';')
            writer.writeheader(); writer.writerows(records)
    (FOLDER/'summary.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(snapshot,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
