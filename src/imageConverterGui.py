"""Local browser GUI for the existing semantic-only converter.

Run with ``python -m src.imageConverterGui`` or startWebServer.cmd.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import uuid
import warnings
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
MAX_UPLOAD = 25 * 1024 * 1024
MAX_PIXELS = 20_000_000
PROFILES = {"quick": (15, 30), "normal": (60, 120), "thorough": (120, 240)}


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
    # Keep referenced descriptions (e.g. "Wie AC0401") available to the existing parser.
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Wurzelform", "Beschreibung"])
        writer.writerows(catalog.items())
        writer.writerow(["UPLOAD", description])


def save_svg_dialog(source: Path, suggested_name: str) -> dict:
    if os.name != "nt":
        raise RequestError("Der System-Speicherdialog ist unter Windows verfügbar. Bitte den Browser-Download verwenden.")
    environment = os.environ.copy()
    environment.update(ICC_GUI_SOURCE=str(source), ICC_GUI_FILENAME=suggested_name)
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


class Jobs:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.save_lock = threading.Lock()
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
            job_id = uuid.uuid4().hex
            folder = self.directory / job_id
            folder.mkdir()
            background.save(folder / "source.png")
            job = dict(id=job_id, name=name, width=background.width, height=background.height,
                       description=description, status="ready", created=time.time(),
                       message="Bild geladen. Beschreibung prüfen und Konvertierung starten.",
                       result=False, quality="unknown", profile="normal", elapsed=0)
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
            return save_svg_dialog(folder / "result.svg", name + ".svg")
        finally:
            self.save_lock.release()

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
        passed = returncode == 0 and not has_failures and result == candidates[0]
        job.update(status="done", result=True, quality="passed" if passed else "warning",
                   message=("SVG erstellt. Qualitätsprüfung bestanden." if passed else
                            "Entwurf erstellt. Die Qualitätsprüfung wurde nicht bestanden; bitte das Ergebnis prüfen."))
    else:
        job.update(status="error", quality="unknown", result=False,
                   message="Kein verwendbares SVG erzeugt. Beschreibung prüfen; Details stehen im Protokoll.")


class GuiServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], jobs: Jobs):
        self.jobs = jobs
        super().__init__(address, Handler)


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
                      "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            if self.command == "GET":
                if path in static:
                    filename, mime = static[path]
                    return self.file(WEB / filename, mime)
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
                if match:
                    job_id, action, remove = match.groups()
                    if action == "sample":
                        return self.json(jobs.attach_sample(job_id, name, None if remove else data))
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise RequestError("Ungültige Anfrage.")
                    if not remove and action == "start":
                        return self.json(jobs.start(job_id, payload.get("description", ""), payload.get("profile", "normal")))
                    if not remove and action in {"cancel", "save"}:
                        operation = jobs.cancel if action == "cancel" else jobs.save_as
                        return self.json(operation(job_id))
            raise RequestError("Nicht gefunden.", 404)
        except RequestError as exc:
            self.json({"error": str(exc)}, exc.status)
        except (ValueError, TypeError):
            self.json({"error": "Ungültige Anfrage."}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass

    do_GET = do_POST = handle_request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "artifacts" / "gui")
    args = parser.parse_args(argv)
    from src.iCCModules.imageCompositeConverterDependencies import activate_vendored_site_packages
    activate_vendored_site_packages()
    try:
        jobs = Jobs(args.data_dir)
        server = GuiServer(("127.0.0.1", args.port), jobs)
    except OSError as exc:
        print(f"GUI konnte nicht gestartet werden: {exc}\nAnderen Port mit --port 8767 wählen.", file=sys.stderr)
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
        jobs.close()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
