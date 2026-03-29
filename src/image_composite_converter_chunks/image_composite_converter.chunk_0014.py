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


def _run_svg_render_subprocess_entrypoint() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return 2
    svg = str(payload.get("svg", ""))
    w = int(payload.get("w", 0))
    h = int(payload.get("h", 0))
    if w <= 0 or h <= 0:
        return 2
    rendered = _render_svg_to_numpy_inprocess(svg, w, h)
    if rendered is None:
        sys.stdout.write('{"ok": false}\n')
        return 0
    response = {
        "ok": True,
        "w": int(rendered.shape[1]),
        "h": int(rendered.shape[0]),
        "data": base64.b64encode(rendered.tobytes()).decode("ascii"),
    }
    sys.stdout.write(json.dumps(response, separators=(",", ":")))
    return 0


class Action:
    STOCHASTIC_SEED_OFFSET = 0
    STOCHASTIC_RUN_SEED = 0
    # DejaVuSans-Bold glyph outline in font units.
    M_PATH_D = "M188 1493H678L1018 694L1360 1493H1849V0H1485V1092L1141 287H897L553 1092V0H188Z"
    M_XMIN = 188
    M_XMAX = 1849
    M_YMIN = 0
    M_YMAX = 1493
    T_PATH_D = "M829 0V1194H381V1493H1636V1194H1188V0H829Z"
    T_XMIN = 381
    T_XMAX = 1636
    T_YMIN = 0
    T_YMAX = 1493

    # AR0100 tuned defaults for 25x25.
    AR0100_BASE = {
