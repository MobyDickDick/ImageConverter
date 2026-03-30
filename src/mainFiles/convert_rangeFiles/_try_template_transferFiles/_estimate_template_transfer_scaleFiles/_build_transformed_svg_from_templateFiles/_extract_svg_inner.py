from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _extract_svg_inner(svg_text: str) -> str:
    match = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return svg_text
