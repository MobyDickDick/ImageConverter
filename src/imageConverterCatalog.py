"""Cancellable catalog measurements, isolated from conversion and prior reports."""
from __future__ import annotations

import csv
from collections import Counter
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid


class CatalogError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


class CatalogQuality:
    def __init__(self, root, directory, stop_process):
        self.root, self.directory = Path(root).resolve(), Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.stop_process = stop_process
        self.lock = threading.RLock()
        self.process = self.thread = None
        self.closed = False
        self.conversion_owner = None
        self.job = read_json(self.directory/'job.json', dict(status='idle'))
        if self.job['status'] in {'running','cancelling'}:
            self.job.update(status='interrupted', message='Die Qualitätsprüfung wurde beim Serverende unterbrochen.')
            atomic_json(self.directory/'job.json', self.job)
        self._manifest_stamp = self._payload = None

    def report_folder(self):
        pointer = read_json(self.directory/'current.json', {})
        run_id = pointer.get('id', '')
        if len(run_id) == 32 and all(c in '0123456789abcdef' for c in run_id):
            folder = self.directory/run_id/'report'
            if (folder/'manifest.json').is_file():
                return folder
        return self.root/'artifacts/catalog_inventory'

    def payload(self):
        with self.lock:
            path = self.report_folder()/'manifest.json'
            if not path.is_file():
                return dict(rows=[], summary={}, labels={})
            reservations = sorted((self.root/'config').glob('real_composition_holdout*.json'))
            reviews = self.root/'config/catalog_class_visual_review.json'
            descriptions = self.root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
            stamp = (str(path), path.stat().st_mtime_ns, path.stat().st_size,
                     tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size)
                           for p in [*reservations, reviews, descriptions] if p.is_file()))
            if stamp != self._manifest_stamp:
                value = read_json(path)
                if value.get('summary', {}).get('schema') != 'catalog_inventory_v1':
                    raise CatalogError('Die gespeicherte Qualitätsliste ist ungültig.', 500)
                # The published inventory can predate a newly sealed family.
                # Apply today's reservations without rendering those old assets.
                reserved = set()
                for reservation in reservations:
                    policy = read_json(reservation, {})
                    if policy.get('evaluation_policy', {}).get('status') == 'sealed_unrun':
                        for case in policy.get('cases', []):
                            reserved.update(name.casefold() for name in [case['file'],*case.get('family_members',[])])
                for row in value['rows']:
                    if row['filename'].casefold() in reserved:
                        row.update(status='reserved', candidates=[], selected=None)
                catalog = [r for r in value['rows'] if r['role'] == 'catalog']
                value['summary']['catalog_statuses'] = dict(Counter(r['status'] for r in catalog))
                value['summary']['archived_current_pixel_pass'] = sum(r['archived'] and r['status']=='pixel_pass' for r in catalog)
                for group, summary in value['summary'].get('groups', {}).items():
                    summary['statuses'] = dict(Counter(r['status'] for r in catalog if r['group']==group))
                value['summary']['current_reservations_applied'] = True
                from src.imageConverterClasses import enrich_catalog
                value['summary']['geometry_classes'] = enrich_catalog(self.root, value['rows'])
                self._payload, self._manifest_stamp = value, stamp
            return self._payload

    def snapshot(self):
        with self.lock:
            result = dict(self.job)
            if result.get('id'):
                result['progress'] = read_json(self.directory/result['id']/'progress.json', {})
            result['summary'] = self.payload()['summary']
            result['has_report'] = bool(result['summary'])
            return result

    def command(self, folder, force, cache):
        command = [sys.executable, '-m', 'tools.build_catalog_inventory', '--root', str(self.root),
                   '--output', str(folder/'report'), '--progress-file', str(folder/'progress.json')]
        if cache.is_file():
            command += ['--cache', str(cache)]
        if force:
            command.append('--force')
        return command

    def start(self, force=False, *, owner=None):
        if type(force) is not bool:
            raise CatalogError('Ungültige Auswahl für die Neumessung.')
        with self.lock:
            if self.conversion_owner is not None and owner is not self.conversion_owner:
                raise CatalogError('Der Hintergrunddienst aktualisiert die Qualitätsliste automatisch.', 409)
            if self.closed:
                raise CatalogError('Der Server wird beendet.', 409)
            if self.thread is not None and self.thread.is_alive():
                raise CatalogError('Es läuft bereits eine Qualitätsprüfung.', 409)
            cache = self.report_folder()/'measurements.json'
            run_id = uuid.uuid4().hex
            folder = self.directory/run_id
            folder.mkdir()
            self.job = dict(id=run_id, status='running', started=time.time(), force=force,
                            message='Qualitätsprüfung wird vorbereitet. Die bisherige Liste bleibt verfügbar.')
            atomic_json(self.directory/'job.json', self.job)
            self.thread = threading.Thread(target=self._run, args=(folder, force, cache), daemon=True)
            self.thread.start()
            return self.snapshot()

    def _run(self, folder, force, cache):
        try:
            with (folder/'console.log').open('wb') as log:
                with self.lock:
                    if self.job['status'] != 'running':
                        return
                    options = dict(cwd=str(Path(__file__).resolve().parents[1]), stdin=subprocess.DEVNULL, stdout=log, stderr=log)
                    if os.name == 'nt':
                        options['creationflags'] = subprocess.CREATE_NO_WINDOW
                    else:
                        options['start_new_session'] = True
                    process = subprocess.Popen(self.command(folder,force,cache), **options)
                    self.process = process
                code = process.wait()
            with self.lock:
                if self.job['status'] == 'cancelling':
                    self.job.update(status='cancelled', message='Qualitätsprüfung abgebrochen. Die bisherige vollständige Liste bleibt erhalten.')
                elif code != 0:
                    self.job.update(status='error', message='Die Qualitätsprüfung ist fehlgeschlagen. Details stehen im Prüfprotokoll.')
                else:
                    payload = read_json(folder/'report/manifest.json', {})
                    if payload.get('summary', {}).get('schema') != 'catalog_inventory_v1':
                        raise ValueError('Keine vollständige Qualitätsliste erzeugt.')
                    atomic_json(self.directory/'current.json', dict(id=folder.name))
                    self.job.update(status='done', message='Vollständige Qualitätsliste aktualisiert.')
        except Exception as exc:
            with self.lock:
                if self.job['status'] == 'cancelling':
                    self.job.update(status='cancelled', message='Qualitätsprüfung abgebrochen. Die bisherige Liste bleibt erhalten.')
                else:
                    self.job.update(status='error', message=f'Qualitätsprüfung fehlgeschlagen: {exc}')
        finally:
            with self.lock:
                if self.job['status'] == 'cancelling':
                    self.job.update(status='cancelled', message='Qualitätsprüfung abgebrochen. Die bisherige Liste bleibt erhalten.')
                self.process = None
                self.job['finished'] = time.time()
                atomic_json(self.directory/'job.json', self.job)

    def cancel(self):
        with self.lock:
            if self.job['status'] not in {'running', 'cancelling'}:
                return self.snapshot()
            self.job.update(status='cancelling', message='Qualitätsprüfung wird abgebrochen …')
            atomic_json(self.directory/'job.json', self.job)
            process = self.process
        if process is not None:
            self.stop_process(process)
        return self.snapshot()

    def close(self):
        with self.lock:
            self.closed = True
        self.cancel()
        if self.thread is not None:
            self.thread.join(timeout=20)

    def asset(self, relative):
        # Only published inventory assets may be served, never arbitrary files.
        allowed = set()
        for row in self.payload()['rows']:
            if row['status'] == 'reserved':
                continue
            allowed.add(row['image'])
            for candidate in row['candidates']:
                allowed.add(candidate['svg'])
            archive = row.get('archive', {})
            if archive.get('evidence_exists'):
                allowed.add(archive['evidence'])
        target = (self.root/relative).resolve()
        if relative not in allowed or not target.is_relative_to(self.root):
            raise CatalogError('Unzulässige Katalogdatei.', 403)
        return target

    def export_csv(self):
        buffer = io.StringIO(newline='')
        fields = ['filename','status','archived','normalized_mse','edge_alignment','foreground_iou',
                  'failures','image','svg','description','semantic_revalidated','measured_at',
                  'geometry_class','geometry_subclass','class_label','class_basis','class_observation','description_issue','model_limit']
        writer = csv.DictWriter(buffer, fields)
        writer.writeheader()
        for row in self.payload()['rows']:
            candidate = row.get('selected') or {}
            measurement = candidate.get('measurement', {})
            renderers = measurement.get('renderers', {})
            metrics = [r.get('metrics', {}) for r in renderers.values()]
            def worst(key, fn):
                values = [m[key] for m in metrics if key in m]
                return fn(values) if values else ''
            failures = [name+': '+str(r.get('error') or ', '.join(r.get('failures', [])))
                        for name,r in renderers.items() if r.get('error') or r.get('failures')]
            if measurement.get('error'):
                failures.append(measurement['error'])
            classification = row.get('classification', {})
            writer.writerow(dict(filename=row['filename'], status=row['status'], archived=row['archived'],
                normalized_mse=worst('normalized_mse', max), edge_alignment=worst('edge_alignment', min),
                foreground_iou=worst('foreground_iou', min), failures='; '.join(failures),
                image=row['image'], svg=candidate.get('svg', ''), description=row['description'],
                semantic_revalidated=row['semantic_revalidated'], measured_at=measurement.get('measured_at',''),
                geometry_class=classification.get('class_id',''), geometry_subclass=classification.get('subclass_id',''),
                class_label=classification.get('label',''), class_observation=classification.get('reason',''),
                class_basis=classification.get('basis',''), description_issue=classification.get('description_issue',''),
                model_limit=classification.get('model_limit','')))
        return ('\ufeff'+buffer.getvalue()).encode('utf-8')
