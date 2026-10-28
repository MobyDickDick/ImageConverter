"""GUI contracts: validated inputs, honest quality labels and isolated attempts."""
from __future__ import annotations

import io
import json
import subprocess
import sys

from PIL import Image
import pytest

from src import imageConverterGui as gui


def image_bytes(mode="RGB", color="white", size=(32, 24)):
    buffer = io.BytesIO()
    Image.new(mode, size, color).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, "catalog_descriptions", lambda: {"AC1234": "Ein blauer Kreis."})
    manager = gui.Jobs(tmp_path / "jobs")
    yield manager
    manager.close()


@pytest.fixture
def job(jobs):
    uploaded = jobs.upload("Mein Bild mit Umlaut ä.jpg", image_bytes())
    return jobs.jobs[uploaded["id"]]


def test_upload_normalizes_image_and_finds_family_description(jobs):
    job = jobs.upload("../../AC1234_L.jpg", image_bytes("RGBA", (255, 0, 0, 0)))
    assert job["name"] == "AC1234_L.jpg"
    assert job["description"] == "Ein blauer Kreis."
    with Image.open(jobs.folder(job["id"]) / "source.png") as image:
        assert image.size == (32, 24)
        assert image.mode == "RGB"
        assert image.getpixel((0, 0)) == (255, 255, 255)
    assert jobs.snapshot(job["id"])["status"] == "ready"


def test_rejects_corrupt_unsupported_and_oversized_inputs(jobs, monkeypatch):
    with pytest.raises(gui.RequestError):
        jobs.upload("bad.png", b"not an image")
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
    with pytest.raises(gui.RequestError):
        jobs.upload("bad.svg", svg)
    monkeypatch.setattr(gui, "MAX_PIXELS", 10)
    with pytest.raises(gui.RequestError, match="Megapixel"):
        jobs.upload("big.png", image_bytes())
    assert jobs.jobs == {}


def test_exif_orientation_is_applied(jobs):
    buffer = io.BytesIO()
    image = Image.new("RGB", (12, 8), "blue")
    exif = image.getexif()
    exif[274] = 6
    image.save(buffer, "JPEG", exif=exif)
    job = jobs.upload("phone.jpg", buffer.getvalue())
    assert (job["width"], job["height"]) == (8, 12)


def test_description_required_and_only_one_conversion_at_a_time(jobs):
    first = jobs.upload("first.png", image_bytes())
    second = jobs.upload("second.png", image_bytes())
    with pytest.raises(gui.RequestError, match="Bildbeschreibung"):
        jobs.start(first["id"], "  ", "quick")
    jobs.jobs[first["id"]]["status"] = "running"
    with pytest.raises(gui.RequestError) as exc:
        jobs.start(second["id"], "Ein Kreis", "quick")
    assert exc.value.status == 409
    jobs.jobs[first["id"]]["status"] = "ready"


@pytest.mark.parametrize("filename,returncode,failures,quality", [
    ("converted_svgs/UPLOAD.svg", 0, False, "passed"),
    ("converted_svgs/Failed_UPLOAD.svg", 0, False, "warning"),
    ("converted_svg_failed/Failed_UPLOAD.svg", 1, True, "warning"),
    ("converted_svgs/UPLOAD.svg", 0, True, "warning"),
    ("converted_svgs/UPLOAD.svg", 1, False, "warning"),
])
def test_result_quality_uses_cli_failures_and_failed_svg_names(jobs, job, filename, returncode, failures, quality):
    folder = jobs.folder(job["id"])
    svg = folder / "output" / filename
    svg.parent.mkdir(parents=True)
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle r="3"/></svg>')
    report = folder / "output" / "reports" / "batch_failure_summary.csv"
    report.parent.mkdir()
    report.write_text("filename;status\n" + ("UPLOAD.png;failed\n" if failures else ""))
    gui.collect_result(folder, job, returncode)
    assert job["quality"] == quality
    assert job["result"] is True
    assert (folder / "source.png").exists()
    assert (folder / "result.svg").read_bytes() == svg.read_bytes()


def test_no_svg_is_an_error_even_with_zero_cli_exit(jobs, job):
    gui.collect_result(jobs.folder(job["id"]), job, 0)
    assert job["status"] == "error"
    assert job["result"] is False


def test_catalog_references_and_multiline_user_text_reach_the_converter(tmp_path):
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingFromCsvImpl

    path = tmp_path / "description.csv"
    description = 'Wie AC1234, jedoch rot.\nBeschriftung: "M"; weisser Hintergrund.'
    gui.write_description_table(path, description, {"AC1234": "Ein blauer Kreis."})
    parsed = loadDescriptionMappingFromCsvImpl(str(path))
    assert parsed["UPLOAD"] == description
    assert parsed["AC1234"] == "Ein blauer Kreis."


