"""Diversity evidence must catch duplicate and visually unchanged failures."""
import json

import numpy as np
from PIL import Image
import pytest

from src.imageConverterDiversity import compare_results, foreground_similarity, geometry_hash
from tools.audit_failed_conversion_diversity import audit

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24">'
       '<circle cx="16" cy="12" r="7" fill="#225599"/></svg>')


def test_metadata_or_different_svg_bytes_cannot_prove_visual_diversity():
    changed = SVG.replace('<circle', '<desc>seed 123</desc><circle data-seed="123"')
    report = compare_results(SVG, changed)
    assert report['geometry_identical'] and report['raster_identical']
    assert report['foreground_similarity'] == 1
    assert geometry_hash(SVG) == geometry_hash(changed)


def test_foreground_measurement_does_not_hide_differences_in_white_background():
    a = np.full((96,96,3), 255, np.uint8)
    b = a.copy()
    a[20:22,20:22] = 0
    b[70:72,70:72] = 0
    assert foreground_similarity(a,b) == 0
    assert (a == b).mean() > .99


def test_real_geometry_changes_are_observable():
    report = compare_results(SVG, SVG.replace('cx="16"', 'cx="7"'))
    assert not report['geometry_identical'] and not report['raster_identical']
    assert report['foreground_similarity'] < .99


def test_audit_reports_repeated_results_and_missing_evidence(tmp_path):
    artifacts = tmp_path/'artifacts'
    for name, seed in [('one', 17), ('two', 18), ('missing', 19)]:
        folder = artifacts/'gui'/name
        folder.mkdir(parents=True)
        Image.new('RGB', (32,24), 'white').save(folder/'source.png')
        (folder/'job.json').write_text(json.dumps(dict(name='neutral.png', search_seed=seed,
            description='Ein Kreis.', quality='warning', status='done')))
        if name != 'missing':
            (folder/'result.svg').write_text(SVG)
    report = audit(artifacts, tmp_path/'audit')
    assert report['records'] == 2 and report['missing_result_jobs'] == 1
    assert report['repeat_pairs'] == 1 and report['identical_different_seed_pairs'] == 1
    assert report['universal_distinctness_disproved']
    assert not report['universal_diversity_proven']
    assert (tmp_path/'audit/comparison.png').is_file()
