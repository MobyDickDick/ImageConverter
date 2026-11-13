"""Pinned category examples, loaded as ordinary fresh GUI conversion inputs.

Saved SVG checks are evidence only. They never seed a new conversion. New
attempts and Plan-B handoffs use the existing Jobs/Workbench quality contract.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from src.imageConverterCatalog import CatalogError
from src.imageConverterClasses import CLASSES


class CategoryCollection:
    def __init__(self, root, catalog, jobs):
        self.root, self.catalog, self.jobs = Path(root).resolve(), catalog, jobs

    def selection(self):
        path = self.root/'config/catalog_conversion_collection.json'
        if not path.is_file():
            return dict(title='Kategorien-Kollektion', cases=[])
        data = json.loads(path.read_text(encoding='utf-8'))
        cases = data.get('cases', [])
        if (not isinstance(cases, list) or any(not isinstance(c, dict) for c in cases)
                or len({c.get('id') for c in cases}) != len(cases)
                or len({c.get('filename', '').casefold() for c in cases}) != len(cases)
                or any(not re.fullmatch(r'[a-z_]{1,64}', c.get('id', ''))
                       or c['id'] not in CLASSES or c['id'] in {'complex_photo','reserved','unresolved'}
                       for c in cases)):
            raise CatalogError('Die Kategorien-Kollektion ist ungültig.', 500)
        return data

    def _source(self, choice, row):
        if row is None or row.get('role') != 'catalog':
            raise CatalogError('Das ausgewählte Katalogbild fehlt.', 409)
        if row.get('status') in {'reserved','source_conflict'}:
            raise CatalogError('Dieses Bild ist reserviert oder hat widersprüchliche Quellen.', 409)
        if row.get('classification', {}).get('class_id') != choice['id']:
            raise CatalogError('Die Bildzuordnung hat sich geändert. Bitte die Kollektion aktualisieren.', 409)
        source = (self.root/row['image']).resolve()
        if not source.is_relative_to(self.root) or not source.is_file():
            raise CatalogError('Die Quelldatei ist nicht verfügbar.', 409)
        data = source.read_bytes()
        if (hashlib.sha256(data).hexdigest() != choice.get('image_sha256')
                or row.get('image_sha256') != choice.get('image_sha256')):
            raise CatalogError('Das Originalbild hat sich seit der Auswahl verändert.', 409)
        return data

    @staticmethod
    def _job_info(job):
        return {key: job.get(key) for key in ('id','status','quality','result','created','message','workbench_id')}

    def payload(self):
        selection = self.selection()
        catalog = self.catalog.payload()
        by_name = {r['filename'].casefold():r for r in catalog['rows']}
        groups = catalog['summary'].get('geometry_classes', {}).get('classes', {})
        cases = []
        with self.jobs.lock:
            jobs = list(self.jobs.jobs.values())
        for choice in selection['cases']:
            row = by_name.get(choice['filename'].casefold())
            problem = None
            try:
                self._source(choice, row)
            except (CatalogError, OSError) as exc:
                problem = str(exc)
            attempts = sorted((j for j in jobs if j.get('collection_case_id') == choice['id']
                and j.get('collection_image_sha256') == choice.get('image_sha256')),
                key=lambda j:j['created'], reverse=True)
            passed = next((j for j in attempts if j.get('status') == 'done'
                and j.get('quality') == 'passed' and j.get('result')), None)
            planned = next((j for j in attempts if j.get('status') == 'done'
                and j.get('quality') == 'passed' and j.get('result') and j.get('workbench_id')), None)
            group = groups.get(choice['id'], {})
            evidence = (row or {}).get('selected') or {}
            # An old filename alone cannot vouch for today's saved SVG bytes.
            evidence_matches = False
            if evidence.get('svg') and not problem:
                svg = (self.root/evidence['svg']).resolve()
                evidence_matches = (svg.is_relative_to(self.root) and svg.is_file()
                    and hashlib.sha256(svg.read_bytes()).hexdigest() == evidence.get('svg_sha256'))
            cases.append(dict(id=choice['id'], label=CLASSES[choice['id']][0], filename=choice['filename'],
                available=problem is None, problem=problem, image=row['image'] if row and not problem else None,
                observation=(row or {}).get('classification', {}).get('reason', ''),
                description=(row or {}).get('description', ''),
                description_issue=(row or {}).get('classification', {}).get('description_issue'),
                selection_note=choice.get('note', ''), category_size=group.get('total', 0),
                category_saved_passes=group.get('saved_pixel_pass', 0),
                selected_saved_pass=bool(row and row.get('status') == 'pixel_pass' and evidence_matches),
                saved_svg=evidence.get('svg') if evidence_matches else None,
                attempt_count=len(attempts), latest_job=self._job_info(attempts[0]) if attempts else None,
                passed_job=self._job_info(passed) if passed else None,
                plan_b_job=self._job_info(planned) if planned else None))
        return dict(title=selection.get('title', 'Kategorien-Kollektion'), cases=cases,
            summary=dict(categories=len(cases), available=sum(c['available'] for c in cases),
                categories_with_saved_pass=sum(c['category_saved_passes'] > 0 for c in cases),
                fresh_passes=sum(bool(c['passed_job']) for c in cases),
                prepared_plan_b=sum(bool(c['plan_b_job']) for c in cases),
                quality_snapshot=catalog['summary'].get('generated_at'),
                excluded_classes=['complex_photo','reserved','unresolved']))

    def load(self, case_id, *, fresh=False):
        if type(fresh) is not bool:
            raise CatalogError('Ungültige Auswahl für einen neuen Versuch.')
        selection = self.selection()
        choice = next((c for c in selection['cases'] if c['id'] == case_id), None)
        if choice is None:
            raise CatalogError('Dieses Kategorienbeispiel wurde nicht gefunden.', 404)
        row = next((r for r in self.catalog.payload()['rows'] if r['filename'].casefold() == choice['filename'].casefold()), None)
        data = self._source(choice, row)
        with self.jobs.lock:
            # Returning to the collection must not create duplicate ready jobs.
            existing = sorted((j for j in self.jobs.jobs.values()
                if j.get('collection_case_id') == case_id
                and j.get('collection_image_sha256') == choice['image_sha256']),
                key=lambda j:j['created'], reverse=True)
            if existing and not fresh:
                return self.jobs.snapshot(existing[0]['id'])
            if any(j['status'] == 'running' for j in self.jobs.jobs.values()):
                raise CatalogError('Bitte die laufende Konvertierung zuerst abschließen oder abbrechen.', 409)
            job = self.jobs.upload(choice['filename'], data)
            stored = self.jobs.jobs[job['id']]
            # The generic uploader merges several tables; this selection is
            # pinned to the primary catalog row shown on its example card.
            # Preserve an explicit user correction on later attempts.
            if stored.get('description_origin') != 'user':
                stored.update(description=row.get('description', ''), description_origin='catalog')
            index = selection['cases'].index(choice)
            stored.update(collection_case_id=case_id, collection_image_sha256=choice['image_sha256'],
                          collection_label=CLASSES[case_id][0],
                          collection_next_case_id=selection['cases'][index+1]['id'] if index+1 < len(selection['cases']) else None)
            self.jobs.save(stored)
            return self.jobs.snapshot(job['id'])
