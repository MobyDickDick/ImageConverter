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
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from urllib.request import ProxyHandler, build_opener
import uuid
import warnings
import webbrowser
import zipfile

from src.imageConverterCatalog import CatalogError, CatalogQuality
from src.imageConverterCatalogConversion import CatalogConversion
from src.imageConverterCollection import CategoryCollection

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
MAX_UPLOAD = 25 * 1024 * 1024
MAX_PIXELS = 20_000_000
# Leave room after the 30-second effort floor for model comparison/finalization.
PROFILES = {"quick": (35, 45), "normal": (60, 120), "thorough": (120, 240)}


class RequestError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def catalog_descriptions() -> dict[str, str]:
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl

    descriptions = {}
    for folder in ("images_to_convert", "descriptions"):
        path = ROOT / "artifacts" / folder / "Finale_Wurzelformen_V3.xml"
        if path.is_file():
            descriptions.update(loadDescriptionMappingImpl(
                str(path), get_base_name_from_file_fn=getBaseNameFromFileImpl))
    return descriptions


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


def save_svg_dialog(source: Path, suggested_name: str, initial_directory: str = '') -> dict:
    if os.name != "nt":
        raise RequestError("Der System-Speicherdialog ist unter Windows verfügbar. Bitte den Browser-Download verwenden.")
    environment = os.environ.copy()
    environment.update(ICC_GUI_SOURCE=str(source), ICC_GUI_FILENAME=suggested_name,
                       ICC_GUI_INITIAL_DIRECTORY=initial_directory)
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
        self.threads: list[threading.Thread] = []
        self.closed = False
        self.descriptions = catalog_descriptions()
        # Keep recent results usable after a server restart.
        for path in self.directory.glob("*/job.json"):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
                if not re.fullmatch(r"[0-9a-f]{32}", job["id"]) or path.parent.name != job["id"]:
                    continue
                if job["status"] == "running":
                    job.update(status="interrupted", message="Der Server wurde während der Konvertierung beendet.")
                self.jobs[job["id"]] = job
                if job.get('quality') == 'passed' and job.get('result') and 'pixel_quality' not in job:
                    quality = saved_svg_quality(path.parent/'source.png', path.parent/'result.svg')
                    job['pixel_quality'] = quality
                    if quality and not quality['passed']:
                        job.update(quality='warning', message='Das gespeicherte SVG besteht die erneute Pixelprüfung nicht. Bitte den Entwurf prüfen oder ein Sample-SVG laden.')
                        if quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']:
                            job.update(status='error', result=False)
                    self.save(job)
            except (OSError, ValueError, KeyError):
                continue

    def folder(self, job_id: str) -> Path:
        if job_id not in self.jobs:
            raise RequestError("Dieser Auftrag wurde nicht gefunden.", 404)
        return self.directory / job_id

    def save(self, job: dict) -> None:
        folder = self.folder(job["id"])
        temporary = folder / "job.json.tmp"
        temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(folder / "job.json")

    def snapshot(self, job_id: str) -> dict:
        with self.lock:
            folder = self.folder(job_id)
            job = dict(self.jobs[job_id])
            if job["status"] == "running":
                job["elapsed"] = round(time.time() - job["started"], 1)
            log = folder / "console.log"
            if log.exists():
                with log.open("rb") as stream:
                    stream.seek(max(0, log.stat().st_size - 16000))
                    job["log"] = stream.read().decode("utf-8", errors="replace")
            else:
                job["log"] = ""
            return job

    def upload(self, name: str, data: bytes) -> dict:
        from PIL import Image, ImageOps, UnidentifiedImageError
        from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl

        name = name.replace("\\", "/").rsplit("/", 1)[-1][:180] or "Bild"
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as original:
                    if original.format not in {"PNG", "JPEG", "BMP", "WEBP", "TIFF"}:
                        raise RequestError("Bitte ein PNG-, JPEG-, BMP-, WebP- oder TIFF-Bild wählen.")
                    if original.width * original.height > MAX_PIXELS:
                        raise RequestError("Das Bild ist zu gross (maximal 20 Megapixel).")
                    image = ImageOps.exif_transpose(original).convert("RGBA")
                    background = Image.new("RGB", image.size, "white")
                    background.paste(image, mask=image.getchannel("A"))
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
                Image.DecompressionBombWarning) as exc:
            raise RequestError("Das Bild ist beschädigt, zu gross oder wird nicht unterstützt.") from exc
        keys = (name, Path(name).stem, getBaseNameFromFileImpl(name))
        description = next((self.descriptions[key.upper()] for key in keys
                            if key.upper() in self.descriptions), "")
        with self.lock:
            source_sha256 = hashlib.sha256(
                f'{background.width}x{background.height}:'.encode()+background.tobytes()).hexdigest()
            previous = next((job for job in sorted(self.jobs.values(), key=lambda j:j['created'], reverse=True)
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
            self.save(job)
            return self.snapshot(job_id)

    def start(self, job_id: str, description: str, profile: str) -> dict:
        if not isinstance(description, str) or not description.strip() or len(description) > 12000:
            raise RequestError("Bitte eine Bildbeschreibung mit 1 bis 12'000 Zeichen eingeben.")
        if profile not in PROFILES:
            raise RequestError("Unbekanntes Suchprofil.")
        with self.lock:
            if self.closed or any(job["status"] == "running" for job in self.jobs.values()):
                raise RequestError("Es läuft bereits eine Konvertierung. Bitte warten oder abbrechen.", 409)
            job = self.editable(job_id)
            job_id = job["id"]
            job.update(description=description.strip(), profile=profile, status="running",
                       description_origin='user',
                       search_seed=secrets.randbits(64),
                       started=time.time(), message="Sample wird am Original verbessert …" if job.get("sample") else "Bild wird konvertiert …")
            self.save(job)
            thread = threading.Thread(target=self.run, args=(job_id,), daemon=True)
            self.threads.append(thread)
            thread.start()
            return self.snapshot(job_id)

    def editable(self, job_id: str) -> dict:
        """Share retry/attachment preparation; completed results stay immutable."""
        folder = self.folder(job_id)
        previous = job = self.jobs[job_id]
        if job["status"] != "ready":
            copied = self.upload(job["name"], (folder / "source.png").read_bytes())
            job = self.jobs[copied["id"]]
            job.update(description=previous["description"], profile=previous["profile"])
            if previous.get("sample"):
                shutil.copyfile(folder / "sample.svg", self.folder(job["id"]) / "sample.svg")
                job.update(sample=True, sample_name=previous["sample_name"])
            job['previous_job_id'] = previous['id']
            for key in ('collection_case_id','collection_image_sha256','collection_label','collection_next_case_id'):
                if key in previous:
                    job[key] = previous[key]
        return job

    def run(self, job_id: str) -> None:
        folder = self.folder(job_id)
        job = self.jobs[job_id]
        process = None
        try:
            input_dir = folder / "input"
            input_dir.mkdir()
            shutil.copyfile(folder / "source.png", input_dir / "UPLOAD.png")
            descriptions = folder / "description.csv"
            write_description_table(descriptions, job["description"], self.descriptions)
            output = folder / "output"
            seconds, maximum = PROFILES[job["profile"]]
            command = [sys.executable, "-u", "-m", "src.imageCompositeConverter", str(input_dir),
                       "--descriptions-path", str(descriptions), "--output-dir", str(output),
                       "--start", "UPLOAD", "--end", "UPLOAD", "--execution-mode", "semantic-only",
                       "--search-seconds", str(seconds), "--search-max-seconds", str(maximum),
                       "--search-seed", str(job["search_seed"]),
                       "--fail-on-batch-failures", "--log-file", str(folder / "converter.local.log")]
            if job.get("sample"):
                description_file = folder / "description.txt"
                description_file.write_text(job["description"], encoding="utf-8")
                command = [sys.executable, "-u", "-m", "src.imageConverterSample",
                           "--source", str(folder / "source.png"), "--sample", str(folder / "sample.svg"),
                           "--output", str(output / "refined.svg"), "--description", str(description_file),
                           "--seconds", str(seconds)]
            environment = os.environ.copy()
            environment.update(PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8",
                               ICC_MAX_QUALITY_PASSES="0", ICC_CONVERSION_TIMEOUT_SEC=str(maximum))
            environment.setdefault("IMAGE_CONVERTER_ISOLATE_SVG_RENDER", "1")
            environment.setdefault("IMAGE_CONVERTER_REUSE_RENDER_WORKER", "1")
            options = ({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt"
                       else {"start_new_session": True})
            with (folder / "console.log").open("wb") as log:
                with self.lock:
                    if job["status"] != "running":
                        return
                    process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                               stdout=log, stderr=subprocess.STDOUT,
                                               stdin=subprocess.DEVNULL, **options)
                    self.processes[job_id] = process
                try:
                    # Cancellation terminates the process tree and releases this wait.
                    process.wait(timeout=maximum + 30)
                except subprocess.TimeoutExpired:
                    with self.lock:
                        stop_process_tree(process)
                        if job["status"] == "running":
                            job.update(status="timeout", message="Zeitlimit erreicht. Ein neues Suchprofil kann helfen.")
            with self.lock:
                if job["status"] == "running":
                    collect = collect_sample_result if job.get("sample") else collect_result
                    collect(folder, job, process.returncode)
                    previous = self.jobs.get(job.get('previous_job_id'))
                    if (job.get('result') and previous and previous.get('result')
                            and previous['description'] == job['description']):
                        same = ((folder / 'result.svg').read_bytes() ==
                                (self.folder(previous['id']) / 'result.svg').read_bytes())
                        job['same_as_previous'] = same
                        if same and job['quality'] == 'warning':
                            job['message'] += ' Die erneute Suche hat denselben besten Entwurf ergeben.'
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
            job.update(sample=prepared is not None, sample_name=name.replace("\\", "/").rsplit("/", 1)[-1][:180] if prepared else "")
            if prepared:
                (folder / "sample.svg").write_text(prepared, encoding="utf-8")
                job["message"] = "Original und Sample geladen. Vorhandene SVG-Formen werden am Original optimiert."
            else:
                job["message"] = "Sample entfernt. Das Original wird neu konvertiert."
            self.save(job)
            return self.snapshot(job_id)

    def save_as(self, job_id: str) -> dict:
        with self.lock:
            folder = self.folder(job_id)
            job = self.jobs[job_id]
            if not job["result"] or not (folder / "result.svg").is_file():
                raise RequestError("Noch kein SVG zum Speichern verfügbar.", 404)
            name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", Path(job["name"]).stem).rstrip(". ") or "Bild"
        if not self.save_lock.acquire(blocking=False):
            raise RequestError("Ein Speicherdialog ist bereits geöffnet.", 409)
        try:
            result = save_svg_dialog(folder / "result.svg", name + ".svg", self.dialog_locations.get('save', ''))
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
        """Re-measure both versions against this source; never replace with a draft."""
        job = self.jobs[job_id]
        if job.get('catalog_background'):
            return  # The background service keeps candidates for both catalog renderers.
        if job.get('status') != 'done' or not job.get('result') or job.get('quality') != 'passed':
            return
        folder = self.folder(job_id)
        quality = saved_svg_quality(folder / 'source.png', folder / 'result.svg')
        if not quality or not quality['passed']:
            job['project_save'] = dict(status='skipped', message='Keine Projektablage: erneute Pixelprüfung nicht bestanden.')
            return
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', Path(job['name']).stem).rstrip('. ') or 'Bild'
        if re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', name, re.I):
            name = '_' + name
        target = self.project_directory / 'converted_svgs' / (name + '.svg')
        if target.exists():
            previous = saved_svg_quality(folder / 'source.png', target)
            if previous is None:
                job['project_save'] = dict(status='skipped', message='Vorhandenes Projekt-SVG konnte nicht verglichen werden; es bleibt erhalten.')
                return
            if quality['normalized_mse'] >= previous['normalized_mse'] - 1e-12:
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
                                   message=f'Automatisch im Projekt gespeichert: {target}')

    def close(self) -> None:
        with self.lock:
            self.closed = True
            for job_id in list(self.jobs):
                if self.jobs[job_id]["status"] == "running":
                    self.cancel(job_id)
        for thread in self.threads:
            thread.join(timeout=20)


def collect_sample_result(folder: Path, job: dict, returncode: int) -> None:
    result = folder / "output" / "refined.svg"
    report_path = result.with_suffix(".json")
    if returncode != 0 or not result.is_file() or not report_path.is_file():
        job.update(status="error", result=False, quality="unknown", message="Sample konnte nicht verbessert werden. Details stehen im Protokoll.")
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    shutil.copyfile(result, folder / "result.svg")
    message = "Sample am Original verbessert." if report["improved"] else "Keine messbare Verbesserung gefunden. Der Sample-Stand bleibt erhalten."
    if report.get('stop_reason') == 'quality_target_reached':
        message = 'Das Sample erfüllt die Pixelprüfung bereits; seine Formen bleiben erhalten.'
    message += " Pixelprüfung bestanden." if report["passed"] else " Bitte den Entwurf prüfen; die Pixel- oder explizite Beschreibungsprüfung ist noch offen."
    job.update(status="done", result=True, quality="passed" if report["passed"] else "warning",
               message=message, sample_report=report)


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
        shutil.copyfile(result, folder / "result.svg")
        # A model can be shifted off-canvas and still receive a successful CLI
        # status. Re-render the saved vector against the actual uploaded image.
        quality = saved_svg_quality(folder / 'source.png', result)
        job['pixel_quality'] = quality
        if quality and quality['observed_foreground_pixels'] and not quality['output_foreground_pixels']:
            job.update(status='error', result=False, quality='warning',
                       message='Das SVG ist leer oder liegt ausserhalb der Zeichenfläche. Bitte die Beschreibung prüfen oder ein Sample-SVG laden.')
            return
        passed = (returncode == 0 and not has_failures and result == candidates[0]
                  and quality is not None and quality['passed'])
        job.update(status="done", result=True, quality="passed" if passed else "warning",
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
                                           'kann wieder beim gleichen fehlerhaften Aufbau landen.')
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
                if event.get('event') == 'image_search_finished':
                    result = {key: event.get(key) for key in
                              ('candidate_evaluations', 'stop_reason', 'satisfactory',
                               'elapsed_seconds', 'minimum_seconds', 'limit_seconds')}
            except (ValueError, AttributeError):
                continue
    return result if result and isinstance(result['candidate_evaluations'], int) else None


def saved_svg_quality(source: Path, svg: Path) -> dict | None:
    from PIL import Image
    import numpy as np
    from src.imageConverterSample import prepare_sample, render_svg
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
    try:
        with Image.open(source) as image:
            target = np.asarray(image.convert('RGB'))
        h, w = target.shape[:2]
        prepared = prepare_sample(svg.read_bytes(), w, h)
        rendered = render_svg(prepared, w, h)
        quality = pixel_quality(target, rendered)
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
                        raise ValueError('Bitte einen ganzzahligen Seed zwischen 0 und 2^63−1 eingeben.')
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
                                       description=previous['source_description'],
                                       name=previous['name'], seed=previous['seed']))
            new_folder = self.folder(result['id'])
            report = read_report(new_folder)
            report['reprepared_from'] = run_id
            save_report(new_folder, report)
            return self.snapshot(result['id'])

    def from_job(self, job_id):
        with self.jobs.lock:
            job = self.jobs.snapshot(job_id)
            if job['status'] != 'done' or not job.get('result') or job.get('quality') != 'passed':
                raise RequestError('Bitte zuerst ein SVG mit bestandener Qualitätsprüfung erstellen.', 409)
            if job.get('workbench_id'):
                return self.snapshot(job['workbench_id'])
            folder = self.jobs.folder(job_id)
            quality = saved_svg_quality(folder / 'source.png', folder / 'result.svg')
            if not quality or not quality['passed']:
                raise RequestError('Das gespeicherte SVG besteht die erneute Pixelprüfung nicht.', 409)
            report = self.prepare(dict(svg=(folder / 'result.svg').read_text(encoding='utf-8'),
                                       description=job['description'], name=Path(job['name']).stem + '.svg'))
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
            if self.jobs.closed or self.busy() or any(j['status'] == 'running' for j in self.jobs.jobs.values()):
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

    def close(self):
        if self.busy():
            self.cancel(self.active_id)


class GuiServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != 'nt'

    def __init__(self, address: tuple[str, int], jobs: Jobs | None = None, *, directory: Path | None = None):
        self.jobs = jobs
        self.workbench = self.catalog = self.catalog_conversion = None
        # Bind before reading persisted jobs: a second launch must not mark
        # the running server's conversions as interrupted.
        super().__init__(address, Handler)
        try:
            if self.jobs is None:
                self.jobs = Jobs(directory if directory is not None else ROOT/'artifacts/gui')
            self.workbench = Workbench(self.jobs)
            self.catalog = CatalogQuality(ROOT, self.jobs.directory/'catalog-quality', stop_process_tree)
            self.collection = CategoryCollection(ROOT, self.catalog, self.jobs)
            self.catalog_conversion = CatalogConversion(self.catalog, self.jobs, self.workbench)
        except Exception:
            self.server_close()
            if jobs is None and self.jobs is not None:
                self.jobs.close()
            raise

    def server_bind(self):
        if os.name == 'nt':
            # SO_REUSEADDR on Windows lets old and new processes listen on
            # the same port and serve incompatible APIs at the same URL.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def server_close(self):
        for manager in (self.catalog_conversion, self.catalog, self.workbench):
            if manager is not None:
                manager.close()
        super().server_close()


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
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            if self.command == "GET":
                if path == '/api/config':
                    return self.json(dict(native_file_dialogs=os.name == 'nt',
                        application='imageconverter_gui', api_version=1,
                        project_root=str(ROOT.resolve()), data_directory=str(jobs.directory)))
                if path in static:
                    filename, mime = static[path]
                    return self.file(WEB / filename, mime)
                if path == '/api/collection':
                    return self.json(self.server.collection.payload())
                if path.startswith('/api/workbench'):
                    return self.workbench_get(path, url.query)
                if path.startswith('/api/catalog'):
                    return self.catalog_get(path, url.query)
                if path == "/api/jobs":
                    with jobs.lock:
                        ids = sorted(jobs.jobs, key=lambda key: jobs.jobs[key]["created"], reverse=True)[:20]
                        return self.json([jobs.snapshot(key) for key in ids])
                if match and not match[3]:
                    job_id, asset, _ = match.groups()
                    job = jobs.snapshot(job_id)
                    if not asset:
                        return self.json(job)
                    assets = {"source": ("source.png", "image/png"), "sample": ("sample.svg", "image/svg+xml"),
                              "result": ("result.svg", "image/svg+xml"), "log": ("console.log", "text/plain; charset=utf-8")}
                    if asset in assets and (asset not in {"result", "sample"} or job.get(asset)):
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
                    wb = re.fullmatch(r'/api/workbench/([0-9a-f]{32})/(start|cancel|note|reprepare)', path)
                    if wb:
                        run_id, action = wb.groups()
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
                            return self.json(jobs.start(job_id, payload.get("description", ""), payload.get("profile", "normal")))
                    if not remove and action in {"cancel", "save"}:
                        operation = jobs.cancel if action == "cancel" else jobs.save_as
                        return self.json(operation(job_id))
                    if not remove and action == 'workbench':
                        return self.json(self.server.workbench.from_job(job_id), 201)
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
                runs.append({k: report[k] for k in ('id', 'name', 'created', 'seed', 'status', 'summary')})
            return self.json(runs)
        match = re.fullmatch(r'/api/workbench/([0-9a-f]{32})(?:/(report|csv|bundle|asset))?', path)
        if not match:
            raise RequestError('Nicht gefunden.', 404)
        run_id, asset = match.groups()
        report = workbench.snapshot(run_id)
        folder = workbench.folder(run_id)
        if asset in (None, 'report'):
            return self.respond(json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'),
                                'application/json; charset=utf-8', download='report.json' if asset else None)
        if asset == 'csv':
            from tools.plan_b_workbench import export_csv
            return self.respond(export_csv(report), 'text/csv; charset=utf-8', download='workbench.csv')
        if asset == 'bundle':
            if workbench.busy() and workbench.active_id == run_id:
                raise RequestError('Bitte den Lauf vor dem Export beenden.', 409)
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for entry in folder.rglob('*'):
                    if entry.is_file():
                        archive.write(entry, entry.relative_to(folder).as_posix())
                from tools.plan_b_workbench import export_csv
                archive.writestr('workbench.csv', export_csv(report))
            return self.respond(buffer.getvalue(), 'application/zip', download='plan-b-workbench.zip')
        relative = parse_qs(query).get('path', [''])[0]
        target = (folder / relative).resolve()
        if not target.is_relative_to(folder.resolve()) or target.suffix.lower() not in {'.png', '.svg', '.log', '.json', '.jsonl', '.txt'}:
            raise RequestError('Unzulässige Artefaktdatei.', 403)
        mime = {'.png': 'image/png', '.svg': 'image/svg+xml'}.get(target.suffix.lower(), 'text/plain; charset=utf-8')
        return self.file(target, mime, 'result.svg' if 'download' in parse_qs(query) else None)


def existing_gui(port: int, directory: Path) -> str | None:
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
            return url
    except (OSError, ValueError):
        pass
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "artifacts" / "gui")
    args = parser.parse_args(argv)
    from src.iCCModules.imageCompositeConverterDependencies import activate_vendored_site_packages
    activate_vendored_site_packages()
    try:
        server = GuiServer(("127.0.0.1", args.port), directory=args.data_dir)
        jobs = server.jobs
    except OSError as exc:
        existing = existing_gui(args.port, args.data_dir)
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
        jobs.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
