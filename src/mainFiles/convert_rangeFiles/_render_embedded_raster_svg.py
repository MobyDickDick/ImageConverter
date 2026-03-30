from src import image_composite_converter as _icc

globals().update(vars(_icc))

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
