"""Local browser GUI for the existing semantic-only converter.

Run with ``python -m src.imageConverterGui`` or startWebServer.cmd.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from urllib.request import ProxyHandler, Request, build_opener
import uuid
import warnings
import webbrowser
import zipfile

from src.imageConverterCatalog import CatalogError, CatalogQuality, atomic_json
from src.imageConverterCatalogConversion import CatalogConversion
from src.imageConverterCatalogUpdates import CatalogUpdates
from src.imageConverterCollection import CategoryCollection
from src.iCCModules.imageCompositeConverterSimilarity import resolve_similarity_description, SimilarityReferenceError

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
MAX_UPLOAD = 25 * 1024 * 1024
MAX_PIXELS = 20_000_000
# Leave room after the 30-second effort floor for model comparison/finalization.
PROFILES = {"quick": (35, 45), "normal": (60, 120), "thorough": (120, 240),
            "explore5": (300, 315), "explore10": (600, 615)}
DESCRIPTION_VALIDATION_VERSION = 15


class RequestError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def catalog_descriptions() -> dict[str, str]:
    from src.iCCModules.imageCompositeConverterDescriptions import loadCatalogDescriptionMappingImpl

    return loadCatalogDescriptionMappingImpl(ROOT)


def find_svg_description(name: str) -> dict:
    """Look in the same maintained tables and sidecars as the Plan-B runner."""
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl

    if not isinstance(name, str):
        raise ValueError('Bitte einen gültigen SVG-Dateinamen angeben.')
    name = name.replace('\\', '/').rsplit('/', 1)[-1]
    stem = re.sub(r'_PlanB$', '', Path(name).stem, flags=re.I)
    sources = [ROOT / 'artifacts' / folder / 'Finale_Wurzelformen_V3.xml'
               for folder in ('images_to_convert', 'descriptions')]
    sidecar = ROOT / 'artifacts' / 'samples' / (stem + '.txt')
    searched = [str(p.relative_to(ROOT)) for p in (sidecar, *sources)]
    result = dict(description='', description_source=None, description_key=None,
                  description_searched=searched, description_warnings=[])
    if sidecar.is_file():
        text = sidecar.read_text(encoding='utf-8-sig').strip()
        if text:
            return dict(result, description=text, description_source=searched[0], description_key=stem)
    catalogs = []
    for path in sources:
        if path.is_file():
            try:
                mapping = loadDescriptionMappingImpl(str(path), get_base_name_from_file_fn=getBaseNameFromFileImpl)
                catalogs.append((path, {key.casefold(): value for key, value in mapping.items()}))
            except (ValueError, OSError) as exc:
                result['description_warnings'].append(f'{path.relative_to(ROOT)}: {exc}')
    # Prefer an image-specific match over a family fallback, even if only the
    # secondary table has that specific image. Keep Plan-B's primary table first.
    for key in dict.fromkeys((Path(name).stem, stem, getBaseNameFromFileImpl(stem))):
        for path, mapping in catalogs:
            description = mapping.get(key.casefold(), '').strip()
            if description:
                return dict(result, description=description,
                            description_source=str(path.relative_to(ROOT)), description_key=key)
    return result


def stop_process_tree(process: subprocess.Popen) -> None:
    # The converter creates render/search children; stopping only its parent leaks them.
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW, timeout=15, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=15)


def write_description_table(path: Path, description: str, catalog: dict[str, str]) -> None:
    # Keep referenced catalog descriptions available to the existing parser.
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Wurzelform", "Beschreibung"])
        writer.writerows(catalog.items())
        writer.writerow(["UPLOAD", description])


def save_file_dialog(source: Path, suggested_name: str, initial_directory: str = '', *,
                     file_filter: str = 'SVG-Vektorgrafik (*.svg)|*.svg', default_extension: str = 'svg') -> dict:
    if os.name != "nt":
        raise RequestError("Der System-Speicherdialog ist unter Windows verfügbar. Bitte den Browser-Download verwenden.")
    environment = os.environ.copy()
    environment.update(ICC_GUI_SOURCE=str(source), ICC_GUI_FILENAME=suggested_name,
                       ICC_GUI_INITIAL_DIRECTORY=initial_directory,
                       ICC_GUI_FILE_FILTER=file_filter, ICC_GUI_DEFAULT_EXTENSION=default_extension)
    script = (ROOT / "tools" / "save_svg_dialog.ps1").read_text(encoding="utf-8")
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-WindowStyle", "Hidden", "-Command", script],
            env=environment, stdin=subprocess.DEVNULL, capture_output=True,
            encoding="utf-8-sig", creationflags=subprocess.CREATE_NO_WINDOW, timeout=600,
        )
        result = json.loads(completed.stdout)
        if completed.returncode or result.get("error"):
            raise RequestError(f"Speichern fehlgeschlagen: {result.get('error', 'Systemdialog nicht verfügbar.')}")
        return result
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise RequestError("Der Speicherdialog konnte nicht geöffnet werden. Bitte den Browser-Download verwenden.") from exc


def save_svg_dialog(source: Path, suggested_name: str, initial_directory: str = '') -> dict:
    return save_file_dialog(source, suggested_name, initial_directory)


def open_file_dialog(kind: str, initial_directory: str) -> dict:
    if os.name != 'nt':
        raise RequestError('Der System-Dateidialog ist nur unter Windows verfügbar.')
    environment = dict(os.environ, ICC_GUI_PICKER_KIND=kind,
                       ICC_GUI_INITIAL_DIRECTORY=initial_directory)
    try:
        completed = subprocess.run(
            ['powershell.exe', '-NoProfile', '-STA', '-WindowStyle', 'Hidden', '-Command',
             (ROOT / 'tools/open_file_dialog.ps1').read_text(encoding='utf-8')],
            env=environment, stdin=subprocess.DEVNULL, capture_output=True,
            encoding='utf-8-sig', creationflags=subprocess.CREATE_NO_WINDOW, timeout=600)
        result = json.loads(completed.stdout)
        if completed.returncode or result.get('error'):
            raise RequestError(f"Dateiauswahl fehlgeschlagen: {result.get('error', 'Systemdialog nicht verfügbar.')}")
        return result
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise RequestError('Der Dateidialog konnte nicht geöffnet werden.') from exc


class Jobs:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.save_lock = threading.Lock()
        self.project_directory = ROOT / 'artifacts/converted_images'
        try:
            self.dialog_locations = json.loads((self.directory / 'dialog_locations.json').read_text(encoding='utf-8'))
            if not isinstance(self.dialog_locations, dict):
                self.dialog_locations = {}
        except (OSError, ValueError):
            self.dialog_locations = {}
        self.jobs: dict[str, dict] = {}
        self.processes: dict[str, subprocess.Popen] = {}
        self.manual_export_scans: dict[str, int] = {}
        self.threads: list[threading.Thread] = []
        self.closed = False
        self.on_result = None
        self.descriptions = catalog_descriptions()
        from src.imageConverterRecognition import ImageRecognition
        self.recognizer = ImageRecognition(ROOT)
        self.description_store = None
        # Keep recent results usable after a server restart.
        for path in self.directory.glob("*/job.json"):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
                if not re.fullmatch(r"[0-9a-f]{32}", job["id"]) or path.parent.name != job["id"]:
                    continue
                if job["status"] == "running":
                    job.update(status="interrupted", message="Der Server wurde während der Konvertierung beendet.")
                self.jobs[job["id"]] = job
                if job.get('result') and reject_raster_result(path.parent/'result.svg', job):
                    self.save(job)
                if (job.get('recovery') and job.get('status') == 'done' and job.get('result')
                        and job.get('description_validation_version') != DESCRIPTION_VALIDATION_VERSION
                        and job.get('recovery_validation_version') != DESCRIPTION_VALIDATION_VERSION):
                    collect_recovery_result(path.parent, job,
                        stop_reason=(job.get('recovery_report') or {}).get('stop_reason', 'worker_finished'))
                    # Rejected/missing recovery candidates return without updating
                    # description_validation_version. Remember the attempted check
                    # too, so every restart does not render the same old drafts.
                    job['recovery_validation_version'] = DESCRIPTION_VALIDATION_VERSION
                    self.save(job)
                if (job.get('quality') == 'passed' and job.get('result')
                        and ('pixel_quality' not in job or
                             (job.get('description_validation_version') != DESCRIPTION_VALIDATION_VERSION
                              and re.search(r'\bSVG-Bauteil\b', job.get('description', ''), re.I)))):
                    quality = saved_svg_quality(path.parent/'source.png', path.parent/'result.svg')
                    job['pixel_quality'] = quality
                    if quality and not quality['passed']:
                        job.update(quality='warning', message='Das gespeicherte SVG besteht die erneute Pixelprüfung nicht. Bitte den Entwurf prüfen oder ein Sample-SVG laden.')
                        if quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']:
                            job.update(status='error', result=False)
                    self.save(job)
                if (job.get('quality') == 'passed' and job.get('result')
                        and job.get('description_validation_version') != DESCRIPTION_VALIDATION_VERSION):
                    error = result_description_error(path.parent/'result.svg', job.get('description', ''))
                    job['description_validation_version'] = DESCRIPTION_VALIDATION_VERSION
                    if error:
                        job.update(quality='warning', description_error=error,
                                   message='Das gespeicherte SVG besteht die erneute Beschreibungsprüfung nicht. Bitte den Entwurf prüfen.')
                    self.save(job)
            except (OSError, ValueError, KeyError):
                continue

    def folder(self, job_id: str) -> Path:
        if job_id not in self.jobs:
            raise RequestError("Dieser Auftrag wurde nicht gefunden.", 404)
        return self.directory / job_id

    def save(self, job: dict) -> None:
        folder = self.folder(job["id"])
        atomic_json(folder/'job.json',job)

    def snapshot(self, job_id: str) -> dict:
        with self.lock:
            folder = self.folder(job_id)
            stored = self.jobs[job_id]
            if stored['status'] == 'ready' and 'search_seed' not in stored:
                stored['search_seed'] = secrets.randbits(64)
                self.save(stored)
            if stored['status'] == 'ready' and stored.get('description_origin') not in {'user', 'recognition'}:
                description = self.catalog_description(stored['name'])
                if description != stored['description']:
                    stored.update(description=description, description_origin='catalog' if description else 'empty')
                    self._check_description(stored)
                    self.save(stored)
            if (stored['status'] != 'running' and not stored.get('description_check')
                    and (folder/'source.png').is_file()):
                self._check_description(stored)
                self.save(stored)
            job = dict(self.jobs[job_id])
            # JSON numbers lose 64-bit integer precision in the browser.
            if 'search_seed' in job:
                job['search_seed'] = str(job['search_seed'])
            if job["status"] == "running":
                job["elapsed"] = round(time.time() - job["started"], 1)
            preview = self.preview_file(job_id)
            if preview.is_file():
                job['preview_revision'] = preview.stat().st_mtime_ns
                job['preview'] = True
            export = self.export_file(job_id)
            job['export_available'] = export is not None
            job['export_draft'] = bool(export and (job['status'] == 'running'
                or not job.get('result') or job.get('quality') != 'passed'))
            if export:
                job['export_revision'] = export.stat().st_mtime_ns
            from src.imageConverterPreview import AttemptJournal
            job['attempt_count'] = AttemptJournal(folder).count
            log = folder / "console.log"
            if log.exists():
                with log.open("rb") as stream:
                    stream.seek(max(0, log.stat().st_size - 16000))
                    job["log"] = stream.read().decode("utf-8", errors="replace")
            else:
                job["log"] = ""
            return job

    def preview_file(self, job_id: str) -> Path:
        folder = self.folder(job_id)
        preview = folder / 'live-preview.svg'
        return preview if preview.is_file() else folder / 'recovery.svg'

    def export_file(self, job_id: str) -> Path | None:
        """Offer native drafts for manual saving, independently of acceptance gates."""
        from src.imageConverterSample import prepare_sample
        folder = self.folder(job_id)
        job = self.jobs[job_id]
        candidates = []
        if job.get('result') and job['status'] != 'running':
            candidates.append(folder/'result.svg')
        candidates.extend((folder/'manual-preview.svg', self.preview_file(job_id), folder/'result.svg'))
        if job['status'] != 'running':
            candidates.extend((folder/'output/refined.svg',
                folder/'output/converted_svgs/UPLOAD.svg',
                folder/'output/converted_svg_failed/Failed_UPLOAD.svg',
                folder/'output/converted_svg_failed/UPLOAD.svg',
                folder/'output/converted_svgs/Failed_UPLOAD.svg'))
        for candidate in dict.fromkeys(candidates):
            try:
                # Validate the file format only. Pixel and description checks
                # remain advisory for an explicit user export.
                prepare_sample(candidate.read_bytes(), job['width'], job['height'])
            except (OSError, ValueError, SyntaxError):
                continue
            return candidate
        if job['status'] != 'running':
            # Older searches may have retained observations only in the journal.
            # Recover once per journal revision, never rescan it on every poll.
            from src.imageConverterPreview import AttemptJournal, atomic_preview
            journal = AttemptJournal(folder)
            count = journal.count
            if count and self.manual_export_scans.get(job_id) != count:
                self.manual_export_scans[job_id] = count
                def native(svg):
                    if not isinstance(svg, str):
                        return False
                    try:
                        prepare_sample(svg.encode('utf-8'), job['width'], job['height'])
                        return True
                    except (ValueError, SyntaxError):
                        return False
                best = journal.best(validator=native)
                if best:
                    manual = folder/'manual-preview.svg'
                    atomic_preview(manual, best['svg'])
                    return manual
        return None

    def catalog_description(self, name: str) -> str:
        from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl

        # XML corrections take effect without restarting the long-lived server.
        descriptions = catalog_descriptions()
        self.descriptions = descriptions
        keys = (name, Path(name).stem, getBaseNameFromFileImpl(name))
        return next((descriptions[key.upper()] for key in keys
                     if key.upper() in descriptions), '')

    def upload(self, name: str, data: bytes) -> dict:
        from PIL import Image, ImageOps, UnidentifiedImageError

        name = name.replace("\\", "/").rsplit("/", 1)[-1][:180] or "Bild"
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as original:
                    if original.format not in {"PNG", "JPEG", "BMP", "GIF", "WEBP", "TIFF"}:
                        raise RequestError("Bitte ein PNG-, JPEG-, BMP-, GIF-, WebP- oder TIFF-Bild wählen.")
                    if original.width * original.height > MAX_PIXELS:
                        raise RequestError("Das Bild ist zu gross (maximal 20 Megapixel).")
                    # Multi-frame images use their first frame, just like catalog recognition.
                    image = ImageOps.exif_transpose(original).convert("RGBA")
                    background = Image.new("RGB", image.size, "white")
                    background.paste(image, mask=image.getchannel("A"))
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
                Image.DecompressionBombWarning) as exc:
            raise RequestError("Das Bild ist beschädigt, zu gross oder wird nicht unterstützt.") from exc
        description = self.catalog_description(name)
        with self.lock:
            source_sha256 = hashlib.sha256(
                f'{background.width}x{background.height}:'.encode()+background.tobytes()).hexdigest()
            previous = next((job for job in sorted(self.jobs.values(), key=lambda j:j.get('description_saved_at', j.get('started', j['created'])), reverse=True)
                             if job.get('source_sha256') == source_sha256
                             and job.get('description_origin') == 'user'), None)
            origin = 'user' if previous else ('catalog' if description else 'empty')
            if previous:
                description = previous['description']
            job_id = uuid.uuid4().hex
            folder = self.directory / job_id
            folder.mkdir()
            background.save(folder / "source.png")
            job = dict(id=job_id, name=name, width=background.width, height=background.height,
                       description=description, status="ready", created=time.time(),
                       message="Bild geladen. Beschreibung prüfen und Konvertierung starten.",
                       result=False, quality="unknown", profile="normal", elapsed=0,
                       source_sha256=source_sha256, description_origin=origin)
            self.jobs[job_id] = job
            self._check_description(job)
            self.save(job)
            return self.snapshot(job_id)

    def _check_description(self, job: dict, description: str | None = None) -> None:
        from src.imageConverterDescriptionCheck import check_description
        from src.imageConverterRecognition import rgb_image
        job['description_check'] = check_description(
            rgb_image(self.folder(job['id'])/'source.png'),
            job['description'] if description is None else description)

    def check_description(self, job_id: str, description: str) -> dict:
        if not isinstance(description, str) or len(description) > 12000:
            raise RequestError("Bitte eine Bildbeschreibung mit höchstens 12'000 Zeichen eingeben.")
        with self.lock:
            self.folder(job_id)
            job = self.jobs[job_id]
            if job['status'] == 'running' or job_id in self.processes:
                raise RequestError('Bitte zuerst die laufende Konvertierung beenden.', 409)
            self._check_description(job, description)
            self.save(job)
            return self.snapshot(job_id)

    def _persist_description(self, job: dict) -> None:
        job['description_saved_at'] = time.time()
        job['description_save'] = dict(scope='image', message='Beschreibung für dieses Bild gespeichert.')
        self.save(job)
        if self.description_store is not None:
            try:
                job['description_save'] = self.description_store.save(
                    job['name'], job.get('source_sha256'), job['description'])
            except (OSError, ValueError, SyntaxError) as exc:
                job['description_save'] = dict(scope='image', warning=True,
                    message=f'Beschreibung für dieses Bild gespeichert. Katalog konnte nicht aktualisiert werden: {exc}')
            self.save(job)

    def save_description(self, job_id: str, description: str) -> dict:
        if not isinstance(description, str) or len(description) > 12000:
            raise RequestError("Bitte eine Bildbeschreibung mit höchstens 12'000 Zeichen eingeben.")
        with self.lock:
            self.folder(job_id)
            if self.jobs[job_id]['status'] == 'running' or job_id in self.processes:
                raise RequestError('Bitte zuerst die laufende Konvertierung beenden.', 409)
            job = self.editable(job_id)
            job.update(description=description, description_origin='user')
            self._check_description(job)
            self._persist_description(job)
            return self.snapshot(job['id'])

    def busy(self, *, background: bool = False) -> bool:
        """Reserve one slot per lane, including workers still cleaning up."""
        with self.lock:
            return any((job['status'] == 'running' or job_id in self.processes)
                       and bool(job.get('catalog_background')) == background
                       for job_id, job in self.jobs.items())

    def recognize(self, job_id: str) -> dict:
        from src.imageConverterRecognition import rgb_image
        with self.lock:
            folder = self.folder(job_id)
            if self.jobs[job_id]['status'] == 'running':
                raise RequestError('Bitte zuerst die laufende Konvertierung beenden.', 409)
        recognition = self.recognizer.recognize(rgb_image(folder/'source.png'))
        with self.lock:
            job = self.jobs[job_id]
            if job['status'] == 'running':
                raise RequestError('Bitte zuerst die laufende Konvertierung beenden.', 409)
            job['recognition'] = recognition
            if job['status'] == 'ready' and not job['description'].strip() and recognition['automatic']:
                job.update(description=recognition['automatic']['description'], description_origin='recognition')
            self._check_description(job)
            self.save(job)
            return self.snapshot(job_id)

    def start(self, job_id: str, description: str, profile: str, *, background: bool = False,
              seed: str | int | None = None, use_current_svg: bool = True) -> dict:
        if not isinstance(description, str) or not description.strip() or len(description) > 12000:
            raise RequestError("Bitte eine Bildbeschreibung mit 1 bis 12'000 Zeichen eingeben.")
        if profile not in PROFILES:
            raise RequestError("Unbekanntes Suchprofil.")
        if profile in {'explore5', 'explore10'}:
            from src.iCCModules.imageCompositeConverterSceneProgram import scene_program
            if scene_program(description) is None:
                raise RequestError('Die freie Suche unterstützt derzeit einfache Listen aus Kreis, Ellipse, Rechteck, '
                                   'Quadrat, Dreieck und Linie sowie Kelle mit Griff und gemeinsame Spitzen. '
                                   'Weitere Angaben in dieser Beschreibung kann sie noch nicht vollständig auswerten.')
        if type(use_current_svg) is not bool:
            raise RequestError('Die SVG-Wiederverwendung muss ein Wahrheitswert sein.')
        if seed is not None:
            if (type(seed) not in (str, int) or not re.fullmatch(r'[0-9]{1,20}', str(seed))
                    or not 0 <= int(seed) < 2**64):
                raise RequestError("Der Seed muss eine ganze Zahl zwischen 0 und 18446744073709551615 sein.")
            seed = int(seed)
        try:
            from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
            resolve_similarity_description(description, catalog_descriptions(), base_name=getBaseNameFromFileImpl)
            from src.iCCModules.imageCompositeConverterSvgComponents import parse_components, load_component
            components = parse_components(description)
            for index, component in enumerate(components):
                load_component(component['name'], index)
        except SimilarityReferenceError as exc:
            raise RequestError(str(exc)) from exc
        except (OSError, ValueError, SyntaxError) as exc:
            raise RequestError(str(exc)) from exc
        with self.lock:
            if self.closed or self.busy(background=background):
                raise RequestError("Es läuft bereits eine Konvertierung. Bitte warten oder abbrechen.", 409)
            self.folder(job_id)
            previous = self.jobs[job_id]
            if previous['status'] == 'running' or job_id in self.processes:
                raise RequestError('Bitte zuerst die laufende Konvertierung beenden.', 409)
            origin = ('user' if description.strip() != previous['description']
                      else previous.get('description_origin', 'user'))
            job = self.editable(job_id)
            job_id = job["id"]
            job.update(description=description.strip(), profile=profile, status="running",
                       use_current_svg=use_current_svg,
                       catalog_background=background,
                       description_origin=origin,
                       search_seed=secrets.randbits(64) if seed is None else seed,
                       started=time.time(), message="Sample wird am Original verbessert …" if job.get("sample") else "Bild wird konvertiert …")
            if use_current_svg and not components and profile not in {'explore5', 'explore10'}:
                self.use_best_svg(job)
            if profile in {'explore5', 'explore10'}:
                job['message'] = 'Freie Grundformensuche: Population erzeugen oder gespeicherten Suchstand fortsetzen …'
            self._check_description(job)
            if origin == 'user' and not background:
                self._persist_description(job)
            self.save(job)
            thread = threading.Thread(target=self.run, args=(job_id,), daemon=True)
            self.threads.append(thread)
            thread.start()
            return self.snapshot(job_id)

    def project_svg(self, job: dict) -> Path:
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', Path(job['name']).stem).rstrip('. ') or 'Bild'
        if re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',name,re.I):
            name = '_'+name
        return self.project_directory/'converted_svgs'/(name+'.svg')

    def use_best_svg(self, job: dict) -> None:
        """Seed from this image's current native vector, never a stale name alone."""
        from src.imageConverterSample import prepare_sample
        folder = self.folder(job['id'])
        if job.get('sample_pending') and job.get('sample') and (folder/'sample.svg').is_file():
            job.update(sample_pending=False,sample_origin='Geladene Vorlage',
                       message='Geladene Vorlage wird am Original weiter verbessert …')
            return
        project = self.project_svg(job)
        if project.is_file():
            try:
                prepare_sample(project.read_bytes(),job['width'],job['height'])
                quality = saved_svg_quality(folder/'source.png',project)
                if (quality and not result_description_error(project, job['description'])
                        and (not quality['observed_foreground_pixels'] or quality['output_foreground_pixels'])):
                    shutil.copyfile(project,folder/'sample.svg')
                    job.update(sample=True,sample_name=project.name,sample_origin='Gespeichertes Projekt-SVG',
                               starting_svg_quality=quality,message='Aktuelles Projekt-SVG wird am Original weiter verbessert …')
                    return
            except (OSError,ValueError,SyntaxError):
                pass
        candidates = []
        if job.get('sample') and (folder/'sample.svg').is_file():
            candidates.append((folder/'sample.svg','Geladene Vorlage'))
        candidates.extend([(self.project_svg(job),'Gespeichertes Projekt-SVG'),
                           (ROOT/'artifacts/samples'/(Path(job['name']).stem+'.svg'),'Vorhandenes SVG')])
        for previous in self.jobs.values():
            if (job.get('source_sha256') and previous.get('result') and previous.get('source_sha256') == job.get('source_sha256')
                    and previous['id'] != job['id']):
                candidates.append((self.folder(previous['id'])/'result.svg','Bisheriges Ergebnis'))
        best, seen = None, set()
        for path,origin in candidates:
            key = path.resolve()
            if key in seen or not path.is_file():
                continue
            seen.add(key)
            try:
                prepare_sample(path.read_bytes(),job['width'],job['height'])
            except (OSError,ValueError,SyntaxError):
                continue
            quality = saved_svg_quality(folder/'source.png',path)
            if quality is None or (quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']):
                continue
            error = result_description_error(path,job['description'])
            rank = (bool(error),not quality['passed'],vector_comparison_score(quality))
            if best is None or rank < best[0]:
                best = rank,path,origin,quality
        if best is not None:
            _,path,origin,quality = best
            if path.resolve() != (folder/'sample.svg').resolve():
                shutil.copyfile(path,folder/'sample.svg')
            job.update(sample=True,sample_name=path.name,sample_origin=origin,
                       starting_svg_quality=quality,message='Aktuelles SVG wird am Original weiter verbessert …')

    def editable(self, job_id: str) -> dict:
        """Share retry/attachment preparation; completed results stay immutable."""
        folder = self.folder(job_id)
        previous = job = self.jobs[job_id]
        if job["status"] != "ready":
            copied = self.upload(job["name"], (folder / "source.png").read_bytes())
            job = self.jobs[copied["id"]]
            job.update(description=previous["description"], profile=previous["profile"],
                       description_origin=previous.get('description_origin', 'user'))
            self._check_description(job)
            if previous.get('recognition'):
                job['recognition'] = previous['recognition']
            if previous.get("sample"):
                shutil.copyfile(folder / "sample.svg", self.folder(job["id"]) / "sample.svg")
                job.update(sample=True, sample_name=previous["sample_name"],
                           sample_pending=previous.get('sample_pending',False),
                           sample_origin=previous.get('sample_origin','Geladene Vorlage'))
            job['previous_job_id'] = previous['id']
            for key in ('collection_case_id','collection_image_sha256','collection_label','collection_next_case_id'):
                if key in previous:
                    job[key] = previous[key]
        return job

    def run(self, job_id: str) -> None:
        folder = self.folder(job_id)
        job = self.jobs[job_id]
        process = None
        deadline = time.monotonic() + PROFILES[job['profile']][1]
        try:
            input_dir = folder / "input"
            job['conversion_policy'] = 'description_only_v1'
            input_dir.mkdir()
            shutil.copyfile(folder / "source.png", input_dir / "UPLOAD.png")
            descriptions = folder / "description.csv"
            catalog = catalog_descriptions()
            write_description_table(descriptions, job["description"], catalog)
            output = folder / "output"
            seconds, maximum = PROFILES[job["profile"]]
            from src.iCCModules.imageCompositeConverterSvgComponents import parse_components
            component_mode = bool(parse_components(job['description']))
            command = [sys.executable, "-u", "-m", "src.imageCompositeConverter", str(input_dir),
                       "--descriptions-path", str(descriptions), "--output-dir", str(output),
                       "--start", "UPLOAD", "--end", "UPLOAD", "--execution-mode", "semantic-only",
                       "--search-seconds", str(seconds), "--search-max-seconds", str(maximum),
                       "--search-seed", str(job["search_seed"]),
                       "--fail-on-batch-failures", "--log-file", str(folder / "converter.local.log")]
            exploring = job['profile'] in {'explore5', 'explore10'}
            from src.iCCModules.imageCompositeConverterSceneProgram import scene_program
            program = scene_program(job['description'])
            complete_scene = program is not None and any(o['kind']=='text' for o in program['objects'])
            if exploring or complete_scene:
                memory = self.directory / 'primitive-search-memory'
                job['primitive_search_memory'] = str(memory)
                # These profiles specify a maximum time. A failed population
                # keeps exploring instead of stopping at the old 4096-render
                # ceiling or at the normal profile's shorter initial slice.
                search_seconds = seconds if exploring else maximum
                command += ['--primitive-exploration', '--primitive-memory', str(memory),
                            '--search-budget', '1000000', '--search-seconds', str(search_seconds),
                            '--search-max-seconds', str(search_seconds)]
            if component_mode:
                description_file = folder / 'description.txt'
                description_file.write_text(job['description'], encoding='utf-8')
                command = [sys.executable, '-u', '-m', 'src.imageConverterComponents',
                           '--source', str(folder / 'source.png'),
                           '--output', str(output / 'refined.svg'),
                           '--description', str(description_file),
                           '--seed', str(job['search_seed']),
                           '--seconds', str(max(0.01, deadline-time.monotonic()-1))]
            elif not exploring and job.get("sample") and job.get('use_current_svg',True):
                description_file = folder / "description.txt"
                from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
                resolved = resolve_similarity_description(job["description"], catalog, base_name=getBaseNameFromFileImpl)
                description_file.write_text(resolved.text, encoding="utf-8")
                command = [sys.executable, "-u", "-m", "src.imageConverterSample",
                           "--source", str(folder / "source.png"), "--sample", str(folder / "sample.svg"),
                           "--output", str(output / "refined.svg"), "--description", str(description_file),
                           "--seconds", str(maximum), '--seed', str(job['search_seed']),
                           '--deadline', str(time.time()+max(0., deadline-time.monotonic()))]
            environment = os.environ.copy()
            environment.update(PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8",
                               ICC_MAX_QUALITY_PASSES="0", ICC_CONVERSION_TIMEOUT_SEC=str(maximum))
            # This whole CLI already runs in a killable, deadline-supervised
            # process tree. Per-candidate renderer IPC consumes the model's
            # budget before multi-part scenes finish. Keep explicit overrides.
            environment.setdefault("IMAGE_CONVERTER_ISOLATE_SVG_RENDER", "0")
            environment.setdefault("IMAGE_CONVERTER_REUSE_RENDER_WORKER", "1")
            if not job.get('catalog_background'):
                preview_description = folder/'preview-description.txt'
                preview_description.write_text(resolve_similarity_description(job['description'], catalog).text, encoding='utf-8')
                environment.update(ICC_GUI_PREVIEW_SOURCE=str(folder / 'source.png'),
                                   ICC_GUI_PREVIEW_OUTPUT=str(folder / 'live-preview.svg'),
                                   ICC_GUI_PREVIEW_DESCRIPTION_FILE=str(preview_description),
                                   ICC_GUI_PREVIEW_PHASE='Freie Grundformensuche' if exploring else 'Sample-Anpassung' if job.get('sample') and job.get('use_current_svg',True) else 'Suche')
            options = ({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt"
                       else {"start_new_session": True})
            with (folder / "console.log").open("wb") as log:
                if not component_mode and not exploring and job.get('sample') and job.get('use_current_svg',True) and resolved.references:
                    for reference in resolved.references:
                        aspect = {'shape': 'Form', 'color': 'Farben', 'gradient': 'Farbverlauf'}[reference['aspect']]
                        log.write(f"Ähnlichkeitsreferenz ({aspect}): {reference['key']}\n".encode('utf-8'))
                    log.write(f"Aufgelöste Bildbeschreibung: {resolved.text}\n".encode('utf-8'))
                    log.flush()
                with self.lock:
                    if job["status"] != "running":
                        return
                    process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                               stdout=log, stderr=subprocess.STDOUT,
                                               stdin=subprocess.DEVNULL, **options)
                    self.processes[job_id] = process
                try:
                    # Cancellation terminates the process tree and releases this wait.
                    process.wait(timeout=max(.01, deadline-time.monotonic()))
                except subprocess.TimeoutExpired:
                    with self.lock:
                        stop_process_tree(process)
                        log.write('Zeitlimit erreicht; besten vorhandenen Vektorentwurf sichern.\n'.encode('utf-8'))
                        log.flush()
            with self.lock:
                if job['status'] != 'running':
                    return
                # Collect into a temporary snapshot: a failed first attempt
                # must not appear terminal while Plan B still has search time.
                collected = dict(job)
                collect = collect_sample_result if component_mode or (not exploring and job.get('sample') and job.get('use_current_svg',True)) else collect_result
                collect(folder, collected, process.returncode)
                retain_best_preview(folder, collected)
            retain_best_preview(folder, collected)
            with self.lock:
                if job["status"] == "running":
                    job.update(collected)
                    previous = self.jobs.get(job.get('previous_job_id'))
                    if job.get('result') and previous and previous.get('result'):
                        same = ((folder / 'result.svg').read_bytes() ==
                                (self.folder(previous['id']) / 'result.svg').read_bytes())
                        job['same_as_previous'] = same
                        from src.imageConverterDiversity import compare_results
                        try:
                            comparison = compare_results((folder/'result.svg').read_text(encoding='utf-8'),
                                (self.folder(previous['id'])/'result.svg').read_text(encoding='utf-8'))
                            job['attempt_comparison'] = dict(comparison, previous_job_id=previous['id'],
                                seed=str(job.get('search_seed')), previous_seed=str(previous.get('search_seed')),
                                same_description=previous['description'] == job['description'])
                            if job['quality'] == 'warning' and comparison['raster_identical']:
                                job['message'] += ' Der Bildvergleich mit dem vorherigen Versuch ist exakt identisch.'
                            elif job['quality'] == 'warning' and comparison['foreground_similarity'] >= .99:
                                job['message'] += ' Der Bildvergleich mit dem vorherigen Versuch zeigt mindestens 99 % Ähnlichkeit.'
                        except (OSError, ValueError, SyntaxError):
                            job['attempt_comparison'] = dict(error='comparison_unavailable')
                        if same and job['quality'] == 'warning':
                            job['message'] += (' Trotz geänderter Beschreibung hat die Suche denselben Entwurf ergeben.'
                                               if previous['description'] != job['description'] else
                                               ' Die erneute Suche hat denselben besten Entwurf ergeben.')
                    try:
                        self.publish_best(job_id)
                    except (OSError, ValueError) as exc:
                        job['project_save'] = dict(status='error', message=f'Projektablage fehlgeschlagen: {exc}')
        except Exception as exc:
            if process is not None:
                stop_process_tree(process)
            with self.lock:
                if job["status"] == "running":
                    job.update(status="error", message=f"Konvertierung fehlgeschlagen: {exc}")
        finally:
            with self.lock:
                self.processes.pop(job_id, None)
                job["elapsed"] = round(time.time() - job["started"], 1)
                self.save(job)

            if self.on_result is not None:
                self.on_result(job_id)

    def recover_result(self, job_id: str, collected: dict, deadline: float, environment: dict, options: dict) -> None:
        """Compatibility entry point: raster reconstruction has been removed."""
        return None

    def cancel(self, job_id: str) -> dict:
        with self.lock:
            self.folder(job_id)
            job = self.jobs[job_id]
            if job["status"] == "running":
                process = self.processes.get(job_id)
                if process:
                    stop_process_tree(process)
                job.update(status="cancelled", message="Konvertierung abgebrochen.")
                self.save(job)
            return self.snapshot(job_id)

    def attach_sample(self, job_id: str, name: str, data: bytes | None) -> dict:
        from src.imageConverterSample import prepare_sample
        with self.lock:
            folder = self.folder(job_id)
            job = self.jobs[job_id]
            if job["status"] == "running":
                raise RequestError("Bitte zuerst die laufende Konvertierung beenden.", 409)
            prepared = None
            if data is not None:
                try:
                    prepared = prepare_sample(data, job["width"], job["height"])
                except (ValueError, SyntaxError) as exc:
                    raise RequestError(f"Sample konnte nicht geladen werden: {exc}") from exc
            job = self.editable(job_id)
            job_id = job["id"]
            folder = self.folder(job_id)
            job.update(sample=prepared is not None, sample_name=name.replace("\\", "/").rsplit("/", 1)[-1][:180] if prepared else "",
                       sample_pending=prepared is not None,sample_origin='Geladene Vorlage' if prepared else '')
            if prepared:
                (folder / "sample.svg").write_text(prepared, encoding="utf-8")
                job["message"] = "Original und Sample geladen. Vorhandene SVG-Formen werden am Original optimiert."
            else:
                job["message"] = "Sample entfernt. Das Original wird neu konvertiert."
            self.save(job)
            return self.snapshot(job_id)

    def save_as(self, job_id: str) -> dict:
        if not self.save_lock.acquire(blocking=False):
            raise RequestError("Ein Speicherdialog ist bereits geöffnet.", 409)
        try:
            with self.lock:
                folder = self.folder(job_id)
                job = self.jobs[job_id]
                source = self.export_file(job_id)
                if source is None:
                    raise RequestError("Noch kein SVG zum Speichern verfügbar.", 404)
                name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", Path(job["name"]).stem).rstrip(". ") or "Bild"
                content = source.read_bytes()
            # The search may keep improving while the system dialog is open.
            # Freeze the version chosen at the start of this save operation.
            with tempfile.TemporaryDirectory(prefix='export-', dir=folder) as temporary:
                snapshot = Path(temporary)/'result.svg'
                snapshot.write_bytes(content)
                result = save_svg_dialog(snapshot, name + ".svg", self.dialog_locations.get('save', ''))
            if result.get('saved'):
                self.remember_location('save', Path(result['path']).parent)
            return result
        finally:
            self.save_lock.release()

    def remember_location(self, kind: str, directory: Path) -> None:
        with self.lock:
            self.dialog_locations[kind] = str(directory)
            path = self.directory / 'dialog_locations.json'
            temporary = path.with_suffix('.tmp')
            temporary.write_text(json.dumps(self.dialog_locations, ensure_ascii=False), encoding='utf-8')
            temporary.replace(path)

    def pick(self, payload: dict) -> dict:
        kind = payload.get('kind')
        if kind not in {'image', 'sample', 'workbench'}:
            raise RequestError('Unbekannte Dateiauswahl.')
        if kind == 'sample':
            with self.lock:
                self.folder(payload.get('job_id'))
        if not self.save_lock.acquire(blocking=False):
            raise RequestError('Ein Dateidialog ist bereits geöffnet.', 409)
        try:
            result = open_file_dialog(kind, self.dialog_locations.get(kind, ''))
            if not result.get('selected'):
                return dict(selected=False)
            path = Path(result['path'])
            limit = MAX_UPLOAD if kind == 'image' else 2 * 1024 * 1024
            with path.open('rb') as stream:
                data = stream.read(limit + 1)
            if len(data) > limit:
                raise RequestError(f'Die Datei darf maximal {limit // (1024 * 1024)} MB gross sein.', 413)
            if kind == 'image':
                output = dict(job=self.upload(path.name, data))
            elif kind == 'sample':
                output = dict(job=self.attach_sample(payload.get('job_id'), path.name, data))
            else:
                output = dict(svg=data.decode('utf-8-sig'), name=path.name)
            self.remember_location(kind, path.parent)
            return dict(selected=True, **output)
        except OSError as exc:
            raise RequestError(f'Die gewählte Datei konnte nicht gelesen werden: {exc}') from exc
        finally:
            self.save_lock.release()

    def publish_best(self, job_id: str) -> None:
        """Save an independently better native result, preserving its quality label."""
        job = self.jobs[job_id]
        if job.get('catalog_background'):
            return  # The background service keeps candidates for both catalog renderers.
        if job.get('status') != 'done' or not job.get('result'):
            return
        folder = self.folder(job_id)
        if result_description_error(folder/'result.svg', job.get('description', '')):
            job['project_save'] = dict(status='skipped', message='Keine Projektablage: Beschreibungsprüfung nicht bestanden.')
            return
        quality = saved_svg_quality(folder / 'source.png', folder / 'result.svg')
        if not quality or (quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']):
            job['project_save'] = dict(status='skipped', message='Keine Projektablage: kein prüfbares Vektorergebnis.')
            return
        target = self.project_svg(job)
        name = target.stem
        if target.exists():
            previous = saved_svg_quality(folder / 'source.png', target)
            if previous is None:
                job['project_save'] = dict(status='skipped', message='Vorhandenes Projekt-SVG konnte nicht verglichen werden; es bleibt erhalten.')
                return
            previous_error = (result_description_error(target,job.get('description',''))
                              or not previous.get('within_canvas', True))
            if ((False,not quality['passed'],vector_comparison_score(quality)) >=
                    (bool(previous_error),not previous['passed'],vector_comparison_score(previous)-1e-12)):
                job['project_save'] = dict(status='unchanged', path=str(target), message='Die vorhandene Projektversion ist gleich gut oder besser und bleibt erhalten.')
                return
            old = target.read_bytes()
            backup = self.project_directory / 'gui_history' / name / (hashlib.sha256(old).hexdigest() + '.svg')
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(old)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.svg.tmp')
        temporary.write_bytes((folder / 'result.svg').read_bytes())
        temporary.replace(target)
        job['project_save'] = dict(status='saved', path=str(target), normalized_mse=quality['normalized_mse'],
                                   quality=job.get('quality','warning'),
                                   message=f'Automatisch im Projekt gespeichert: {target}')

    def close(self) -> None:
        with self.lock:
            self.closed = True
            for job_id in list(self.jobs):
                if self.jobs[job_id]["status"] == "running":
                    self.cancel(job_id)
        for thread in self.threads:
            thread.join(timeout=20)


def retain_best_preview(folder: Path, job: dict) -> None:
    """Keep the independently rechecked best observation at phase boundaries.

    Preview scores and worker reports cannot certify a model. A recovered
    observation remains an explicitly unconfirmed draft, even if pixels pass.
    """
    from src.imageConverterPreview import AttemptJournal
    from src.imageConverterSample import prepare_sample
    from src.iCCModules.imageCompositeConverterCanvas import contain_svg
    result = folder/'result.svg'
    candidates = [folder/'live-preview.svg']
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    try:
        assertions = description_assertions(resolve_similarity_description(
            job.get('description', ''), catalog_descriptions()).text)
    except ValueError:
        return
    def valid_inventory(svg):
        try:
            svg = contain_svg(svg, job['width'], job['height'])
            validate_svg_assertions(svg, assertions)
            return True
        except (ValueError, SyntaxError):
            return False
    # The population engine and its live publisher already retain their best
    # valid candidates. Rescanning tens of thousands of rejected observations
    # here can otherwise add minutes after a five-minute search has finished.
    best = (None if job.get('profile') in {'explore5', 'explore10'}
            else AttemptJournal(folder).best(validator=valid_inventory))
    if best is not None:
        observed = folder/'best-observed.svg'
        observed.write_text(contain_svg(best['svg'], job['width'], job['height']), encoding='utf-8')
        candidates.append(observed)
    if job.get('result') and result.is_file():
        contain_result(result, job)
    previous = saved_svg_quality(folder/'source.png', result) if job.get('result') else None
    previous_error = result_description_error(result, job.get('description', '')) if previous else ''
    if job.get('quality') == 'passed' and previous and previous['passed'] and not previous_error:
        return
    for candidate in candidates:
        if not candidate.is_file():
            continue
        contain_result(candidate, job)
        try:
            prepare_sample(candidate.read_bytes(), job['width'], job['height'])
        except (OSError, ValueError, SyntaxError):
            continue
        quality = saved_svg_quality(folder/'source.png', candidate)
        if quality is None or (quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']):
            continue
        error = result_description_error(candidate, job.get('description', ''))
        if error:
            continue
        # Prefer a valid deliverable over a numerically closer contradiction.
        rank = (bool(error), not quality['passed'], vector_comparison_score(quality))
        old_rank = ((bool(previous_error), not previous['passed'], vector_comparison_score(previous))
                    if previous else (True, True, float('inf')))
        if previous and rank >= old_rank:
            continue
        shutil.copyfile(candidate, result)
        previous, previous_error = quality, error
        job.pop('result_rejection',None)
        job.update(status='done', result=True, quality='warning', pixel_quality=quality,
                   description_error=error, retained_preview=True,
                   description_validation_version=DESCRIPTION_VALIDATION_VERSION,
                   message='Bester vorhandener Vektorentwurf aus der Suche erhalten. '
                           'Die vollständige Modellprüfung ist noch offen; bitte den Entwurf prüfen.')
        if (job.get('sample_report') or {}).get('restarted_from_description'):
            job['message'] = 'Unpassende Vorlage verworfen; neu aus der Bildbeschreibung konvertiert. '+job['message']


def collect_recovery_result(folder: Path, job: dict, *, stop_reason: str) -> None:
    """Recheck the delivered vector, even after worker termination or reload."""
    result = folder/'recovery.svg'
    try:
        from src.imageConverterSample import prepare_sample
        prepare_sample(result.read_bytes(), job['width'], job['height'])
    except (OSError, ValueError, SyntaxError):
        return
    try:
        report = json.loads(result.with_suffix('.json').read_text(encoding='utf-8'))
        if not isinstance(report, dict):
            report = {}
    except (OSError, ValueError):
        # Termination can fall between the atomic SVG and report writes. The
        # actual saved vector is independently checked below and stays usable.
        report = {}
    quality = saved_svg_quality(folder/'source.png', result)
    if quality is None or (quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']):
        return
    previous_result = folder/'result.svg'
    previous_quality = saved_svg_quality(folder/'source.png', previous_result) if job.get('result') else None
    candidate_error = result_description_error(result, job.get('description', ''))
    if candidate_error:
        return  # historical recovery artifacts cannot bypass the closed inventory
    candidate_passed = bool(quality['passed'] and not candidate_error)
    previous_passed = bool(previous_quality and previous_quality.get('passed') and
        not result_description_error(previous_result, job.get('description', '')))
    if (previous_quality and
            (not previous_passed, vector_comparison_score(previous_quality)) <=
            (not candidate_passed, vector_comparison_score(quality))):
        result = folder/'result.svg'
        quality = saved_svg_quality(folder/'source.png', result)
        if quality is None:
            return
    else:
        shutil.copyfile(result, folder/'result.svg')
    error = result_description_error(result, job.get('description', ''))
    passed = bool(quality['passed'] and not error)
    message = ('SVG erstellt. Bildvergleich und Beschreibungsprüfung bestanden.' if passed else
               'Vektorentwurf elementweise erstellt. Bitte prüfen; die Qualitätsprüfung wurde nicht bestanden.')
    if error.startswith('wrong_described_arrow_direction:'):
        side = 'links' if error.endswith(':left') else 'rechts'
        message += f' Die beschriebene Pfeilrichtung {side} widerspricht dem Bild; der Entwurf folgt dem Original.'
    elif error:
        message += ' Bild und Beschreibung stimmen noch nicht vollständig überein.'
    job.update(status='done', result=True, quality='passed' if passed else 'warning', pixel_quality=quality,
               description_error=error, message=message,
               description_validation_version=DESCRIPTION_VALIDATION_VERSION)
    job.pop('result_rejection', None)
    report.update(passed=passed, description_error=error, pixel_quality=quality)
    if not ((passed and report.get('stop_reason') == 'quality_target_reached') or
            report.get('stop_reason') in {'search_space_exhausted', 'construction_frontier_exhausted', 'time_limit'}):
        report['stop_reason'] = stop_reason
    job['recovery_report'] = report
    if not passed:
        job['message'] += (' Die geprüften unterschiedlichen Konstruktionen sind ausgeschöpft.'
                           if report.get('stop_reason') in {'search_space_exhausted', 'construction_frontier_exhausted'} else
                           ' Das Zeitbudget wurde ausgeschöpft.' if stop_reason == 'time_limit'
                           else ' Die elementweise Suche ist beendet.')


def collect_sample_result(folder: Path, job: dict, returncode: int) -> None:
    result = folder / "output" / "refined.svg"
    report_path = result.with_suffix(".json")
    if not report_path.is_file():
        job.update(status="error", result=False, quality="unknown", message="Sample konnte nicht verbessert werden. Details stehen im Protokoll.")
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not result.is_file() or report.get('result') is False:
        job.update(status='error', result=False, quality='warning', sample_report=report,
                   description_error=report.get('description_error', ''),
                   message=report.get('message') or 'Kein passendes SVG aus der Beschreibung erzeugt. Details stehen im Protokoll.')
        return
    if returncode != 0:
        report['stop_reason'] = 'interrupted'
    if reject_raster_result(result, job):
        return
    contain_result(result, job)
    if reject_description_result(result, job):
        return
    # Recheck the actual deliverable, including old worker reports. A low
    # global pixel error cannot certify a described but collapsed arrow head.
    quality = saved_svg_quality(folder/'source.png', result)
    error = result_description_error(result, job.get('description', ''))
    report.update(passed=bool(report['passed'] and quality and quality['passed'] and not error),
                  description_error=error or report.get('description_error', ''))
    shutil.copyfile(result, folder / "result.svg")
    message = "Sample am Original verbessert." if report.get("improved") else "Keine messbare Verbesserung gefunden. Der Sample-Stand bleibt erhalten."
    if report.get('stop_reason') == 'quality_target_reached':
        message = 'Das Sample erfüllt die Pixelprüfung bereits; seine Formen bleiben erhalten.'
    elif report.get('stop_reason') == 'sample_alignment_accepted':
        message = 'Sample als Ganzes skaliert und ausgerichtet; vorhandene Formen bleiben erhalten.'
    elif report.get('stop_reason') == 'native_search_accepted':
        message = 'Vorlagenaufbau neu bearbeitet; Bildvergleich und Beschreibungsprüfung bestanden.'
    elif report.get('stop_reason') == 'svg_components_composed':
        message = 'Referenzierte SVG-Bauteile zusammengesetzt und am Original platziert.'
    elif report.get('primitive_evolution'):
        message = 'Grundformen mit allen beschriebenen Rändern und Verläufen neu angepasst.'
    elif report.get('restarted_from_description'):
        message = 'Unpassende Vorlage verworfen. SVG neu aus der Bildbeschreibung erstellt.'
    message += " Pixelprüfung bestanden." if report["passed"] else " Bitte den Entwurf prüfen; die Pixel- oder explizite Beschreibungsprüfung ist noch offen."
    if quality and quality.get('overlap_passed') is False:
        message += ' Im Überlappungsbereich weicht das SVG zu stark vom Original ab.'
    if report.get('continuation'):
        message += f" {report['evaluations']} Bildkandidaten geprüft."
        if not report.get('search_goal_reached'):
            message += ' Das strengere Suchziel wurde noch nicht erreicht.'
    job.update(status="done", result=True, quality="passed" if report["passed"] else "warning",
               message=message, sample_report=report, pixel_quality=quality, description_error=report['description_error'],
               description_validation_version=DESCRIPTION_VALIDATION_VERSION)


def result_description_error(svg: Path, description: str) -> str:
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    try:
        resolved = resolve_similarity_description(description, catalog_descriptions())
        validate_svg_assertions(svg.read_text(encoding='utf-8'), description_assertions(resolved.text))
    except (OSError, ValueError, SyntaxError) as exc:
        return str(exc)
    return ''


def contain_result(path: Path, job: dict) -> None:
    """Normalize only a newly generated job artifact, never its uploaded sample."""
    from src.iCCModules.imageCompositeConverterSvgComponents import parse_components
    if parse_components(job.get('description', '')):
        # Components already have independently bounded viewports and a strict
        # placement contract; another wrapper would change that assembly.
        return
    from src.iCCModules.imageCompositeConverterCanvas import contain_svg
    try:
        original = path.read_text(encoding='utf-8')
        bounded = contain_svg(original, job.get('width'), job.get('height'))
        if bounded != original:
            temporary = path.with_suffix('.svg.tmp')
            temporary.write_text(bounded, encoding='utf-8')
            temporary.replace(path)
    except (ValueError, OSError, SyntaxError):
        pass  # normal SVG/quality rejection below handles invalid artifacts


def reject_description_result(result: Path, job: dict) -> bool:
    error = result_description_error(result, job.get('description', ''))
    if not error:
        return False
    job.update(status='error', result=False, quality='warning',
               result_rejection='description_inventory', description_error=error,
               description_validation_version=DESCRIPTION_VALIDATION_VERSION,
               message='Konvertierung ungenügend: Die beschriebenen Elemente konnten nicht exakt '
                       'umgesetzt werden. Bitte die Bildbeschreibung präzisieren. Details stehen im Protokoll.')
    return True


def reject_raster_result(result: Path, job: dict) -> bool:
    """Keep raster failure diagnostics out of previews, downloads and history."""
    from xml.etree import ElementTree as ET
    try:
        root = ET.parse(result).getroot()
    except (OSError, ET.ParseError):
        return False  # Invalid/unrenderable output is handled by the quality check.
    if not any(node.tag.rsplit('}', 1)[-1] == 'image' for node in root.iter()):
        return False
    job.update(status='error', result=False, quality='warning', result_rejection='embedded_raster',
               message='Vektorisierung fehlgeschlagen. Die Ausgabe enthält ein eingebettetes Rasterbild '
                       'und wird deshalb nicht als SVG-Ergebnis angeboten. Details stehen im Protokoll.')
    return True


def collect_result(folder: Path, job: dict, returncode: int) -> None:
    """Never equate a zero CLI exit code or an existing SVG with passed quality."""
    output = folder / "output"
    candidates = [output / "converted_svgs" / "UPLOAD.svg"]
    for subdirectory in ("converted_svg_failed", "converted_svgs"):
        candidates.append(output / subdirectory / "Failed_UPLOAD.svg")
        candidates.append(output / subdirectory / "UPLOAD.svg")
    result = next((path for path in candidates if path.is_file()), None)
    failures = output / "reports" / "batch_failure_summary.csv"
    has_failures = False
    if failures.exists():
        with failures.open(encoding="utf-8-sig", newline="") as stream:
            has_failures = bool(list(csv.DictReader(stream, delimiter=";")))
    if result:
        if reject_raster_result(result, job):
            return
        contain_result(result, job)
        if reject_description_result(result, job):
            return
        shutil.copyfile(result, folder / "result.svg")
        # A model can be shifted off-canvas and still receive a successful CLI
        # status. Re-render the saved vector against the actual uploaded image.
        quality = saved_svg_quality(folder / 'source.png', result)
        job['pixel_quality'] = quality
        if quality and quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']:
            job.update(status='error', result=False, quality='warning',
                       message='Das SVG ist leer oder liegt ausserhalb der Zeichenfläche. Bitte die Beschreibung prüfen oder ein Sample-SVG laden.')
            return
        description_error = result_description_error(result, job.get('description', ''))
        passed = (returncode == 0 and not has_failures and result == candidates[0]
                  and quality is not None and quality['passed'] and not description_error)
        job.update(status="done", result=True, quality="passed" if passed else "warning",
                   description_error=description_error,
                   description_validation_version=DESCRIPTION_VALIDATION_VERSION,
                   message=("SVG erstellt. Qualitätsprüfung bestanden." if passed else
                            "Entwurf erstellt. Die Qualitätsprüfung wurde nicht bestanden; bitte das Ergebnis prüfen."))
        summary = search_summary(output)
        if summary is not None:
            job['search_summary'] = summary
            if passed and summary['satisfactory'] is False:
                passed = False
                job.update(quality='warning', message=(
                    'SVG erstellt. Pixelprüfung bestanden; die vollständige Modell- und Beschreibungsprüfung '
                    'ist noch offen. Bitte den Entwurf prüfen.'))
            if not passed:
                if summary['candidate_evaluations'] == 0:
                    job['message'] += ' Für dieses Motiv wurde keine zusätzliche Modellsuche ausgeführt; Wiederholen allein erschliesst keine neue Lösung.'
                else:
                    job['message'] += f" Die Modellsuche hat {summary['candidate_evaluations']} Kandidaten geprüft."
                    if summary['stop_reason'] == 'supported_models_exhausted':
                        job['message'] += (' Die verfügbaren Modelle sind ausgeschöpft; ein weiterer Versuch '
                                           'kann wieder beim gleichen Ergebnis enden.')
    else:
        job.update(status="error", quality="unknown", result=False,
                   message="Kein verwendbares SVG erzeugt. Beschreibung prüfen; Details stehen im Protokoll.")


def search_summary(output: Path) -> dict | None:
    """Expose actual search work; a different seed alone is no exploration."""
    path = output / 'search' / 'progress.jsonl'
    if not path.is_file():
        return None
    result = None
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            try:
                event = json.loads(line)
                if event.get('event') in {'image_search_finished', 'image_search_context_finished'}:
                    result = {key: event.get(key) for key in
                              ('candidate_evaluations', 'stop_reason', 'satisfactory',
                               'elapsed_seconds', 'minimum_seconds', 'limit_seconds',
                               'renderings', 'render_budget', 'render_cache_hits',
                               'render_sequence_sha256', 'search_seed', 'global_stop_reason')}
            except (ValueError, AttributeError):
                continue
    return result if result and isinstance(result['candidate_evaluations'], int) else None


def vector_comparison_score(quality: dict) -> float:
    # A smaller global pixel error alone rewards the broken crossing/contour
    # seen in the reported retry. Compare visible edges and foreground too.
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_quality_score
    return vector_quality_score(quality)


def saved_svg_quality(source: Path, svg: Path) -> dict | None:
    from PIL import Image
    import numpy as np
    from src.imageConverterSample import prepare_sample, render_svg
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality
    from src.iCCModules.imageCompositeConverterCanvas import within_canvas
    try:
        with Image.open(source) as image:
            target = np.asarray(image.convert('RGB'))
        h, w = target.shape[:2]
        prepared = prepare_sample(svg.read_bytes(), w, h)
        rendered = render_svg(prepared, w, h)
        quality = vector_candidate_quality(target, rendered, prepared)
        quality['within_canvas'] = within_canvas(prepared, w, h)
        quality['passed'] = bool(quality['passed'] and quality['within_canvas'])
        border = np.concatenate((target[0], target[-1], target[:, 0], target[:, -1]))
        background = np.median(border.astype(float), axis=0)
        quality.update(observed_foreground_pixels=int(np.count_nonzero(
            np.max(abs(target.astype(float)-background), axis=2) > 25)),
            output_foreground_pixels=int(np.count_nonzero(
                np.max(abs(rendered.astype(float)-background), axis=2) > 25)))
        return quality
    except (ValueError, SyntaxError, OSError, RuntimeError):
        return None


class Workbench:
    """Own one background diagnostic batch; reports and old attempts stay on disk."""
    def __init__(self, jobs: Jobs):
        self.jobs = jobs
        self.directory = jobs.directory / 'workbench'
        self.directory.mkdir(exist_ok=True)
        self.process = None
        self.active_id = None
        for folder in self.directory.iterdir():
            if folder.is_dir() and re.fullmatch(r'[0-9a-f]{32}', folder.name):
                self.finish(folder, 'interrupted')

    def folder(self, run_id):
        folder = self.directory / run_id
        if not re.fullmatch(r'[0-9a-f]{32}', run_id) or not (folder / 'report.json').is_file():
            raise RequestError('Dieser Workbench-Lauf wurde nicht gefunden.', 404)
        return folder

    def finish(self, folder, status):
        from tools.plan_b_workbench import read_report, save_report
        if not (folder / 'report.json').exists():
            return
        report = read_report(folder)
        if report['status'] == 'running':
            report.update(status=status, active_case=None)
            for attempt in report['attempts']:
                if attempt['status'] == 'running':
                    attempt.update(status=status, finished=time.time())
            save_report(folder, report)

    def busy(self):
        if self.process is not None and self.process.poll() is not None:
            self.finish(self.folder(self.active_id), 'error' if self.process.returncode else 'interrupted')
            self.process = None
            self.active_id = None
        return self.process is not None

    def snapshot(self, run_id):
        from tools.plan_b_workbench import read_report, summary
        with self.jobs.lock:
            self.busy()
            report = read_report(self.folder(run_id))
            return dict(report, seed=str(report['seed']), id=run_id, summary=summary(report))

    def prepare(self, payload):
        from tools.plan_b_workbench import prepare
        with self.jobs.lock:
            run_id = uuid.uuid4().hex
            try:
                seed = payload.get('seed')
                if isinstance(seed, str):
                    if not re.fullmatch(r'[0-9]{1,19}', seed):
                        raise ValueError('Bitte einen ganzzahligen Seed zwischen 0 und 2^64−1 eingeben.')
                    seed = int(seed)
                prepare(payload.get('svg', ''), payload.get('description', ''), self.directory / run_id,
                        seed=seed, name=payload.get('name', 'Motiv.svg'))
            except (ValueError, SyntaxError) as exc:
                raise RequestError(str(exc)) from exc
            return self.snapshot(run_id)

    def inspect(self, payload):
        from tools.plan_b_workbench import inspect_svg
        try:
            preview = inspect_svg(payload.get('svg', ''))
            description = find_svg_description(payload.get('name', 'Motiv.svg'))
            return dict(preview, **description)
        except (ValueError, SyntaxError) as exc:
            raise RequestError(str(exc)) from exc

    def reprepare(self, run_id, payload):
        from tools.plan_b_workbench import read_report, save_report
        with self.jobs.lock:
            folder = self.folder(run_id)
            previous = read_report(folder)
            if previous['status'] == 'running':
                raise RequestError('Bitte die laufende Aufgabe zuerst beenden.', 409)
            result = self.prepare(dict(svg=(folder / 'source.svg').read_text(encoding='utf-8'),
                                       description=payload.get('description', previous['source_description']),
                                       name=previous['name'], seed=payload.get('seed', previous['seed'])))
            new_folder = self.folder(result['id'])
            report = read_report(new_folder)
            report['reprepared_from'] = run_id
            save_report(new_folder, report)
            return self.snapshot(result['id'])

    def from_job(self, job_id, payload=None):
        with self.jobs.lock:
            job = self.jobs.snapshot(job_id)
            if job['status'] != 'done' or not job.get('result') or job.get('quality') != 'passed':
                raise RequestError('Bitte zuerst ein SVG mit bestandener Qualitätsprüfung erstellen.', 409)
            description = (payload or {}).get('description', job['description'])
            if not isinstance(description, str) or not 1 <= len(description.strip()) <= 12000:
                raise RequestError("Bitte eine Bildbeschreibung mit 1 bis 12'000 Zeichen eingeben.")
            description = description.strip()
            if job.get('workbench_id'):
                previous = self.snapshot(job['workbench_id'])
                if previous['source_description'] == description:
                    return previous
            folder = self.jobs.folder(job_id)
            quality = saved_svg_quality(folder / 'source.png', folder / 'result.svg')
            if not quality or not quality['passed']:
                raise RequestError('Das gespeicherte SVG besteht die erneute Pixelprüfung nicht.', 409)
            report = self.prepare(dict(svg=(folder / 'result.svg').read_text(encoding='utf-8'),
                                       description=description, name=Path(job['name']).stem + '.svg'))
            from tools.plan_b_workbench import read_report, save_report
            run_folder = self.folder(report['id'])
            stored = read_report(run_folder)
            stored['source_job_id'] = job_id
            stored['source_raster_sha256'] = job.get('source_sha256')
            save_report(run_folder, stored)
            self.jobs.jobs[job_id]['workbench_id'] = report['id']
            self.jobs.save(self.jobs.jobs[job_id])
            return self.snapshot(report['id'])

    def start(self, run_id, payload):
        from tools.plan_b_workbench import read_report, save_report
        with self.jobs.lock:
            if self.jobs.closed or self.busy() or self.jobs.busy():
                raise RequestError('Es läuft bereits eine Konvertierung. Bitte warten oder abbrechen.', 409)
            folder = self.folder(run_id)
            report = read_report(folder)
            cases = payload.get('cases')
            known = {c['case_id'] for c in report['cases']}
            iterations, timeout = payload.get('iterations', 64), payload.get('timeout', 60)
            if not isinstance(cases, list) or not cases or any(not isinstance(c, str) or c not in known for c in cases) or len(set(cases)) != len(cases):
                raise RequestError('Bitte mindestens einen gültigen Fall auswählen.')
            if type(iterations) is not int or not 1 <= iterations <= 4096 or type(timeout) not in (int, float) or not 1 <= timeout <= 600:
                raise RequestError('Suchbudget: 1–4096 Iterationen; Zeitlimit: 1–600 Sekunden je Fall.')
            command = [sys.executable, '-m', 'tools.plan_b_workbench', '--run-dir', str(folder),
                       '--iterations', str(iterations), '--timeout-seconds', str(timeout), '--cases', *cases]
            environment = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONHASHSEED='0')
            report['status'] = 'running'
            save_report(folder, report)
            try:
                with (folder / 'console.log').open('a', encoding='utf-8') as log:
                    self.process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log,
                                                    stderr=subprocess.STDOUT,
                                                    **({'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}))
            except OSError as exc:
                self.finish(folder, 'error')
                raise RequestError(f'Die Rückkonvertierung konnte nicht gestartet werden: {exc}') from exc
            self.active_id = run_id
            return dict(self.snapshot(run_id), status='running')

    def cancel(self, run_id):
        with self.jobs.lock:
            folder = self.folder(run_id)
            if self.busy() and self.active_id == run_id:
                stop_process_tree(self.process)
                self.process, self.active_id = None, None
                self.finish(folder, 'cancelled')
            return self.snapshot(run_id)

    def note(self, run_id, payload):
        from tools.plan_b_workbench import read_report, save_report
        with self.jobs.lock:
            if self.busy() and self.active_id == run_id:
                raise RequestError('Bitte vor dem Speichern der Notiz den Lauf beenden.', 409)
            folder = self.folder(run_id)
            report = read_report(folder)
            case_id, note = payload.get('case_id'), payload.get('note')
            if case_id not in {c['case_id'] for c in report['cases']} or not isinstance(note, str) or len(note) > 12000:
                raise RequestError('Ungültiger Fall oder zu lange Notiz.')
            report['notes'][case_id] = note
            save_report(folder, report)
            return self.snapshot(run_id)

    def export_data(self, run_id, kind):
        from tools.plan_b_workbench import export_csv
        if not isinstance(kind, str) or kind not in {'report', 'csv', 'bundle'}:
            raise RequestError('Unbekanntes Exportformat.')
        with self.jobs.lock:
            report = self.snapshot(run_id)
            if kind == 'report':
                return (json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'),
                        'application/json; charset=utf-8', 'report.json')
            if kind == 'csv':
                return export_csv(report), 'text/csv; charset=utf-8', 'workbench.csv'
            if report['status'] == 'running':
                raise RequestError('Bitte den Lauf vor dem Export beenden.', 409)
            folder = self.folder(run_id)
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for entry in folder.rglob('*'):
                    if entry.is_file():
                        archive.write(entry, entry.relative_to(folder).as_posix())
                archive.writestr('workbench.csv', export_csv(report))
            return buffer.getvalue(), 'application/zip', 'plan-b-workbench.zip'

    def save_export(self, run_id, payload):
        kind = payload.get('format')
        data, _, filename = self.export_data(run_id, kind)
        if not self.jobs.save_lock.acquire(blocking=False):
            raise RequestError('Ein Speicherdialog ist bereits geöffnet.', 409)
        try:
            extension = filename.rsplit('.', 1)[-1]
            file_filter = {'report': 'JSON-Bericht (*.json)|*.json',
                           'csv': 'CSV-Messdaten (*.csv)|*.csv',
                           'bundle': 'ZIP-Archiv (*.zip)|*.zip'}[kind]
            with tempfile.TemporaryDirectory(prefix='imageconverter-export-') as directory:
                source = Path(directory)/filename
                source.write_bytes(data)
                result = save_file_dialog(source, filename,
                    self.jobs.dialog_locations.get('workbench_export', ''),
                    file_filter=file_filter, default_extension=extension)
            if result.get('saved'):
                self.jobs.remember_location('workbench_export', Path(result['path']).parent)
            return result
        finally:
            self.jobs.save_lock.release()

    def close(self):
        if self.busy():
            self.cancel(self.active_id)


class GuiServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != 'nt'

    def __init__(self, address: tuple[str, int], jobs: Jobs | None = None, *, directory: Path | None = None):
        self.jobs = jobs
        self.workbench = self.catalog = self.catalog_conversion = self.catalog_updates = None
        self.shutdown_requested = threading.Event()
        self.shutdown_complete = threading.Event()
        self.shutdown_response_sent = threading.Event()
        self._bound = False
        # Bind before reading persisted jobs: a second launch must not mark
        # the running server's conversions as interrupted.
        super().__init__(address, Handler)
        self._bound = True
        try:
            if self.jobs is None:
                self.jobs = Jobs(directory if directory is not None else ROOT/'artifacts/gui')
            self.workbench = Workbench(self.jobs)
            self.catalog = CatalogQuality(ROOT, self.jobs.directory/'catalog-quality', stop_process_tree)
            self.jobs.recognizer.payload_loader = self.catalog.payload
            from src.imageConverterDescriptionStore import DescriptionStore
            self.jobs.description_store = DescriptionStore(ROOT)
            self.collection = CategoryCollection(ROOT, self.catalog, self.jobs)
            self.catalog_conversion = CatalogConversion(self.catalog, self.jobs, self.workbench)
            self.catalog_updates = CatalogUpdates(self.catalog, self.jobs)
        except Exception:
            self.server_close()
            raise

    def server_bind(self):
        if os.name == 'nt':
            # SO_REUSEADDR on Windows lets old and new processes listen on
            # the same port and serve incompatible APIs at the same URL.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def server_close(self):
        for manager in (self.catalog_conversion, self.catalog_updates, self.catalog, self.workbench):
            if manager is not None:
                manager.close()
        if self._bound and self.jobs is not None:
            self.jobs.close()
        super().server_close()
        self.shutdown_complete.set()


class Handler(BaseHTTPRequestHandler):
    server: GuiServer

    def log_message(self, format: str, *args) -> None:
        pass

    def respond(self, data: bytes, mime: str, status: int = 200, download: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob:; object-src 'none'; frame-ancestors 'none'")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.end_headers()
        self.wfile.write(data)

    def json(self, payload: object, status: int = 200) -> None:
        self.respond(json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                     "application/json; charset=utf-8", status)

    def file(self, path: Path, mime: str, download: str | None = None) -> None:
        if not path.is_file():
            raise RequestError("Datei noch nicht verfügbar.", 404)
        self.respond(path.read_bytes(), mime, download=download)

    def handle_request(self) -> None:
        try:
            jobs = self.server.jobs
            addresses = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if self.headers.get("Host") not in addresses:
                raise RequestError("Unzulässiger Host.", 403)
            url = urlsplit(self.path)
            path = url.path
            name = parse_qs(url.query).get("name", ["Bild"])[0]
            match = re.fullmatch(r"/api/jobs/([0-9a-f]{32})(?:/([a-z]+)(/remove)?)?", path)
            static = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/catalog": ("catalog.html", "text/html; charset=utf-8"),
                      "/catalog.js": ("catalog.js", "text/javascript; charset=utf-8"),
                      "/catalog.css": ("catalog.css", "text/css; charset=utf-8"),
                      "/collection": ("collection.html", "text/html; charset=utf-8"),
                      "/collection.js": ("collection.js", "text/javascript; charset=utf-8"),
                      "/collection.css": ("collection.css", "text/css; charset=utf-8"),
                      "/workbench": ("workbench.html", "text/html; charset=utf-8"),
                      "/workbench.js": ("workbench.js", "text/javascript; charset=utf-8"),
                      "/workbench.css": ("workbench.css", "text/css; charset=utf-8"),
                      "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/attempts": ("attempts.html", "text/html; charset=utf-8"),
                      "/attempts.js": ("attempts.js", "text/javascript; charset=utf-8"),
                      "/attempts.css": ("attempts.css", "text/css; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            if self.command == "GET":
                if path == '/api/config':
                    return self.json(dict(native_file_dialogs=os.name == 'nt',
                        application='imageconverter_gui', api_version=1,
                        workbench_native_exports=True,
                        workbench_description_updates=True,
                        parallel_background_conversion=True,
                        editable_search_seed=True,
                        seeded_template_search=True,
                        simple_native_forms=True,
                        image_recognition=True,
                        description_check=True,
                        description_autosave=True,
                        current_svg_reuse=True,
                        primitive_exploration=True,
                        scoped_primitive_paint=True,
                        three_wing_valve=True,
                        partitioned_rhombus=True,
                        manual_svg_export=True,
                        project_root=str(ROOT.resolve()), data_directory=str(jobs.directory)))
                if path in static:
                    filename, mime = static[path]
                    return self.file(WEB / filename, mime)
                reference = re.fullmatch(r'/api/recognition/reference/([0-9a-f]{64})/(source|svg)', path)
                if reference:
                    asset = jobs.recognizer.asset(*reference.groups())
                    if asset is None:
                        raise RequestError('Diese Bildreferenz ist nicht mehr verfügbar.', 404)
                    if reference[2] == 'source':
                        from src.imageConverterRecognition import rgb_image
                        buffer = io.BytesIO()
                        rgb_image(asset).save(buffer, format='PNG')
                        return self.respond(buffer.getvalue(), 'image/png')
                    return self.file(asset, 'image/svg+xml')
                if path == '/api/collection':
                    return self.json(self.server.collection.payload())
                if path.startswith('/api/workbench'):
                    return self.workbench_get(path, url.query)
                if path.startswith('/api/catalog'):
                    return self.catalog_get(path, url.query)
                if path == "/api/jobs":
                    with jobs.lock:
                        foreground = parse_qs(url.query).get('scope') == ['foreground']
                        ids = sorted((key for key, job in jobs.jobs.items()
                                      if not foreground or not job.get('catalog_background')),
                                     key=lambda key: jobs.jobs[key]["created"], reverse=True)[:20]
                        return self.json([jobs.snapshot(key) for key in ids])
                if match and not match[3]:
                    job_id, asset, _ = match.groups()
                    job = jobs.snapshot(job_id)
                    if not asset:
                        return self.json(job)
                    if asset == 'attempts':
                        from src.imageConverterPreview import AttemptJournal
                        journal = AttemptJournal(jobs.folder(job_id))
                        query = parse_qs(url.query)
                        try:
                            if 'number' in query:
                                record = journal.read(int(query['number'][0]))
                                return self.respond(record['svg'].encode('utf-8'), 'image/svg+xml')
                            after = int(query.get('after', ['0'])[0])
                            if after < 0:
                                raise ValueError
                        except (ValueError, IndexError):
                            raise RequestError('Dieser Suchversuch wurde nicht gefunden.', 404)
                        return self.json(journal.page(after))
                    if asset == 'export':
                        with jobs.lock:
                            source = jobs.export_file(job_id)
                            if source is None:
                                raise RequestError('Noch kein SVG zum Speichern verfügbar.', 404)
                            content = source.read_bytes()
                        download = 'result.svg' if 'download' in parse_qs(url.query) else None
                        return self.respond(content, 'image/svg+xml', download=download)
                    assets = {"source": ("source.png", "image/png"), "sample": ("sample.svg", "image/svg+xml"),
                              "preview": (jobs.preview_file(job_id).name, "image/svg+xml"),
                              "result": ("result.svg", "image/svg+xml"), "log": ("console.log", "text/plain; charset=utf-8")}
                    if asset in assets and (asset not in {"result", "sample", "preview"} or job.get(asset)):
                        filename, mime = assets[asset]
                        download = "result.svg" if "download" in parse_qs(url.query) else None
                        return self.file(jobs.folder(job_id) / filename, mime, download)
            else:
                origin = self.headers.get("Origin")
                if (origin and origin not in {"http://" + address for address in addresses}) or self.headers.get("X-ImageConverter") != "1":
                    raise RequestError("Anfragen sind nur aus der lokalen Oberfläche erlaubt.", 403)
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_UPLOAD:
                    raise RequestError("Bitte eine Datei mit maximal 25 MB auswählen.", 413)
                self.connection.settimeout(30)
                data = self.rfile.read(length)
                if len(data) != length:
                    raise RequestError("Upload unvollständig.")
                if path == '/api/shutdown':
                    self.server.shutdown_requested.set()
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    try:
                        if not self.server.shutdown_complete.wait(timeout=90):
                            raise RequestError('Der Webserver hat das Beenden noch nicht abgeschlossen.', 503)
                        self.json(dict(status='stopped', message='Der Webserver ist gestoppt.'))
                    finally:
                        self.server.shutdown_response_sent.set()
                    return
                if path == "/api/upload":
                    return self.json(jobs.upload(name, data), 201)
                if path == '/api/pick':
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError('Ungültige Anfrage.')
                    return self.json(jobs.pick(payload))
                collection_case = re.fullmatch(r'/api/collection/([a-z_]{1,64})/load', path)
                if collection_case:
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError('Ungültige Anfrage.')
                    return self.json(self.server.collection.load(collection_case[1], fresh=payload.get('fresh',False)), 201)
                if path in {'/api/catalog/conversion/start','/api/catalog/conversion/stop'}:
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError('Ungültige Anfrage.')
                    operation = self.server.catalog_conversion
                    return self.json(operation.start(payload.get('profile','normal')) if path.endswith('/start') else operation.cancel())
                if path == '/api/catalog/delete':
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError('Ungültige Anfrage.')
                    return self.json(self.server.catalog.delete_images(payload.get('filenames')))
                if path in {'/api/catalog/start','/api/catalog/cancel'}:
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError('Ungültige Anfrage.')
                    operation = self.server.catalog
                    if operation.conversion_owner is not None:
                        raise RequestError('Bitte zuerst den Hintergrunddienst stoppen.', 409)
                    return self.json(operation.start(payload.get('force',False)) if path.endswith('/start') else operation.cancel())
                if path.startswith('/api/workbench/'):
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError('Ungültige Anfrage.')
                    workbench = self.server.workbench
                    if path == '/api/workbench/inspect':
                        return self.json(workbench.inspect(payload))
                    if path == '/api/workbench/prepare':
                        return self.json(workbench.prepare(payload), 201)
                    wb = re.fullmatch(r'/api/workbench/([0-9a-f]{32})/(start|cancel|note|reprepare|export)', path)
                    if wb:
                        run_id, action = wb.groups()
                        if action == 'export':
                            return self.json(workbench.save_export(run_id, payload))
                        return self.json(workbench.cancel(run_id) if action == 'cancel' else getattr(workbench, action)(run_id, payload))
                if match:
                    job_id, action, remove = match.groups()
                    if action == "sample":
                        return self.json(jobs.attach_sample(job_id, name, None if remove else data))
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError("Ungültige Anfrage.")
                    if not remove and action == "start":
                        with jobs.lock:
                            if self.server.workbench.busy():
                                raise RequestError('In der Workbench läuft eine Konvertierung.', 409)
                            return self.json(jobs.start(job_id, payload.get("description", ""),
                                                        payload.get("profile", "normal"), seed=payload.get('seed'),
                                                        use_current_svg=payload.get('use_current_svg',True)))
                    if not remove and action == 'recognize':
                        return self.json(jobs.recognize(job_id))
                    if not remove and action == 'description':
                        return self.json(jobs.save_description(job_id, payload.get('description')))
                    if not remove and action == 'check':
                        return self.json(jobs.check_description(job_id, payload.get('description')))
                    if not remove and action in {"cancel", "save"}:
                        operation = jobs.cancel if action == "cancel" else jobs.save_as
                        return self.json(operation(job_id))
                    if not remove and action == 'workbench':
                        return self.json(self.server.workbench.from_job(job_id, payload), 201)
            raise RequestError("Nicht gefunden.", 404)
        except (RequestError, CatalogError) as exc:
            self.json({"error": str(exc)}, exc.status)
        except (ValueError, TypeError):
            self.json({"error": "Ungültige Anfrage."}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass

    do_GET = do_POST = handle_request

    def catalog_get(self, path, query):
        catalog = self.server.catalog
        if path == '/api/catalog/conversion':
            return self.json(self.server.catalog_conversion.snapshot())
        if path == '/api/catalog':
            return self.json(catalog.snapshot())
        if path == '/api/catalog/list':
            return self.json(catalog.payload())
        if path == '/api/catalog/csv':
            return self.respond(catalog.export_csv(), 'text/csv; charset=utf-8', download='konvertierungsqualitaet.csv')
        if path == '/api/catalog/json':
            return self.respond(json.dumps(catalog.payload(),ensure_ascii=False).encode('utf-8'),
                                'application/json; charset=utf-8', download='konvertierungsqualitaet.json')
        if path == '/api/catalog/log':
            snapshot = catalog.snapshot()
            if not snapshot.get('id'):
                raise RequestError('Noch kein Prüfprotokoll vorhanden.',404)
            return self.file(catalog.directory/snapshot['id']/'console.log','text/plain; charset=utf-8')
        if path == '/api/catalog/asset':
            relative = parse_qs(query).get('path',[''])[0]
            target = catalog.asset(relative)
            mime = {'.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg',
                    '.gif':'image/gif','.webp':'image/webp','.bmp':'image/bmp',
                    '.tif':'image/tiff','.tiff':'image/tiff'}.get(target.suffix.lower(),'text/plain; charset=utf-8')
            return self.file(target,mime)
        raise RequestError('Nicht gefunden.',404)

    def workbench_get(self, path, query):
        workbench = self.server.workbench
        if path == '/api/workbench':
            runs = []
            for report_path in sorted(workbench.directory.glob('*/report.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
                report = workbench.snapshot(report_path.parent.name)
                runs.append({k: report[k] for k in ('id', 'name', 'created', 'seed', 'status', 'summary', 'active_case')})
            return self.json(runs)
        match = re.fullmatch(r'/api/workbench/([0-9a-f]{32})(?:/(report|csv|bundle|asset|description))?', path)
        if not match:
            raise RequestError('Nicht gefunden.', 404)
        run_id, asset = match.groups()
        if asset in {'report', 'csv', 'bundle'}:
            data, mime, filename = workbench.export_data(run_id, asset)
            return self.respond(data, mime, download=filename)
        report = workbench.snapshot(run_id)
        if asset == 'description':
            return self.json(find_svg_description(report['name']))
        folder = workbench.folder(run_id)
        if asset is None:
            return self.json(report)
        relative = parse_qs(query).get('path', [''])[0]
        target = (folder / relative).resolve()
        if not target.is_relative_to(folder.resolve()) or target.suffix.lower() not in {'.png', '.svg', '.log', '.json', '.jsonl', '.txt'}:
            raise RequestError('Unzulässige Artefaktdatei.', 403)
        mime = {'.png': 'image/png', '.svg': 'image/svg+xml'}.get(target.suffix.lower(), 'text/plain; charset=utf-8')
        return self.file(target, mime, 'result.svg' if 'download' in parse_qs(query) else None)


def existing_gui(port: int, directory: Path, *, warn_outdated: bool = False) -> str | None:
    """Reuse only this project's server with the requested data directory."""
    url = f'http://127.0.0.1:{port}'
    try:
        # A local server probe must not depend on configured HTTP proxies.
        with build_opener(ProxyHandler({})).open(url+'/api/config', timeout=3) as response:
            config = json.loads(response.read(65536))
        if (isinstance(config, dict) and config.get('application') == 'imageconverter_gui'
                and config.get('api_version') == 1
                and isinstance(config.get('project_root'), str)
                and isinstance(config.get('data_directory'), str)
                and Path(config['project_root']).resolve() == ROOT.resolve()
                and Path(config['data_directory']).resolve() == directory.resolve()):
            if warn_outdated and not config.get('parallel_background_conversion'):
                print('Der laufende Webserver verwendet noch eine ältere Version, die '
                      'manuelle Konvertierungen während des Hintergrunddienstes blockieren kann. '
                      'Bitte stopWebServer.cmd und danach startWebServer.cmd ausführen; '
                      'anschliessend die Browserseite neu laden.', flush=True)
            return url
    except (OSError, ValueError):
        pass
    return None


def stop_gui(port: int, directory: Path) -> int:
    """Stop only the local server belonging to this project and data directory."""
    url = existing_gui(port, directory)
    if url is None:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                pass
        except (ConnectionRefusedError, TimeoutError):
            print('Der ImageConverter-Webserver ist bereits gestoppt.', flush=True)
            return 0
        except OSError as exc:
            print(f'Der Webserver konnte nicht erreicht werden: {exc}', file=sys.stderr)
            return 1
        print('Auf diesem Port läuft kein passender ImageConverter-Webserver. '
              'Bitte Port und --data-dir prüfen.', file=sys.stderr)
        return 1
    request = Request(url+'/api/shutdown', data=b'{}', headers={'X-ImageConverter': '1',
                      'Content-Type': 'application/json'})
    try:
        print('Webserver wird beendet; laufende Aufgaben werden abgebrochen …', flush=True)
        with build_opener(ProxyHandler({})).open(request, timeout=95) as response:
            result = json.loads(response.read(65536))
        if not isinstance(result, dict) or result.get('status') != 'stopped':
            raise ValueError('Der Webserver hat das Beenden nicht bestätigt.')
        print('ImageConverter-Webserver gestoppt.', flush=True)
        return 0
    except (OSError, ValueError) as exc:
        print(f'Webserver konnte nicht gestoppt werden: {exc}', file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument('--stop', action='store_true', help='Passenden lokalen Webserver samt Aufgaben beenden.')
    parser.add_argument("--data-dir", type=Path, default=ROOT / "artifacts" / "gui")
    args = parser.parse_args(argv)
    if args.stop:
        return stop_gui(args.port, args.data_dir)
    from src.iCCModules.imageCompositeConverterDependencies import activate_vendored_site_packages
    activate_vendored_site_packages()
    print('ImageConverter wird gestartet; gespeicherte Aufträge werden geladen '
          'und bei Bedarf erneut geprüft …', flush=True)
    try:
        server = GuiServer(("127.0.0.1", args.port), directory=args.data_dir)
        jobs = server.jobs
    except OSError as exc:
        existing = existing_gui(args.port, args.data_dir, warn_outdated=True)
        if existing:
            print(f'ImageConverter läuft bereits: {existing}\nDie vorhandene Instanz wird verwendet.', flush=True)
            if not args.no_browser:
                webbrowser.open(existing)
            return 0
        print(f"GUI konnte nicht gestartet werden: {exc}\n"
              f"Falls Port {args.port} bereits belegt ist: den vorhandenen Webserver zuerst beenden.\n"
              "Für einen getrennten Server einen anderen Port und ein eigenes --data-dir wählen.", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"ImageConverter: {url}\nErgebnisse: {jobs.directory}\nBeenden mit Strg+C.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if server.shutdown_requested.is_set():
            server.shutdown_response_sent.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
