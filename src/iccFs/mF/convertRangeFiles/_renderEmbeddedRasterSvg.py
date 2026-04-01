def renderEmbeddedRasterSvg(input_path: str | Path) -> str:
    width, height = sniffRasterSize(input_path)
    raw = Path(input_path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    mime = svgHrefMimeType(input_path)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" href="data:{mime};base64,{encoded}"/>\n'
        "</svg>\n"
    )
