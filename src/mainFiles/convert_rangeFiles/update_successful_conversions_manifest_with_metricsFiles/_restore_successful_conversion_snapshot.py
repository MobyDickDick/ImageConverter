from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _restore_successful_conversion_snapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> bool:
    """Restore the previous best conversion for ``variant`` if a snapshot exists."""
    snapshot_paths = _successful_conversion_snapshot_paths(reports_out_dir, variant)
    restored = False

    target_svg = Path(svg_out_dir) / f'{variant}.svg'
    if snapshot_paths['svg'].exists():
        target_svg.parent.mkdir(parents=True, exist_ok=True)
        target_svg.write_text(snapshot_paths['svg'].read_text(encoding='utf-8'), encoding='utf-8')
        restored = True

    target_log = Path(reports_out_dir) / f'{variant}_element_validation.log'
    if snapshot_paths['log'].exists():
        target_log.write_text(snapshot_paths['log'].read_text(encoding='utf-8'), encoding='utf-8')
        restored = True

    return restored
