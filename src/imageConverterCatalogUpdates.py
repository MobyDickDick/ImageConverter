"""Reconcile successful manual GUI results with the measured catalog."""
from __future__ import annotations

import hashlib
from pathlib import Path
import queue
import threading


class CatalogUpdates:
    def __init__(self, catalog, jobs):
        self.catalog, self.jobs = catalog, jobs
        self.pending = queue.Queue()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        jobs.on_result = self.submit
        self.thread.start()
        # Catch up successful attempts saved before this feature, or a restart.
        for job_id in list(jobs.jobs):
            self.submit(job_id)

    def submit(self, job_id):
        with self.jobs.lock:
            job = self.jobs.jobs[job_id]
            if (self.stop.is_set() or job.get('catalog_background') or job.get('status') != 'done'
                    or not job.get('result') or job.get('quality') != 'passed'
                    or job.get('catalog_update', {}).get('status') in {'done', 'skipped'}):
                return
            job['catalog_update'] = dict(status='queued', message='Ergebnis wird in der Qualitätsliste nachgetragen …')
            self.jobs.save(job)
            self.pending.put(job_id)

    def _state(self, job_id, **state):
        with self.jobs.lock:
            self.jobs.jobs[job_id]['catalog_update'] = state
            self.jobs.save(self.jobs.jobs[job_id])

    def _candidate(self, job_id):
        from PIL import Image, ImageOps

        with self.jobs.lock:
            job = dict(self.jobs.jobs[job_id])
            folder = self.jobs.folder(job_id)
        row = next((r for r in self.catalog.payload()['rows']
                    if r['filename'].casefold() == job['name'].casefold()), None)
        if not row or row['role'] != 'catalog' or row['status'] in {'reserved', 'source_conflict'}:
            return None
        source = (self.catalog.root/row['image']).resolve()
        if not source.is_relative_to(self.catalog.root):
            raise ValueError('Ungültiger Katalogpfad.')
        if hashlib.sha256(source.read_bytes()).hexdigest() != row['image_sha256']:
            raise ValueError('Das Katalogoriginal wurde verändert.')
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert('RGBA')
            normalized = Image.new('RGB', image.size, 'white')
            normalized.paste(image, mask=image.getchannel('A'))
        with Image.open(folder/'source.png') as uploaded:
            if uploaded.size != normalized.size or uploaded.convert('RGB').tobytes() != normalized.tobytes():
                raise ValueError('Das hochgeladene Bild entspricht nicht dem Katalogoriginal.')
        candidate = self.catalog.root/'artifacts/converted_images/catalog_manual_svgs'/job_id/(Path(row['filename']).stem+'.svg')
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes((folder/'result.svg').read_bytes())
        return row['filename'], source, candidate

    def _run(self):
        from tools.build_catalog_inventory import QualityWorker

        worker = QualityWorker()
        try:
            while not self.stop.is_set():
                job_id = self.pending.get()
                if job_id is None or self.stop.is_set():
                    break
                try:
                    candidate = self._candidate(job_id)
                    if candidate is None:
                        self._state(job_id, status='skipped', message='Kein freigegebenes Katalogoriginal zugeordnet.')
                        continue
                    filename, source, svg = candidate
                    self._state(job_id, status='checking', message='Qualitätsliste: neues SVG wird mit beiden Renderern geprüft …')
                    measurement = worker.measure(source, svg)
                    if self.stop.is_set():
                        break
                    status = self.catalog.record_manual_candidate(filename, svg, measurement)
                    self._state(job_id, status='done', catalog_status=status,
                                message='Qualitätsliste aktualisiert: '+('Rastergates erfüllt.' if status == 'pixel_pass'
                                        else 'Ergebnis nachgetragen; Rasterprüfung noch nicht bestanden.'))
                except Exception as exc:
                    self._state(job_id, status='error', message=f'Nachtrag in die Qualitätsliste fehlgeschlagen: {exc}')
        finally:
            worker.close()

    def close(self):
        self.stop.set()
        self.pending.put(None)
        self.thread.join(timeout=40)
