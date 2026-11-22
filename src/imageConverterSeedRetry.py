"""Server-owned, sequential seed retries with an immutable best observation."""
from __future__ import annotations

import secrets
import shutil


class SeedRetry:
    def __init__(self, jobs):
        self.jobs = jobs
        # A server restart stops the loop; it must never silently restart work.
        for job in jobs.jobs.values():
            session = job.get('seed_retry')
            if session and session['active']:
                session.update(active=False, message='Automatische Fortsetzung durch Serverende unterbrochen.')
                jobs.save(job)

    def session(self, job_id):
        job = self.jobs.jobs[job_id]
        root = self.jobs.jobs.get(job.get('seed_retry_root'), {})
        return root.get('seed_retry')

    def busy(self, exclude=None):
        return any(job.get('seed_retry', {}).get('active') and job['id'] != exclude
                   for job in self.jobs.jobs.values())

    def toggle(self, job_id, description, profile, *, seed=None, use_current_svg=True):
        jobs = self.jobs
        with jobs.lock:
            jobs.folder(job_id)
            session = self.session(job_id)
            if session and session['active']:
                return self.stop(job_id)
            job = jobs.jobs[job_id]
            if job.get('catalog_background'):
                from src.imageConverterGui import RequestError
                raise RequestError('Die automatische Fortsetzung gehört zur Einzelkonvertierung.', 409)
            if job['status'] != 'running':
                job = jobs.jobs[jobs.start(job_id, description, profile, seed=seed,
                                          use_current_svg=use_current_svg)['id']]
            root_id = job['id']
            job['seed_retry_root'] = root_id
            job['seed_retry'] = dict(active=True, root_id=root_id, current_job_id=root_id,
                                     best_job_id=None, attempts=1, message='Automatische Fortsetzung aktiv.')
            jobs.save(job)
            return jobs.snapshot(root_id)

    def stop(self, job_id):
        jobs = self.jobs
        with jobs.lock:
            session = self.session(job_id)
            if not session:
                return jobs.cancel(job_id)
            session.update(active=False, message='Automatische Fortsetzung beendet.')
            jobs.save(jobs.jobs[session['root_id']])
            current_id = session['current_job_id']
            jobs.cancel(current_id)
            self.consider(current_id, session)
            return jobs.snapshot(session.get('best_job_id') or current_id)

    def consider(self, job_id, session):
        from src.imageConverterGui import saved_svg_quality, result_description_error, vector_comparison_score
        jobs = self.jobs
        candidate = jobs.export_file(job_id, include_retry=False)
        if candidate is None:
            return
        job = jobs.jobs[job_id]
        quality = saved_svg_quality(jobs.folder(job_id)/'source.png', candidate)
        if not quality or (quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']):
            return
        error = result_description_error(candidate, job['description'])
        rank = (bool(error), not quality['passed'], vector_comparison_score(quality))
        if session.get('best_rank') is not None and rank >= tuple(session['best_rank']):
            return
        # Freeze previews as well: cancellation or worker cleanup may replace them.
        target = jobs.folder(session['root_id'])/'seed-best.svg'
        temporary = target.with_suffix('.svg.tmp')
        shutil.copyfile(candidate, temporary)
        temporary.replace(target)
        session.update(best_job_id=job_id, best_rank=rank, best_quality=quality,
                       best_description_error=error, best_seed=str(job['search_seed']),
                       best_revision=target.stat().st_mtime_ns)
        jobs.save(jobs.jobs[session['root_id']])

    def finished(self, job_id):
        jobs = self.jobs
        with jobs.lock:
            session = self.session(job_id)
            if not session or session['current_job_id'] != job_id:
                return
            try:
                self.consider(job_id, session)
                if not session['active'] or jobs.closed:
                    session['active'] = False
                    return
                job = jobs.jobs[job_id]
                seed = secrets.randbits(64)
                if seed == job['search_seed']:
                    seed ^= 1
                # A fresh seed must explore a fresh construction, rather than
                # immediately accept the same already satisfactory sample.
                jobs.start(job_id, job['description'], job['profile'], seed=seed,
                           use_current_svg=False, _retry_root=session['root_id'])
            except Exception as exc:
                session.update(active=False, message=f'Automatische Fortsetzung beendet: {exc}')
            finally:
                jobs.save(jobs.jobs[session['root_id']])