def test_save_as_proposes_original_name_and_preserves_svg(jobs, job, monkeypatch, tmp_path):
    source = jobs.folder(job["id"]) / "result.svg"
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    job["result"] = True
    target = tmp_path / "Anderer Name.svg"

    def dialog(path, suggested):
        assert path == source
        assert suggested == "Mein Bild mit Umlaut ä.svg"
        target.write_bytes(path.read_bytes())
        return {"saved": True, "path": str(target)}

    monkeypatch.setattr(gui, "save_svg_dialog", dialog)
    result = jobs.save_as(job["id"])
    assert result == {"saved": True, "path": str(target)}
    assert target.read_bytes() == source.read_bytes()


def test_cancelled_save_keeps_result_and_releases_dialog_lock(jobs, job, monkeypatch):
    source = jobs.folder(job["id"]) / "result.svg"
    source.write_text("svg contents")
    job["result"] = True
    monkeypatch.setattr(gui, "save_svg_dialog", lambda *args: {"saved": False})
    assert jobs.save_as(job["id"]) == {"saved": False}
    assert source.read_text() == "svg contents"
    assert jobs.save_as(job["id"]) == {"saved": False}
    jobs.save_lock.acquire()
    try:
        with pytest.raises(gui.RequestError) as exc:
            jobs.save_as(job["id"])
        assert exc.value.status == 409
    finally:
        jobs.save_lock.release()


def test_save_requires_an_existing_result(jobs):
    uploaded = jobs.upload("Bild.png", image_bytes())
    with pytest.raises(gui.RequestError) as exc:
        jobs.save_as(uploaded["id"])
    assert exc.value.status == 404


def test_restart_recovers_result_and_marks_unfinished_jobs(jobs, job):
    job.update(status="running", started=0)
    jobs.save(job)
    restored = gui.Jobs(jobs.directory)
    assert restored.snapshot(job["id"])["status"] == "interrupted"
    assert restored.snapshot(job["id"])["description"] == job["description"]
    job["status"] = "ready"


def test_retry_keeps_previous_result_and_original(jobs, monkeypatch):
    uploaded = jobs.upload("image.png", image_bytes())
    old = jobs.jobs[uploaded["id"]]
    old.update(status="done", result=True)
    result = jobs.folder(old["id"]) / "result.svg"
    result.write_text("previous result")
    monkeypatch.setattr(jobs, "run", lambda job_id: None)
    retry = jobs.start(old["id"], "Ein Kreis", "quick")
    assert retry["id"] != old["id"]
    assert retry["result"] is False
    assert result.read_text() == "previous result"
    assert (jobs.folder(retry["id"]) / "source.png").read_bytes() == (jobs.folder(old["id"]) / "source.png").read_bytes()
    jobs.cancel(retry["id"])


def test_cancel_stops_a_real_background_process(jobs, job):
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {"start_new_session": True}
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], **options)
    try:
        job.update(status="running", started=0)
        jobs.processes[job["id"]] = process
        cancelled = jobs.cancel(job["id"])
        assert cancelled["status"] == "cancelled"
        assert process.poll() is not None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)


def test_routes_do_not_serve_arbitrary_files_or_cross_origin_requests(jobs, request):
    from http.client import HTTPConnection
    import threading

    server = gui.GuiServer(("127.0.0.1", 0), jobs)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def send(path, method="GET", headers="", data=b""):
        connection = HTTPConnection(*server.server_address, timeout=5)
        request_headers = dict(line.split(": ", 1) for line in headers.splitlines() if line)
        try:
            connection.request(method, path, body=data, headers=request_headers)
            response = connection.getresponse()
            return str(response.status).encode(), response.read()
        finally:
            connection.close()

    request.addfinalizer(server.server_close)
    request.addfinalizer(lambda: thread.join(timeout=5))
    request.addfinalizer(server.shutdown)

    assert b"200" in send("/")[0]
    assert b"404" in send("/../../README.md")[0]
    assert b"403" in send("/api/upload", "POST", "Origin: https://example.org\r\nX-ImageConverter: 1\r\n", image_bytes())[0]
    assert b"403" in send("/api/upload", "POST", "", image_bytes())[0]
    assert b"400" in send("/api/jobs/" + "a" * 32 + "/start", "POST", "X-ImageConverter: 1\r\n", b"[]")[0]
    head, body = send("/api/upload?name=test.png", "POST", "X-ImageConverter: 1\r\n", image_bytes())
    assert b"201" in head
    uploaded = json.loads(body)
    assert b"200" in send("/api/jobs/" + uploaded["id"] + "/source")[0]
    assert b"404" in send("/api/jobs/" + uploaded["id"] + "/result")[0]
