import json

from tools.inventory_plan_b_issues import inventory


def issue(number, seed, phase='variations', failures=None):
    evidence = dict(source_svg='artifacts/samples/foreign.svg', source_description_sha256='description',
                    seed=seed, phase=phase, failures=[{'failures':failures or []}])
    return {'issue_number':number, 'body':'```json\n'+json.dumps(evidence)+'\n```'}


def test_seeds_keep_integer_precision_and_execution_errors_stay_separate():
    result = inventory([issue(1,6329305985306020792), issue(2,4263954452271046129),
                        issue(3,5,'original',['converter_error'])])
    assert result['issue_count'] == 3
    assert result['investigation_group_count'] == 2
    assert result['phase_counts'] == {'variations':2, 'execution':1}
    group = next(group for group in result['groups'] if group['phase']=='variations')
    assert [row['seed'] for row in group['issues']] == [6329305985306020792,4263954452271046129]
