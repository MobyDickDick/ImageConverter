def _sniff_raster_size(path: str | Path) -> tuple[int, int]:
    file_path = Path(path)
    with file_path.open("rb") as fh:
        header = fh.read(32)

    if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
        return struct.unpack(">II", header[16:24])

    if header[:6] in {b"GIF87a", b"GIF89a"} and len(header) >= 10:
        return struct.unpack("<HH", header[6:10])

    if header.startswith(b"BM"):
        with file_path.open("rb") as fh:
            fh.seek(18)
            dib = fh.read(8)
        if len(dib) == 8:
            width, height = struct.unpack("<ii", dib)
            return abs(int(width)), abs(int(height))

    if header.startswith(b"\xff\xd8"):
        with file_path.open("rb") as fh:
            fh.seek(2)
            while True:
                marker_prefix = fh.read(1)
                if not marker_prefix:
                    break
                if marker_prefix != b"\xff":
                    continue
                marker = fh.read(1)
                while marker == b"\xff":
                    marker = fh.read(1)
                if marker in {b"\xd8", b"\xd9"}:
                    continue
                size_bytes = fh.read(2)
                if len(size_bytes) != 2:
                    break
                segment_size = struct.unpack(">H", size_bytes)[0]
                if marker in {
                    b"\xc0", b"\xc1", b"\xc2", b"\xc3",
                    b"\xc5", b"\xc6", b"\xc7",
                    b"\xc9", b"\xca", b"\xcb",
                    b"\xcd", b"\xce", b"\xcf",
                }:
                    payload = fh.read(5)
                    if len(payload) != 5:
                        break
                    height, width = struct.unpack(">HH", payload[1:5])
                    return int(width), int(height)
                fh.seek(max(0, segment_size - 2), os.SEEK_CUR)

    raise ValueError(f"Unsupported or unreadable raster image: {file_path}")


def _svg_href_mime_type(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def _render_embedded_raster_svg(input_path: str | Path) -> str:
    width, height = _sniff_raster_size(input_path)
    raw = Path(input_path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    mime = _svg_href_mime_type(input_path)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" href="data:{mime};base64,{encoded}"/>\n'
        "</svg>\n"
    )


def _quality_config_path(reports_out_dir: str) -> str:
    return os.path.join(reports_out_dir, "quality_tercile_config.json")


def _load_quality_config(reports_out_dir: str) -> dict[str, object]:
    path = _quality_config_path(reports_out_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_quality_config(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
) -> None:
    path = _quality_config_path(reports_out_dir)
    normalized_error_pp = float(allowed_error_per_pixel) if math.isfinite(allowed_error_per_pixel) else 0.0
    payload = {
        "allowed_error_per_pixel": float(max(0.0, normalized_error_pp)),
        "skip_variants": sorted(set(skipped_variants)),
        "notes": (
            "Varianten in skip_variants werden in Folge-Pässen nicht erneut konvertiert. "
            "Loeschen der Datei setzt den Ablauf zurueck, dann werden wieder alle Bitmaps bearbeitet."
        ),
        "source": source,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


