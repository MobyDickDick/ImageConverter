""" Start move to File mainFiles/_run_svg_render_subprocess_entrypointFiles/_render_svg_to_numpy_inprocess.py
import src
"""
def _render_svg_to_numpy_inprocess(svg_string: str, size_w: int, size_h: int):
    if fitz is None or np is None or cv2 is None:
        return None

    svg_string = str(svg_string or "")
    if re.search(r"(?<![A-Za-z])(nan|inf)(?![A-Za-z])", svg_string, flags=re.IGNORECASE):
        return None

    attempts = [svg_string]
    normalized_svg = re.sub(r">\s+<", "><", svg_string.strip())
    if normalized_svg and normalized_svg != svg_string:
        attempts.append(normalized_svg)

    for candidate_svg in attempts:
        page = None
        pix = None
        try:
            with fitz.open("pdf", candidate_svg.encode("utf-8")) as doc:
                page = doc.load_page(0)
                zoom_x = size_w / page.rect.width if page.rect.width > 0 else 1
                zoom_y = size_h / page.rect.height if page.rect.height > 0 else 1
                mat = fitz.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat, alpha=True)
            rgba = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 4).astype(np.float32)
            rgb = rgba[:, :, :3]
            alpha = (rgba[:, :, 3:4] / 255.0)
            # PyMuPDF's RGBA pixmap uses premultiplied RGB for alpha=True.
            # Composite onto white directly from premultiplied RGB.
            composited = rgb + (255.0 * (1.0 - alpha))
            composited = np.clip(composited, 0.0, 255.0)
            img = composited.astype(np.uint8)
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception:
            continue
        finally:
            # Free native MuPDF resources eagerly to avoid accumulation over
            # large AC08 range batches.
            if pix is not None:
                del pix
            if page is not None:
                del page
            gc.collect()
    return None
""" End move to File mainFiles/_run_svg_render_subprocess_entrypointFiles/_render_svg_to_numpy_inprocess.py """


def _render_svg_to_numpy_via_subprocess(svg_string: str, size_w: int, size_h: int):
    if np is None:
        return None
    payload = json.dumps(
        {"svg": str(svg_string or ""), "w": int(size_w), "h": int(size_h)},
        ensure_ascii=False,
    ).encode("utf-8")
    cmd = [sys.executable, "-m", "src.image_composite_converter", "--_render-svg-subprocess"]
    try:
        completed = subprocess.run(
            cmd,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=SVG_RENDER_SUBPROCESS_TIMEOUT_SEC,
        )
    except Exception:
        return None
    if completed.returncode != 0 or not completed.stdout:
        return None
    try:
        response = json.loads(completed.stdout.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(response, dict) or not response.get("ok", False):
        return None
    try:
        w = int(response["w"])
        h = int(response["h"])
        raw = base64.b64decode(str(response["data"]).encode("ascii"))
        return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3).copy()
    except Exception:
        return None


""" Start move to File mainFiles/_run_svg_render_subprocess_entrypoint.py
import src
"""
