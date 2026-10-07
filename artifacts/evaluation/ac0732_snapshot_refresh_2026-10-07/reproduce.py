"""Run from the repository root; outputs stay in .tmp, outside committed fixtures."""
from pathlib import Path
import os
import random
import shutil

import numpy as np

from src.iCCModules import imageCompositeConverterCli as cli
from tools.review_conversion_quality import review_variant

root = Path('.tmp/ac0732-s-reproduction')
(root / 'inputs').mkdir(parents=True, exist_ok=True)
shutil.copyfile('artifacts/images_to_convert/AC0732_1_S.jpg', root / 'inputs/AC0732_1_S.jpg')
os.environ['TINY_ICC_OUTPUT_VARIATION'] = '0'
random.seed(0)
np.random.seed(0)
exit_code = cli.main([
    str(root / 'inputs'), '--descriptions-path', 'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',
    '--output-dir', str(root / 'after'), '--execution-mode', 'semantic-only',
    '--start', 'AC0732_1_S', '--end', 'AC0732_1_S', '--deterministic-order',
])
assert exit_code == 0
fresh = root / 'after/converted_svgs/AC0732_1_S.svg'
snapshot = Path('artifacts/converted_images/reports/conversion_bestlist_snapshots/AC0732_1_S.svg')
assert fresh.read_bytes() == snapshot.read_bytes()
record = review_variant('AC0732_1_S', source='reproduction', svg_dirs=(fresh.parent,))
assert record.mean_delta2 <= 3659.34130859375
print(f'Reproduced SVG and independent quality bound: {record.mean_delta2}')
