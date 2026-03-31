def _runSvgRenderSubprocessEntrypoint() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return 2
    svg = str(payload.get("svg", ""))
    w = int(payload.get("w", 0))
    h = int(payload.get("h", 0))
    if w <= 0 or h <= 0:
        return 2
    rendered = _renderSvgToNumpyInprocess(svg, w, h)
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
