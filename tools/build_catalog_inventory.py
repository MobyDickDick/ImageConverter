"""Join every catalog bitmap to descriptions, pinned admissions and pixel checks.

Read-only toward sources/archives. This measures saved SVGs, never converts an
input, reads a sample template or runs a detector on reserved real holdouts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import quote
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl

ROOT = Path(__file__).resolve().parents[1]
BITMAPS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp'}
SVG_DIRS = ('artifacts/converted_images/converted_svgs',
            'artifacts/converted_images/catalog_background_svgs',
            'artifacts/converted_images/catalog_manual_svgs',
            'artifacts/converted_images/converted_svg_failed',
            'artifacts/converted_images/reports/conversion_bestlist_snapshots',
            'artifacts/regression_baseline/legacy_ac08/svgs',
            'artifacts/regression_baseline/satisfactory/svgs')
LABELS = dict(pixel_pass='Rastergates erfüllt', pixel_fail='Rastergates verfehlt',
              measurement_error='Messung fehlgeschlagen', no_svg='Kein gespeichertes SVG',
              reserved='Reserviert, nicht geprüft', source_conflict='Widersprüchliche Quellkopien',
              auxiliary='Hilfsgrafik außerhalb des Katalogs')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else default


def inside(root, path):
    target = (root/path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Evidence path leaves repository: '+str(path))
    return target


def relative(root, path):
    return path.resolve().relative_to(root.resolve()).as_posix()


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def publish_progress(path, payload):
    """Windows readers can briefly deny replacement; UI progress is best effort.

    Never sacrifice a catalog measurement because a polling request still has
    the previous progress file open. The next tick retries with current counts.
    """
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload), encoding='utf-8')
    for attempt in range(5):
        try:
            temporary.replace(path)
            return True
        except PermissionError:
            if attempt < 4:
                time.sleep(.02*(attempt+1))
    return False


def _quality_worker(connection):
    # Native viewport parsing and rendering both stay in the bounded child.
    import cv2
    import numpy as np
    from tools.evaluate_svg_text_baseline import render_librsvg
    from tools.run_plan_b_variations import measure_quality
    try:
        while True:
            image_path, svg_path = connection.recv()
            result = dict(measured_at=utcnow(), renderers={})
            try:
                image = cv2.imdecode(np.frombuffer(Path(image_path).read_bytes(), np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError('Unreadable source bitmap')
                result.update(width=image.shape[1], height=image.shape[0])
                svg = Path(svg_path).read_text(encoding='utf-8-sig')
                for name in ('mupdf', 'librsvg'):
                    try:
                        renderer = None
                        if name == 'librsvg':
                            pixels = render_librsvg(svg, image.shape[1], image.shape[0])
                            renderer = lambda *args: pixels
                        result['renderers'][name] = measure_quality(image, svg, render_fn=renderer)
                    except Exception as exc:
                        result['renderers'][name] = dict(error=type(exc).__name__+': '+str(exc))
            except Exception as exc:
                result['error'] = type(exc).__name__+': '+str(exc)
            connection.send(result)
    except (EOFError, BrokenPipeError):
        pass
    finally:
        connection.close()


class QualityWorker:
    def __init__(self, timeout=35., max_requests=64):
        self.timeout, self.max_requests = timeout, max_requests
        self.process = self.connection = None
        self.requests = 0

    def close(self):
        if self.connection is not None:
            self.connection.close()
        if self.process is not None:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=1)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=1)
            self.process.close()
        self.process = self.connection = None
        self.requests = 0

    def measure(self, image, svg):
        if self.process is None or not self.process.is_alive() or self.requests >= self.max_requests:
            self.close()
            parent, child = multiprocessing.get_context('spawn').Pipe()
            self.process = multiprocessing.get_context('spawn').Process(target=_quality_worker, args=(child,), daemon=True)
            self.connection = parent
            self.process.start()
            child.close()
        try:
            self.connection.send((str(image), str(svg)))
            if not self.connection.poll(self.timeout):
                raise TimeoutError('Pixel measurement exceeded request budget')
            result = self.connection.recv()
            self.requests += 1
            return result
        except (EOFError, BrokenPipeError, OSError, TimeoutError) as exc:
            self.close()
            return dict(error=type(exc).__name__+': '+str(exc), measured_at=utcnow(), renderers={})


def classify(measurement):
    renderers = measurement.get('renderers', {})
    if measurement.get('error') or any(name not in renderers or 'error' in renderers[name]
                                        for name in ('mupdf', 'librsvg')):
        return 'measurement_error'
    return 'pixel_pass' if all(renderers[name]['satisfactory'] for name in ('mupdf', 'librsvg')) else 'pixel_fail'


def quality_order(candidate):
    measurement = candidate['measurement']
    status = classify(measurement)
    errors = [r['metrics'].get('normalized_mse', float('inf'))
              for r in measurement.get('renderers', {}).values() if 'metrics' in r]
    return ({'pixel_pass': 0, 'pixel_fail': 1, 'measurement_error': 2}[status],
            max(errors, default=float('inf')), candidate['svg'])


def discover(root):
    source = root/'artifacts/images_to_convert'
    descriptions_path = source/'Finale_Wurzelformen_V3.xml'
    descriptions = loadDescriptionMappingImpl(str(descriptions_path), get_base_name_from_file_fn=getBaseNameFromFileImpl)
    image_names = {str(e.text or '').strip().casefold()
                   for e in ET.parse(descriptions_path).getroot().findall('.//bilder/bild')}
    copies = defaultdict(list)
    for directory in (source, source/'succesessfulConvertedImages', source/'nonconvertable'):
        if directory.is_dir():
            for path in sorted(directory.iterdir()):
                if path.is_file() and path.suffix.lower() in BITMAPS:
                    inside(root, path)
                    copies[path.name.casefold()].append(path)
    archive_root = root/'artifacts/satisfactory_conversions'
    index = read_json(archive_root/'index.json', dict(cases=[]))
    archive = {}
    for case in index['cases']:
        key = case['variant'].casefold()
        if key in archive:
            raise ValueError('Duplicate archive variant: '+case['variant'])
        archive[key] = case
    candidates = defaultdict(list)
    for directory in SVG_DIRS:
        folder = root/directory
        if folder.is_dir():
            paths = folder.rglob('*.svg') if directory.endswith('/catalog_background_svgs') else folder.iterdir()
            for path in sorted(paths):
                if path.is_file() and path.suffix.lower() == '.svg':
                    inside(root, path)
                    candidates[path.stem.casefold()].append(path)
    reserved = set()
    for path in sorted((root/'config').glob('real_composition_holdout*.json')):
        reservation = read_json(path, {})
        if reservation.get('evaluation_policy', {}).get('status') == 'sealed_unrun':
            for case in reservation.get('cases', []):
                reserved.update(n.casefold() for n in [case['file'], *case.get('family_members', [])])
    return descriptions_path, descriptions, image_names, copies, archive_root, archive, candidates, reserved


def build(root, *, measure, cache=None, signature='uncached', force=False, progress=None):
    root = root.resolve()
    desc_path, descriptions, image_names, copies, archive_root, archive, svgs, reserved = discover(root)
    cache = {} if cache is None else cache
    rows, used_cache, measured = [], 0, 0
    if progress:
        progress(0, len(copies), measured, used_cache)
    for number, (name, paths) in enumerate(sorted(copies.items()), 1):
        source = paths[0]
        variant = source.stem
        hashes = [digest(p.read_bytes()) for p in paths]
        description_key = next((k for k in (source.name, variant, variant.upper(), variant.lower(),
            getBaseNameFromFileImpl(variant), getBaseNameFromFileImpl(variant).upper()) if descriptions.get(k)), None)
        role = 'auxiliary' if source.suffix.lower() == '.gif' and name not in image_names else 'catalog'
        row = dict(filename=source.name, variant=variant, group=variant.split('_', 1)[0][:2].upper(),
            role=role, image=relative(root, source), image_sha256=hashes[0],
            all_source_paths=[relative(root, p) for p in paths], source_conflict=len(set(hashes)) > 1,
            description=descriptions.get(description_key, ''), description_key=description_key,
            description_source=relative(root, desc_path), archived=False, candidates=[], selected=None,
            semantic_revalidated=False, manual_review='not_systematically_recorded')
        options = list(svgs.get(variant.casefold(), []))
        admission = archive.get(variant.casefold())
        if admission is not None:
            row['archived'] = True
            image = inside(root, archive_root/admission['image'])
            svg = inside(root, archive_root/admission['svg'])
            row['archive'] = dict(description=admission['description'],
                description_matches_catalog=' '.join(admission['description'].split()) == ' '.join(row['description'].split()),
                image=relative(root, image), svg=relative(root, svg),
                source_matches=hashes[0] == admission['image_sha256'],
                image_hash_matches=image.is_file() and digest(image.read_bytes()) == admission['image_sha256'],
                svg_hash_matches=svg.is_file() and digest(svg.read_bytes()) == admission['svg_sha256'],
                evidence=admission.get('evidence'),
                evidence_exists=bool(admission.get('evidence')) and inside(root, admission['evidence']).exists(),
                execution_mode=admission.get('execution_mode'), historical_metrics=admission.get('metrics', {}))
            if svg.is_file():
                options.insert(0, svg)
        # Deduplicate identical saved outputs, retaining every path as provenance.
        unique = {}
        for svg in options:
            svg_hash = digest(svg.read_bytes())
            if svg_hash in unique:
                unique[svg_hash]['all_paths'].append(relative(root, svg))
            else:
                unique[svg_hash] = dict(svg=relative(root, svg), svg_sha256=svg_hash,
                                       all_paths=[relative(root, svg)])
        if role == 'auxiliary':
            row['status'] = 'auxiliary'
        elif name in reserved:
            row['status'] = 'reserved'
        elif row['source_conflict']:
            row['status'] = 'source_conflict'
        elif not unique:
            row['status'] = 'no_svg'
        else:
            for candidate in unique.values():
                key = digest(json.dumps([signature, hashes[0], candidate['svg_sha256']]).encode())
                if not force and key in cache and classify(cache[key]) != 'measurement_error':
                    measurement = cache[key]
                    used_cache += 1
                else:
                    measurement = measure(source, inside(root, candidate['svg']))
                    cache[key] = measurement
                    measured += 1
                candidate['measurement'] = measurement
                row['candidates'].append(candidate)
                if progress:
                    progress(number-1, len(copies), measured, used_cache)
            row['selected'] = min(row['candidates'], key=quality_order)
            row['status'] = classify(row['selected']['measurement'])
        rows.append(row)
        if progress:
            progress(number, len(copies), measured, used_cache)
    catalog = [r for r in rows if r['role'] == 'catalog']
    archived = [r for r in catalog if r['archived']]
    groups = {}
    for group in sorted({r['group'] for r in catalog}):
        members = [r for r in catalog if r['group'] == group]
        groups[group] = dict(total=len(members), archived=sum(r['archived'] for r in members),
                            statuses=dict(Counter(r['status'] for r in members)))
    summary = dict(schema='catalog_inventory_v1', generated_at=utcnow(),
        catalog_bitmaps=len(catalog), auxiliary_bitmaps=len(rows)-len(catalog),
        unique_catalog_variants=len({r['variant'].casefold() for r in catalog}),
        catalog_statuses=dict(Counter(r['status'] for r in catalog)),
        descriptions_present=sum(bool(r['description']) for r in catalog),
        missing_descriptions=[r['filename'] for r in catalog if not r['description']],
        archived=len(archived), not_archived=len(catalog)-len(archived),
        archive_pinned_pairs_valid=sum(all(r['archive'][k] for k in
            ('source_matches', 'image_hash_matches', 'svg_hash_matches')) for r in archived),
        archive_description_differences=sum(not r['archive']['description_matches_catalog'] for r in archived),
        archive_missing_evidence=sum(not r['archive']['evidence_exists'] for r in archived),
        archived_current_pixel_pass=sum(r['status'] == 'pixel_pass' for r in archived),
        measurements_computed=measured, measurements_reused=used_cache, groups=groups,
        fresh_conversion_performed=False, semantic_revalidation_performed=False,
        manual_reviews_systematically_recorded=False)
    from src.imageConverterClasses import enrich_catalog
    summary['geometry_classes'] = enrich_catalog(root, rows)
    return rows, summary, cache


def runtime_signature(root):
    import cv2
    import fitz
    from tools.evaluate_svg_text_baseline import find_librsvg
    from tools.run_plan_b_variations import LIMITS
    versions = dict(python=sys.version.split()[0], pymupdf=fitz.VersionBind, opencv=cv2.__version__,
        librsvg=subprocess.check_output([find_librsvg(), '--version'], text=True).strip())
    files = {relative(root, p): digest(p.read_bytes()) for p in sorted((root/'src').rglob('*.py'))}
    for name in ('tools/build_catalog_inventory.py', 'tools/run_plan_b_variations.py',
                 'tools/evaluate_svg_text_baseline.py', 'tools/evaluate_quality_complexity_gate.py'):
        files[name] = digest((root/name).read_bytes())
    metadata = dict(versions=versions, source_sha256=files, limits=LIMITS)
    return digest(json.dumps(metadata, sort_keys=True).encode()), metadata


def update_candidate(root, payload, filename, svg, *, measure):
    """Update one saved catalog row without discovering or measuring other files."""
    import copy

    payload = copy.deepcopy(payload)
    row = next((r for r in payload['rows'] if r['filename'] == filename), None)
    if row is None or row['role'] != 'catalog' or row['status'] in {'reserved', 'source_conflict'}:
        raise ValueError('No eligible catalog row: '+filename)
    for path in sorted((root/'config').glob('real_composition_holdout*.json')):
        policy = read_json(path, {})
        if policy.get('evaluation_policy', {}).get('status') == 'sealed_unrun':
            if any(filename.casefold() in {n.casefold() for n in [case['file'], *case.get('family_members', [])]}
                   for case in policy.get('cases', [])):
                raise ValueError('Reserved catalog row: '+filename)
    source = inside(root, row['image'])
    for path in row.get('all_source_paths', [row['image']]):
        if digest(inside(root, path).read_bytes()) != row['image_sha256']:
            raise ValueError('Source bitmap changed since catalog measurement: '+filename)
    svg = inside(root, svg)
    expected = [root/'artifacts/converted_images'/folder
                for folder in ('catalog_background_svgs', 'catalog_manual_svgs')]
    if not any(svg.is_relative_to(folder.resolve()) for folder in expected) or svg.stem.casefold() != Path(filename).stem.casefold():
        raise ValueError('Invalid catalog candidate path')
    svg_hash, svg_path = digest(svg.read_bytes()), relative(root, svg)
    old_status = row['status']
    candidate = next((c for c in row['candidates'] if c['svg_sha256'] == svg_hash), None)
    if candidate is None:
        candidate = dict(svg=svg_path, svg_sha256=svg_hash, all_paths=[svg_path])
        row['candidates'].append(candidate)
    elif svg_path not in candidate['all_paths']:
        candidate['all_paths'].append(svg_path)
    # Only this newly produced candidate is checked, even if its bytes match
    # an old attempt. Other saved measurements and their dates stay intact.
    candidate['measurement'] = measure(source, svg)
    row['selected'] = min(row['candidates'], key=quality_order)
    row['status'] = classify(row['selected']['measurement'])
    summary = payload['summary']
    def change_counts(counts):
        counts = Counter(counts)
        counts[old_status] -= 1
        counts[row['status']] += 1
        return {key: value for key, value in counts.items() if value}
    summary['catalog_statuses'] = change_counts(summary['catalog_statuses'])
    group = summary['groups'][row['group']]
    group['statuses'] = change_counts(group['statuses'])
    if row['archived']:
        summary['archived_current_pixel_pass'] += int(row['status'] == 'pixel_pass') - int(old_status == 'pixel_pass')
    from src.imageConverterClasses import summarize
    summary['geometry_classes'] = summarize(payload['rows'])
    summary.setdefault('full_generated_at', summary['generated_at'])
    summary.update(generated_at=utcnow(), measurement_scope='single_candidate',
                   updated_filename=filename, measurements_computed=1, measurements_reused=0)
    return payload['rows'], summary


def write_report(root, output, rows, summary, metadata):
    from tools.catalog_inventory_html import render_catalog_html
    output.mkdir(parents=True, exist_ok=True)
    linked = []
    for row in rows:
        row = dict(row)
        row['image_url'] = quote(os.path.relpath(root/row['image'], output).replace('\\', '/'), safe='/')
        if row['selected']:
            row['svg_url'] = quote(os.path.relpath(root/row['selected']['svg'], output).replace('\\', '/'), safe='/')
        if row.get('archive', {}).get('evidence_exists'):
            row['evidence_url'] = quote(os.path.relpath(root/row['archive']['evidence'], output).replace('\\', '/'), safe='/')
        linked.append(row)
    payload = dict(summary=summary, labels=LABELS, rows=linked)
    (output/'manifest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (output/'sources.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    template = (Path(__file__).parent/'templates/catalog_inventory.html').read_text(encoding='utf-8')
    (output/'index.html').write_text(render_catalog_html(template, payload), encoding='utf-8')


def main():
    from src.iCCModules.imageCompositeConverterPower import conversion_awake
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/catalog_inventory')
    parser.add_argument('--force', action='store_true', help='Remeasure instead of reusing hash-identical checks')
    parser.add_argument('--cache', type=Path, help='Read a previous measurement cache; writes stay in --output')
    parser.add_argument('--progress-file', type=Path, help='Atomically publish current measurement counts')
    parser.add_argument('--render-only', action='store_true', help='Rebuild the HTML from the saved manifest without new measurements')
    parser.add_argument('--update-manifest', type=Path, help='Update only one candidate in this saved catalog')
    parser.add_argument('--filename', help='Catalog filename for --update-manifest')
    parser.add_argument('--candidate', type=Path, help='New background SVG for --update-manifest')
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.exists() and any(output.iterdir()):
        previous = read_json(output/'summary.json', {})
        if previous.get('schema') != 'catalog_inventory_v1':
            raise ValueError('Existing output is not an owned catalog inventory')
    if args.render_only:
        from tools.catalog_inventory_html import render_catalog_html
        payload = read_json(output/'manifest.json')
        if not payload or payload.get('summary', {}).get('schema') != 'catalog_inventory_v1':
            raise ValueError('A saved catalog manifest is required for --render-only')
        template = (Path(__file__).parent/'templates/catalog_inventory.html').read_text(encoding='utf-8')
        (output/'index.html').write_text(render_catalog_html(template, payload), encoding='utf-8')
        print(f'HTML rebuilt: {len(payload["rows"])} entries; no new measurements')
        return 0
    if args.update_manifest:
        if not args.filename or not args.candidate or args.force:
            parser.error('--update-manifest requires --filename and --candidate, without --force')
        payload = read_json(args.update_manifest)
        if payload.get('summary', {}).get('schema') != 'catalog_inventory_v1':
            raise ValueError('A saved catalog manifest is required')
        worker = QualityWorker()
        started = time.monotonic()
        try:
            with conversion_awake():
                if args.progress_file:
                    publish_progress(args.progress_file, dict(completed=0, total=1, measured=0, cached=0))
                rows, summary = update_candidate(root, payload, args.filename, args.candidate, measure=worker.measure)
        finally:
            worker.close()
        metadata = read_json(args.update_manifest.parent/'sources.json', {})
        metadata.setdefault('measurement_cache', str((args.update_manifest.parent/'measurements.json').resolve()))
        summary['elapsed_seconds'] = round(time.monotonic()-started, 3)
        write_report(root, output, rows, summary, metadata)
        if args.progress_file:
            publish_progress(args.progress_file, dict(completed=1, total=1, measured=1, cached=0,
                elapsed_seconds=round(time.monotonic()-started, 3)))
        print(f'Einzelprüfung {args.filename}: 1 SVG; übrige Katalogmessungen unverändert.', flush=True)
        return 0
    signature, metadata = runtime_signature(root)
    cache = read_json(args.cache or output/'measurements.json', {})
    worker = QualityWorker()
    started = time.monotonic()
    last_progress = 0.

    def progress(n, total, measured, cached):
        nonlocal last_progress
        now = time.monotonic()
        if n != total and now-last_progress < .25:
            return
        last_progress = now
        payload = dict(completed=n, total=total, measured=measured, cached=cached,
                       elapsed_seconds=round(now-started, 3))
        if args.progress_file:
            publish_progress(args.progress_file, payload)
        if n % 100 == 0 or n == total:
            print(f'Inventar {n}/{total}; neue Paarprüfungen {measured}; Cache {cached}', flush=True)

    try:
        with conversion_awake():
            rows, summary, cache = build(root, measure=worker.measure, cache=cache, signature=signature,
                force=args.force, progress=progress)
    finally:
        worker.close()
    summary['measurement_signature'] = signature
    summary['elapsed_seconds'] = round(time.monotonic()-started, 3)
    metadata.update(description_source_sha256=digest((root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').read_bytes()),
        archive_index_sha256=digest((root/'artifacts/satisfactory_conversions/index.json').read_bytes()))
    write_report(root, output, rows, summary, metadata)
    (output/'measurements.json').write_text(json.dumps(cache, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
