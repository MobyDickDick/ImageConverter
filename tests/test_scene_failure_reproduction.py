"""Small Actions-only quality probes. Known negative conversions stay red."""
import os

import pytest

from tools.run_seeded_scene_check import run


pytestmark = pytest.mark.skipif(os.environ.get('ICC_R1_REPRODUCTION') != '1',
                                reason='Opt-in targeted Actions conversion probes')


@pytest.mark.parametrize('case_id', ['gradient_00', 'gradient_03', 'gradient_04'])
def test_frozen_gradient_quality(case_id):
    run('evaluate_gradient_scene', 628191, ('--count', '6', '--paraphrase'),
        case_ids=[case_id])


def test_frozen_same_paint_quality():
    run('evaluate_overlap_composition', 915463, ('--rounded', '--outlines', '--same-fill'),
        case_ids=['same_paint_outlined_rounded_overlap_07'])
