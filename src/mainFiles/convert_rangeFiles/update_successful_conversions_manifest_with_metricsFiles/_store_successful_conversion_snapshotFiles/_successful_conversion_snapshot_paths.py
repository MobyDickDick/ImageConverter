from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _successful_conversion_snapshot_paths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    base_dir = _successful_conversion_snapshot_dir(reports_out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {
        'svg': base_dir / f'{variant}.svg',
        'log': base_dir / f'{variant}_element_validation.log',
        'metrics': base_dir / f'{variant}.json',
    }
