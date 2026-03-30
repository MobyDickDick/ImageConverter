from src import image_composite_converter as _icc

globals().update(vars(_icc))

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
