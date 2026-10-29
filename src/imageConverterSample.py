"""Refine an explicitly uploaded SVG against its source raster, in a bounded worker."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
MAX_SAMPLE_BYTES = 2 * 1024 * 1024
NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")
TAGS = {"svg", "g", "defs", "circle", "ellipse", "rect", "path", "line", "polyline", "polygon",
        "text", "tspan", "linearGradient", "radialGradient", "stop", "clipPath", "mask", "pattern",
        "title", "desc", "metadata", "style"}
SCALARS = {"x", "y", "cx", "cy", "x1", "y1", "x2", "y2", "r", "rx", "ry", "width", "height",
           "stroke-width", "font-size", "opacity", "fill-opacity", "stroke-opacity", "stop-opacity"}
POSITIVE = {"r", "rx", "ry", "width", "height", "stroke-width", "font-size"}
EDITOR_NAMESPACES = {"http://www.inkscape.org/namespaces/inkscape",
                     "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"}


def prepare_sample(data: bytes, width: int, height: int) -> str:
    """Accept standalone vector SVGs, never active content or external resources."""
    if not data or len(data) > MAX_SAMPLE_BYTES:
        raise ValueError("Die Sample-Datei darf maximal 2 MB gross sein.")
    text = data.decode("utf-8-sig")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)|<\?xml-stylesheet", text, re.I):
        raise ValueError("Bitte ein eigenständiges SVG ohne externe Ressourcen hochladen.")
    root = ET.fromstring(text)
    if root.tag not in {"svg", f"{{{SVG_NS}}}svg"}:
        raise ValueError("Die Sample-Datei muss ein SVG sein.")
    elements = list(root.iter())
    if len(elements) > 1500:
        raise ValueError("Das Sample enthält zu viele Elemente (maximal 1500).")
    stack = [(root, 0)]
    while stack:
        element, depth = stack.pop()
        if depth > 64:
            raise ValueError("Das Sample enthält zu tief verschachtelte Gruppen.")
        stack.extend((child, depth + 1) for child in element)
    # Editor views, guides and RDF metadata are not rendered SVG geometry.
    # Discard them, while retaining the strict validation of all visual nodes.
    for parent in list(root.iter()):
        for child in list(parent):
            namespace = child.tag[1:].split('}', 1)[0] if child.tag.startswith('{') else ''
            if namespace in EDITOR_NAMESPACES or child.tag.rsplit('}', 1)[-1] == 'metadata':
                parent.remove(child)
    elements = list(root.iter())
    for element in elements:
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in TAGS or (element.tag.startswith("{") and not element.tag.startswith("{" + SVG_NS + "}")):
            raise ValueError(f"Das Sample enthält ein nicht unterstütztes Element: {tag}.")
        for key, value in element.attrib.items():
            attribute = key.rsplit("}", 1)[-1].lower()
            if attribute.startswith("on") or attribute in {"href", "src"}:
                raise ValueError("Das Sample muss ausschliesslich eigenständige SVG-Formen enthalten.")
            if len(value) > 250000:
                raise ValueError("Das Sample enthält einen zu komplexen Pfad.")
        content = " ".join(element.attrib.values()) + " " + (element.text or "")
        if re.search(r"@import|javascript\s*:|expression\s*\(", content, re.I):
            raise ValueError("Aktive Inhalte sind in einer Sample-Datei nicht erlaubt.")
        for resource in re.findall(r"url\s*\((.*?)\)", content, re.I):
            if not resource.strip(" \t\r\n\"'").startswith("#"):
                raise ValueError("Das Sample darf keine externen Ressourcen laden.")
        for key in list(element.attrib):
            if key.startswith('{') and key[1:].split('}', 1)[0] in EDITOR_NAMESPACES:
                del element.attrib[key]
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    root = ET.fromstring(inline_simple_svg_styles(ET.tostring(root, encoding="unicode")))
    if not root.get("viewBox"):
        original_w = NUMBER.match(root.get("width", ""))
        original_h = NUMBER.match(root.get("height", ""))
        w = float(original_w[0]) if original_w else width
        h = float(original_h[0]) if original_h else height
        root.set("viewBox", f"0 0 {w:g} {h:g}")
    values = NUMBER.findall(root.get("viewBox", ""))
    if len(values) != 4 or not all(math.isfinite(float(v)) for v in values) or min(map(float, values[2:])) <= 0:
        raise ValueError("Das Sample hat keine gültige SVG-Zeichenfläche.")
    root.set("width", str(width))
    root.set("height", str(height))
    ET.register_namespace("", SVG_NS)
    return ET.tostring(root, encoding="unicode")


def parameters(root):
    """Editable paint/geometry values; paths with arc flags remain intact."""
    from PIL import ImageColor
    result = []
    for node in root.iter():
        if node is root:
            continue
        for attribute, value in list(node.attrib.items()):
            if attribute in SCALARS and re.fullmatch(NUMBER.pattern + r"(?:px|%)?", value.strip()):
                result.append((node, attribute, "scalar", 0))
            elif attribute == "points" or (attribute == "d" and not re.search("[Aa]", value)):
                for index, number in enumerate(NUMBER.findall(value)):
                    if math.isfinite(float(number)):
                        result.append((node, attribute, "list", index))
            elif attribute in {"fill", "stroke", "stop-color"}:
                try:
                    rgb = ImageColor.getrgb(value)
                    if len(rgb) == 3:
                        node.set(attribute, "#%02x%02x%02x" % rgb)
                        result.extend((node, attribute, "color", channel) for channel in range(3))
                except ValueError:
                    pass
        if len(result) > 3000:
            raise ValueError("Das Sample enthält zu viele veränderbare Parameter (maximal 3000).")
    return result


def adjusted(value, kind, index, delta, attribute):
    if kind == "color":
        rgb = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
        rgb[index] = max(0, min(255, round(rgb[index] + delta)))
        return "#%02x%02x%02x" % tuple(rgb)
    matches = list(NUMBER.finditer(value))
    match = matches[index]
    number = float(match[0]) + delta
    if attribute in POSITIVE:
        number = max(0.01, number)
    elif attribute.endswith("opacity"):
        number = max(0, min(1, number))
    if not math.isfinite(number):
        return value
    return value[:match.start()] + f"{number:.5f}".rstrip("0").rstrip(".") + value[match.end():]


def render_svg(svg, width, height):
    import fitz
    import numpy as np
    import cv2
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
    # Use the same private gradient adapters as the converter: this PyMuPDF
    # build otherwise paints native SVG gradients black during GUI validation.
    image = render_svg_to_numpy_inprocess(svg, width, height,
        fitz_module=fitz, np_module=np, cv2_module=cv2)
    if image is None:
        raise ValueError("Das SVG konnte nicht gerendert werden.")
    if image.shape[:2] != (height, width):
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    # The converter works in BGR; uploaded samples and Pillow sources use RGB.
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def refine(source: Path, sample: Path, output: Path, description: str, seconds: float) -> dict:
    import numpy as np
    from PIL import Image
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions

    with Image.open(source) as image:
        target = np.asarray(image.convert("RGB"))
    height, width = target.shape[:2]
    root = ET.fromstring(prepare_sample(sample.read_bytes(), width, height))
    params = parameters(root)
    svg = lambda: ET.tostring(root, encoding="unicode")
    reference = target.astype(np.float32)
    border = np.concatenate((reference[0], reference[-1], reference[:, 0], reference[:, -1]))
    foreground = np.max(abs(reference - np.median(border, axis=0)), axis=2) > 25
    weights = 1 + 4 * foreground.astype(np.float32)
    evaluations = 0

    def measure():
        nonlocal evaluations
        pixels = render_svg(svg(), width, height)
        squared = np.square(reference - pixels.astype(np.float32)).mean(axis=2) / 255 ** 2
        evaluations += 1
        return float((squared * weights).mean()), float(squared.mean()), pixels

    best, best_mse, rendered = measure()
    initial_mse = best_mse
    initial_quality = pixel_quality(target, rendered)
    started = time.monotonic()
    # Preserve an already accepted assembly instead of trading its square,
    # alignment and shared paint for tiny improvements in a few raster pixels.
    accepted_input = bool(initial_quality and initial_quality['passed'])
    deadline = started if accepted_input else started + seconds
    accepted = 0
    print(f"Sample geladen: {len(params)} Parameter, mittlerer Pixelfehler={best_mse:.8f}", flush=True)
    # Coarse-to-fine coordinate descent retains the uploaded primitive structure.
    span = max(float(v) for v in NUMBER.findall(root.get("viewBox"))[2:])
    for fraction, paint_step in [(0.06, 32), (0.025, 16), (0.01, 8), (0.004, 4), (0.0015, 2), (0.0006, 1)]:
        for sweep in range(4):
            changed = False
            for node, attribute, kind, index in params:
                if time.monotonic() >= deadline:
                    break
                step = paint_step if kind == "color" else (fraction if attribute.endswith("opacity") else span * fraction)
                previous = node.get(attribute)
                for direction in (-1, 1):
                    node.set(attribute, adjusted(previous, kind, index, direction * step, attribute))
                    try:
                        loss, mse, pixels = measure()
                    except Exception:
                        node.set(attribute, previous)
                        continue
                    # Each accepted step improves the weighted loss and cannot worsen MSE.
                    if loss < best - 1e-10 and mse <= best_mse + 1e-12:
                        best, best_mse, rendered = loss, mse, pixels
                        previous = node.get(attribute)
                        changed = True
                        accepted += 1
                    else:
                        node.set(attribute, previous)
                    if time.monotonic() >= deadline:
                        break
            print(f"Sample-Suche: Prüfungen={evaluations}, Verbesserungen={accepted}, Pixelfehler={best_mse:.8f}", flush=True)
            if not changed or time.monotonic() >= deadline:
                break
        if time.monotonic() >= deadline:
            break
    final_svg = svg()
    quality = pixel_quality(target, rendered)
    description_error = ""
    try:
        validate_svg_assertions(final_svg, description_assertions(description))
    except ValueError as exc:
        description_error = str(exc)
    report = dict(initial_mse=initial_mse, final_mse=best_mse,
                  initial_quality=initial_quality, final_quality=quality,
                  improved=best_mse < initial_mse - 1e-10, evaluations=evaluations,
                  accepted=accepted, description_error=description_error,
                  stop_reason='quality_target_reached' if accepted_input else 'search_complete',
                  passed=bool(quality and quality["passed"] and not description_error),
                  elapsed=round(time.monotonic() - started, 2))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final_svg, encoding="utf-8")
    output.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


def main():
    from src.iCCModules.imageCompositeConverterDependencies import activate_vendored_site_packages
    activate_vendored_site_packages()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--description", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 240:
        parser.error("--seconds muss zwischen 0 und 240 liegen")
    refine(args.source, args.sample, args.output, args.description.read_text(encoding="utf-8"), args.seconds)


if __name__ == "__main__":
    main()
