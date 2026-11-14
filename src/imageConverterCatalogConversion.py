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


def checked_attempt(attempt, row):
    """Judge this attempt's SVG, independently of an older passing candidate."""
    from tools.build_catalog_inventory import classify
    candidate = next((c for c in row.get('candidates', [])
                      if c.get('svg_sha256') == attempt.get('svg_sha256')), None) if attempt.get('result') else None
    measurement = candidate.get('measurement', {}) if candidate else {}
    passed = bool(candidate and classify(measurement) == 'pixel_pass') if candidate or not attempt.get('result') else None
    return dict(attempt, passed=passed, checking=False, measurement=measurement,
                catalog_passed=row.get('status') == 'pixel_pass')


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
        self._index_rows = None
        self._quality_index = []
        self.state = read_json(self.directory/'state.json', dict(status='idle', message='Hintergrunddienst ist gestoppt.'))
        if self.state['status'] in {'running', 'stopping'}:
            self.state.update(status='interrupted', phase='idle',
                              message='Hintergrunddienst beim Serverende unterbrochen. Er kann erneut gestartet werden.')
            self._save()
        if not self.state.get('last_attempt') and (self.state.get('job_id') or self.state.get('history')):
            try:
                previous = (self.state.get('history') or [{}])[-1]
                job = self.jobs.snapshot(self.state.get('job_id') or previous['job_id'])
                if not job.get('result') and previous.get('job_id'):
                    job = self.jobs.snapshot(previous['job_id'])
                last = dict(filename=job['name'],job_id=job['id'],status=job['status'],message=job['message'],
                            round=self.state.get('round',1),attempt=self.state.get('attempt',1),
                            result=bool(job.get('result')),checking=False)
                if last['result']:
                    last['svg_sha256'] = hashlib.sha256((self.jobs.folder(job['id'])/'result.svg').read_bytes()).hexdigest()
                row = next((r for r in self.catalog.payload()['rows'] if r['filename'] == last['filename']), {})
                self.state['last_attempt'] = checked_attempt(last, row)
                self._save()
            except (OSError, ValueError, KeyError):
                pass

    def _save(self):
        atomic_json(self.directory/'state.json', self.state)

    def _update(self, **values):
        with self.lock:
            self.state.update(values)
            self._save()

    def _ranked(self):
        payload = self.catalog.payload()
        rows = payload['rows']
        if rows is not self._index_rows or not payload.get('summary'):
            self._quality_index = sorted(((order, row) for row in rows
                if (order := failure_order(row)) is not None), key=lambda item:item[0])
            self._index_rows = rows
        return self._quality_index

    def snapshot(self):
        with self.lock:
            result = dict(self.state)
        job_id = result.get('job_id')
        if job_id:
            result['job'] = self.jobs.snapshot(job_id)
        counts = dict(result.get('failure_counts', {}))
        pending = result.get('last_attempt') or {}
        conditional = result.get('status') == 'running' and (result.get('phase') == 'convert' or pending.get('checking'))
        if conditional and result.get('filename'):
            counts[result['filename'].casefold()] = result.get('attempt', 1)
        ranked = self._ranked()
        candidates = [(order, row) for order, row in ranked if counts.get(row['filename'].casefold(), 0) < MAX_FAILURES]
        round_number = result.get('round', 1)
        if ranked and not candidates:
            candidates, counts, round_number = ranked, {}, round_number+1
        result['next'] = None
        if candidates:
            order, row = candidates[0]
            result['next'] = dict(filename=row['filename'], image=row['image'], mse=order[0],
                round=round_number, attempt=counts.get(row['filename'].casefold(), 0)+1,
                provisional=result.get('phase') == 'refresh', conditional=conditional)
        result['inspection'] = None
        result['log'] = (result.get('job') or {}).get('log', '')
        if result.get('phase') == 'refresh':
            inspection = self.catalog.snapshot()
            result['inspection'] = {key:inspection.get(key) for key in ('id','status','message','progress')}
            result['inspection']['elapsed'] = round(time.time()-inspection.get('started',time.time()),1)
            log = self.catalog.directory/inspection.get('id','')/'console.log'
            if log.is_file():
                with log.open('rb') as stream:
                    stream.seek(max(0, log.stat().st_size-16000))
                    result['log'] = stream.read().decode('utf-8',errors='replace')
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
            last_attempt = self.state.get('last_attempt')
            self.state = dict(id=uuid.uuid4().hex, status='running', phase='refresh', profile=profile,
                              started=time.time(), completed=0, passed=0, failed=0, history=[],
                              round=round_number, failure_counts=failure_counts, deferred=[],
                              last_attempt=last_attempt,
                              message='Gespeicherte Qualitätsrangliste wird geladen …')
            self._save()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        return self.snapshot()

    def _refresh(self):
        last = self.state.get('last_attempt') or {}
        pending = last.get('result') and last.get('passed') is None
        if not pending and self.catalog.payload().get('summary'):
            return not self.stop.is_set()
        if pending:
            job = self.jobs.snapshot(last['job_id'])
            row = next(r for r in self.catalog.payload()['rows'] if r['filename'] == last['filename'])
            candidate = self._preserve(row, job)
            message = f"Prüfe nur das neue SVG für {last['filename']} …"
        else:
            candidate = None
            message = 'Noch keine Qualitätsliste vorhanden. Einmalige Bestandsaufnahme …'
        self._update(phase='refresh', message=message)
        with self.lock:
            if self.stop.is_set():
                return False
            if candidate is None:
                self.catalog.start(owner=self)
            else:
                self.catalog.start(owner=self, filename=last['filename'], candidate=candidate)
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
        return target

    def _run(self):
        try:
            if not self._refresh():
                return
            last = self.state.get('last_attempt')
            if last and last.get('passed') is None:
                row = next((r for r in self.catalog.payload()['rows'] if r['filename'] == last['filename']), {})
                last = checked_attempt(last,row)
                if last.get('accounted') is False:
                    self._record_attempt(last)
                else:
                    self._update(last_attempt=last)
            while not self.stop.is_set():
                ranked = self._ranked()
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
                order, row = candidates[0]
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
                last = dict(filename=row['filename'], job_id=job['id'], status=job['status'],
                    result=bool(job.get('result')), message=job['message'],
                    round=self.state['round'], attempt=attempt, finished=time.time(),
                    passed=None, checking=True, accounted=False)
                if last['result']:
                    last['svg_sha256'] = hashlib.sha256((self.jobs.folder(job['id'])/'result.svg').read_bytes()).hexdigest()
                self._update(last_attempt=last)
                if last['result'] and not self._refresh():
                    return
                current = next((r for r in self.catalog.payload()['rows'] if r['filename'] == row['filename']), {})
                last = checked_attempt(last, current)
                self._record_attempt(last)
        except Exception as exc:
            if not self.stop.is_set():
                self._update(status='error', phase='idle', message=f'Hintergrunddienst fehlgeschlagen: {exc}')
        finally:
            with self.lock:
                if self.stop.is_set():
                    self.state.update(status='stopped', phase='idle', message='Hintergrunddienst gestoppt.')
                last = self.state.get('last_attempt')
                if last and last.get('checking'):
                    self.state['last_attempt'] = dict(last, checking=False, passed=None,
                        message=last['message']+' Die anschließende Qualitätsprüfung wurde unterbrochen.')
                self.state['finished'] = time.time()
                self._save()
            with self.catalog.lock:
                self.catalog.conversion_owner = None

    def _record_attempt(self, last):
        """Commit the checklist once, also after interrupted validation resumes."""
        with self.lock:
            counts = dict(self.state['failure_counts'])
            name = last['filename'].casefold()
            if last['catalog_passed']:
                counts.pop(name, None)
            else:
                counts[name] = last['attempt']
            deferred = [r['filename'] for _, r in self._ranked()
                        if counts.get(r['filename'].casefold(), 0) >= MAX_FAILURES]
            passed = last['passed']
            history = [*self.state['history'], dict(filename=last['filename'], job_id=last['job_id'],
                passed=passed, status=last['status'], message=last['message'], finished=last['finished'],
                round=last['round'], attempt=last['attempt'],
                deferred=not last['catalog_passed'] and last['attempt'] >= MAX_FAILURES)]
            self._update(completed=self.state['completed']+1, passed=self.state['passed']+int(bool(passed)),
                failed=self.state['failed']+int(not passed), history=history[-200:],
                failure_counts=counts, deferred=deferred, last_attempt=dict(last, accounted=True))

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
