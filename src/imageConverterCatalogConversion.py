"""Sequential, stoppable retries of the best measured failing catalog images."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import threading
import time
import uuid

from src.imageConverterCatalog import CatalogError, atomic_json, read_json

MAX_FAILURES = 3


def failure_order(row):
    """Use the same worst-renderer MSE as the catalog's candidate selection."""
    if row.get('role') != 'catalog' or row.get('status') != 'pixel_fail':
        return None
    renderers = (row.get('selected') or {}).get('measurement', {}).get('renderers', {})
    values = [renderers.get(name, {}).get('metrics', {}).get('normalized_mse')
              for name in ('mupdf', 'librsvg')]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        return None
    if not row.get('description', '').strip():
        return None
    return max(values), row['filename'].casefold()


class CatalogConversion:
    def __init__(self, catalog, jobs, workbench):
        self.catalog, self.jobs, self.workbench = catalog, jobs, workbench
        self.directory = catalog.directory/'conversion-service'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.thread = None
        self.closed = False
        self.state = read_json(self.directory/'state.json', dict(status='idle', message='Hintergrunddienst ist gestoppt.'))
        if self.state['status'] in {'running', 'stopping'}:
            self.state.update(status='interrupted', phase='idle',
                              message='Hintergrunddienst beim Serverende unterbrochen. Er kann erneut gestartet werden.')
            self._save()

    def _save(self):
        atomic_json(self.directory/'state.json', self.state)

    def _update(self, **values):
        with self.lock:
            self.state.update(values)
            self._save()

    def snapshot(self):
        with self.lock:
            result = dict(self.state)
        job_id = result.get('job_id')
        if job_id:
            result['job'] = self.jobs.snapshot(job_id)
        return result

    def start(self, profile='normal'):
        if not isinstance(profile, str) or profile not in {'quick', 'normal', 'thorough'}:
            raise CatalogError('Unbekanntes Suchprofil.')
        with self.lock:
            if self.closed:
                raise CatalogError('Der Server wird beendet.', 409)
            if self.thread is not None and self.thread.is_alive():
                raise CatalogError('Der Hintergrunddienst läuft bereits.', 409)
            with self.catalog.lock:
                if self.catalog.thread is not None and self.catalog.thread.is_alive():
                    raise CatalogError('Bitte zuerst die laufende Qualitätsprüfung beenden.', 409)
                self.catalog.conversion_owner = self
            self.stop.clear()
            round_number = self.state.get('round', 1)
            failure_counts = dict(self.state.get('failure_counts', {}))
            self.state = dict(id=uuid.uuid4().hex, status='running', phase='refresh', profile=profile,
                              started=time.time(), completed=0, passed=0, failed=0, history=[],
                              round=round_number, failure_counts=failure_counts, deferred=[],
                              message='Aktuelle Qualitätsliste wird vor der Auswahl geprüft …')
            self._save()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        return self.snapshot()

    def _refresh(self):
        self._update(phase='refresh', message='Qualitätsliste wird aktualisiert …')
        with self.lock:
            if self.stop.is_set():
                return False
            self.catalog.start(owner=self)
        while self.catalog.thread.is_alive():
            if self.stop.wait(.2):
                self.catalog.cancel()
                self.catalog.thread.join(timeout=20)
                return False
        if self.catalog.snapshot()['status'] != 'done':
            raise CatalogError('Die Qualitätsprüfung ist fehlgeschlagen. Siehe Prüfprotokoll.')
        return not self.stop.is_set()

    def _source(self, row):
        source = (self.catalog.root/row['image']).resolve()
        if not source.is_relative_to(self.catalog.root) or not source.is_file():
            raise CatalogError('Die Quelldatei ist nicht verfügbar.')
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != row.get('image_sha256'):
            raise CatalogError('Das Originalbild hat sich seit der Qualitätsprüfung verändert.')
        return data

    def _launch(self, row):
        # This lock is shared with the manual GUI and Workbench start paths.
        # Let an existing foreground conversion finish before taking its slot.
        with self.jobs.lock:
            if self.workbench.busy() or any(j['status'] == 'running' for j in self.jobs.jobs.values()):
                return None
            data = self._source(row)
            job = self.jobs.upload(row['filename'], data)
            stored = self.jobs.jobs[job['id']]
            stored.update(catalog_background=True, description=row['description'], description_origin='catalog')
            self.jobs.save(stored)
            result = self.jobs.start(job['id'], row['description'], self.state['profile'])
            stored['description_origin'] = 'catalog'
            self.jobs.save(stored)
            return result

    def _preserve(self, row, job):
        if not job.get('result'):
            return
        # Keep every attempt, including drafts. Both catalog renderers decide
        # admission; old candidates are never overwritten or discarded.
        folder = self.catalog.root/'artifacts/converted_images/catalog_background_svgs'/job['id']
        folder.mkdir(parents=True, exist_ok=True)
        target = folder/(Path(row['filename']).stem+'.svg')
        temporary = target.with_suffix('.tmp')
        temporary.write_bytes((self.jobs.folder(job['id'])/'result.svg').read_bytes())
        temporary.replace(target)

    def _run(self):
        try:
            if not self._refresh():
                return
            while not self.stop.is_set():
                rows = self.catalog.payload()['rows']
                ranked = [(order, r) for r in rows if (order := failure_order(r)) is not None]
                if not ranked:
                    self._update(status='done', phase='idle',
                                 failure_counts={}, deferred=[],
                                 message='Keine bewertbaren Bilder mit verfehlten Rastergates mehr vorhanden.')
                    return
                names = {r['filename'].casefold() for _, r in ranked}
                counts = {name: count for name, count in self.state['failure_counts'].items() if name in names}
                candidates = [(order, r) for order, r in ranked
                              if counts.get(r['filename'].casefold(), 0) < MAX_FAILURES]
                if not candidates:
                    # Every remaining failing image has exhausted this round.
                    # Release all deferrals together, then rank afresh.
                    counts = {}
                    self._update(round=self.state['round']+1, failure_counts={}, deferred=[],
                                 message='Alle offenen Bilder dreimal versucht. Neue Runde beginnt …')
                    candidates = ranked
                deferred = [r['filename'] for _, r in ranked
                            if counts.get(r['filename'].casefold(), 0) >= MAX_FAILURES]
                order, row = min(candidates, key=lambda item:item[0])
                name = row['filename'].casefold()
                attempt = counts.get(name, 0)+1
                with self.lock:
                    if self.stop.is_set():
                        return
                    self._update(phase='waiting', filename=row['filename'], mse=order[0],
                                 attempt=attempt, failure_counts=counts, deferred=deferred,
                                 job_id=None, remaining=len(candidates), message='Warte auf einen freien Konvertierungsplatz …')
                    job = self._launch(row)
                    if job:
                        self._update(phase='convert', job_id=job['id'], message=f"Konvertiere {row['filename']} …")
                if job is None:
                    self.stop.wait(.5)
                    continue
                while True:
                    with self.jobs.lock:
                        busy = (self.jobs.jobs[job['id']]['status'] == 'running'
                                or job['id'] in self.jobs.processes)
                    if not busy:
                        break
                    if self.stop.wait(.2):
                        self.jobs.cancel(job['id'])
                        return
                if self.stop.is_set():
                    return
                job = self.jobs.snapshot(job['id'])
                self._preserve(row, job)
                if not self._refresh():
                    return
                current = next((r for r in self.catalog.payload()['rows'] if r['filename'] == row['filename']), {})
                passed = current.get('status') == 'pixel_pass'
                with self.lock:
                    if passed:
                        counts.pop(name, None)
                    else:
                        counts[name] = attempt
                    deferred = [r['filename'] for _, r in ranked
                                if counts.get(r['filename'].casefold(), 0) >= MAX_FAILURES]
                    history = [*self.state['history'], dict(filename=row['filename'], job_id=job['id'],
                        passed=passed, status=job['status'], message=job['message'], finished=time.time(),
                        round=self.state['round'], attempt=attempt, deferred=not passed and attempt >= MAX_FAILURES)]
                    self._update(completed=self.state['completed']+1, passed=self.state['passed']+int(passed),
                                 failed=self.state['failed']+int(not passed), history=history[-200:],
                                 failure_counts=counts, deferred=deferred)
        except Exception as exc:
            if not self.stop.is_set():
                self._update(status='error', phase='idle', message=f'Hintergrunddienst fehlgeschlagen: {exc}')
        finally:
            with self.lock:
                if self.stop.is_set():
                    self.state.update(status='stopped', phase='idle', message='Hintergrunddienst gestoppt.')
                self.state['finished'] = time.time()
                self._save()
            with self.catalog.lock:
                self.catalog.conversion_owner = None

    def cancel(self):
        with self.lock:
            if self.thread is None or not self.thread.is_alive():
                return self.snapshot()
            self.stop.set()
            self._update(status='stopping', message='Hintergrunddienst wird gestoppt …')
            job_id = self.state.get('job_id') if self.state.get('phase') == 'convert' else None
        if job_id:
            self.jobs.cancel(job_id)
        if self.state.get('phase') == 'refresh':
            self.catalog.cancel()
        return self.snapshot()

    def close(self):
        with self.lock:
            self.closed = True
        self.cancel()
        if self.thread is not None:
            self.thread.join(timeout=25)
