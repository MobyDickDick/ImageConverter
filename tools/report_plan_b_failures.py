"""Turn retained Plan-B reports into readable evidence and deduplicated tasks.

Only JSON is read from run artifacts. Publishing uses the trusted default-branch
copy of this module, never code or commands supplied by a pull request artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'Expected a JSON object: {path.name}')
    return data


def source_path(value: str) -> str:
    value = value.replace('\\', '/')
    marker = 'artifacts/'
    return marker + value.split(marker, 1)[1] if marker in value else value.rsplit('/', 1)[-1]


def collect_tasks(root: Path, *, conclusion: str = 'unknown', run_url: str = '') -> list[dict]:
    """Keep failures of earlier originals even when the final battery passes."""
    tasks = []
    try:
        overall = read_json(root/'report.json')
        reports = []
        if overall.get('schema_version') == 'plan_b_search_v1':
            for attempt in overall.get('attempts', []):
                path = (root/attempt['report']).resolve()
                if not path.is_relative_to(root.resolve()):
                    raise ValueError('Attempt report escapes the artifact directory')
                try:
                    reports.append((attempt['report'], read_json(path)))
                except (OSError, ValueError) as exc:
                    reports.append((attempt['report'], dict(status='report_unavailable', error=str(exc),
                        selection={'source_svg': attempt.get('source_svg', 'unknown')}, seed=attempt.get('seed'))))
        else:
            reports = [('report.json', overall)]
        for report_path, report in reports:
            failures = [case for case in report.get('cases', []) if case.get('satisfactory') is False]
            incomplete = report.get('status') in {
                'interrupted', 'preparation_error', 'report_unavailable', 'checking_original', 'running_variations'}
            if not failures and not incomplete:
                continue
            source = source_path(report.get('selection', {}).get('source_svg', 'unknown'))
            phase = 'original' if report.get('original_satisfactory') is False else 'variations'
            if incomplete:
                phase = 'execution'
            identity = [source, report.get('source_svg_sha256'), report.get('source_description_sha256'), phase]
            key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]
            tasks.append(dict(key=key, title=f'Plan B: {Path(source).name} – {phase}'[:200],
                source_svg=source, phase=phase, seed=report.get('seed'), status=report.get('status'),
                source_svg_sha256=report.get('source_svg_sha256'),
                source_description_sha256=report.get('source_description_sha256'),
                source_description=report.get('source_description', ''),
                source_image=report.get('source_image'), source_image_sha256=report.get('source_image_sha256'),
                original_satisfactory=report.get('original_satisfactory'), variations_started=report.get('variations_started'),
                iterations=report.get('iterations'), timeout_seconds=report.get('timeout_seconds'),
                limits=report.get('limits', {}), summary=report.get('summary', {}),
                failures=failures, error=report.get('error'), report=report_path, run_url=run_url))
        if overall.get('status') in {'preparation_error', 'interrupted'} and not tasks:
            raise ValueError(overall.get('error') or overall['status'])
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        tasks.append(dict(key='runner-evidence-unavailable', title='Plan B: Lauf oder Fehlerbeleg fehlt',
            phase='execution', status='report_unavailable', error=str(exc), failures=[],
            report='report.json', run_url=run_url))
    if not tasks and (conclusion not in {'success','unknown'} or not overall.get('summary', {}).get('satisfactory')):
        tasks.append(dict(key='runner-incomplete', title='Plan B: Abnahme unvollständig', phase='execution',
            status=overall.get('status'), failures=[], report='report.json', run_url=run_url))
    # Duplicate entries within a run become one task, without discarding cases.
    grouped = {}
    for task in tasks:
        if task['key'] in grouped:
            grouped[task['key']]['failures'].extend(task['failures'])
        else:
            grouped[task['key']] = task
    return list(grouped.values())


def task_markdown(task: dict) -> str:
    evidence = {k: v for k, v in task.items() if k not in {'key', 'title'}}
    # Full tails stay in the downloadable JSON. Keep GitHub's issue body below
    # its size limit even when all 17 subprocesses fail with tracebacks.
    evidence['failures'] = [{k: (v[-1000:] if k == 'converter_log_tail' else v)
        for k,v in case.items() if k not in {'command','description','reference_svg','output_svg','limits'}}
        for case in task.get('failures', [])]
    # JSON preserves full measured values, limits, descriptions and hashes.
    block = json.dumps(evidence, ensure_ascii=False, indent=2)
    fence = '`' * max(3, max((len(m.group())+1 for m in re.finditer(r'`+', block)), default=3))
    def cell(value):
        return str(value).replace('|','\\|').replace('\n',' ').replace('`','').replace('@','&#64;')
    def metric(case, key):
        value = case.get('metrics', {}).get(key)
        return f'{value:.6f}' if isinstance(value, (int,float)) else '–'
    table = ['| Fall | Fehlergründe | RGB-MSE | Vordergrund-MSE | Kontur | IoU |',
             '|---|---|---:|---:|---:|---:|']
    for case in task.get('failures', []):
        values = [case.get('case_id','?'), ', '.join(case.get('failures', [])),
                  *(metric(case,key) for key in ('normalized_mse','foreground_mse','edge_alignment','foreground_iou'))]
        table.append('| '+' | '.join(cell(v) for v in values)+' |')
    summary = task.get('summary', {})
    return '\n'.join([
        f"### {task['title']}", '',
        f"Lauf: {task.get('run_url') or 'lokal'}; Bericht: `{task['report']}`.", '',
        f"Status: {task.get('status')}; bestanden: {summary.get('passed','?')}/{summary.get('required','?')}.", '',
        *table, '',
        'Fehler: '+cell(task['error']) if task.get('error') else '',
        '- [ ] Ursache mit dem dokumentierten SVG- und Beschreibungshash sowie Seed reproduzieren.',
        '- [ ] Beschreibung oder allgemeinen Rasteralgorithmus korrigieren; Qualitätsgrenzen beibehalten.',
        '- [ ] Original und alle 16 Varianten über die echte CLI abnehmen; Holdouts und Regressionen prüfen.',
        '', 'Wiederholung: Beschreibung aus dem Einzelbericht als UTF-8-Datei speichern und',
        '`python -m tools.run_plan_b_variations --svg QUELLE --description-file BESCHREIBUNG --seed SEED`',
        'mit den protokollierten `--iterations` und `--timeout-seconds` ausführen.', '',
        '<details><summary>Messwerte, Grenzen und Wiederholungsbeleg</summary>', '',
        f'{fence}json', block, fence, '', '</details>', '',
    ])


def write_evidence(root: Path, tasks: list[dict]) -> str:
    root.mkdir(parents=True, exist_ok=True)
    (root/'failure_tasks.json').write_text(json.dumps(
        {'schema_version': 'plan_b_failure_tasks_v1', 'tasks': tasks}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    markdown = '# Plan-B-Fehler und Folgeaufgaben\n\n' + (
        '\n'.join(task_markdown(task) for task in tasks) if tasks else 'Keine dokumentierten Fehlschläge.\n')
    (root/'failure_summary.md').write_text(markdown, encoding='utf-8')
    return markdown


class GitHub:
    def __init__(self, repository: str, token: str):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Invalid repository')
        self.base = f'https://api.github.com/repos/{repository}'
        self.token = token

    def request(self, method: str, path: str, data=None):
        request = urllib.request.Request(self.base+path, method=method,
            data=None if data is None else json.dumps(data).encode(), headers={
                'Authorization': 'Bearer '+self.token, 'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def issues(self):
        page = 1
        while True:
            batch = self.request('GET', f'/issues?state=all&per_page=100&page={page}')
            yield from (issue for issue in batch if 'pull_request' not in issue)
            if len(batch) < 100:
                break
            page += 1


def sync_issues(tasks: list[dict], client, run_id: str) -> list[dict]:
    """One issue per source/hash/phase; repeat runs update evidence, never spam comments."""
    existing = list(client.issues()) if tasks else []
    results = []
    for task in tasks:
        marker = f"<!-- plan-b-task:{task['key']} -->"
        occurrence = f'<!-- plan-b-run:{run_id} -->'
        issue = next((i for i in existing if (i.get('body') or '').split('\n',1)[0] == marker), None)
        start, end = '<!-- plan-b-evidence:start -->', '<!-- plan-b-evidence:end -->'
        latest = start+'\n'+occurrence+'\n'+task_markdown(task)+end
        if issue and occurrence in (issue.get('body') or ''):
            results.append(dict(key=task['key'], url=issue['html_url'], action='already_recorded'))
            continue
        if issue:
            body = issue.get('body') or ''
            # Preserve notes and checkboxes maintained outside the evidence block.
            if start in body and end in body:
                body = body.split(start, 1)[0]+latest+body.split(end, 1)[1]
            else:
                body += '\n\n'+latest
            result = client.request('PATCH', f"/issues/{issue['number']}", dict(body=body, state='open'))
            action = 'updated'
        else:
            result = client.request('POST', '/issues', dict(title=task['title'], body=marker+'\n'+latest))
            existing.append(result)
            action = 'created'
        results.append(dict(key=task['key'], url=result['html_url'], action=action))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--run-url', default='')
    parser.add_argument('--run-id', default='local')
    parser.add_argument('--conclusion', default='unknown')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args(argv)
    tasks = collect_tasks(args.artifact_dir, conclusion=args.conclusion, run_url=args.run_url)
    markdown = write_evidence(args.artifact_dir, tasks)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with Path(summary).open('a', encoding='utf-8') as stream:
            stream.write(markdown)
    if args.publish:
        try:
            client = GitHub(os.environ['GITHUB_REPOSITORY'], os.environ['GH_TOKEN'])
            if any(t['phase'] == 'execution' for t in tasks) and re.fullmatch(r'\d+(?:-\d+)?',args.run_id):
                # Even dependency/setup failures without a converter report
                # have a named failed step, rather than only a red run link.
                try:
                    jobs = client.request('GET', f"/actions/runs/{args.run_id.split('-')[0]}/jobs?per_page=100")['jobs']
                    failed = [dict(job=job['name'], url=job['html_url'], conclusion=job['conclusion'],
                        steps=[s['name'] for s in job.get('steps', []) if s.get('conclusion') not in {'success','skipped',None}])
                        for job in jobs if job.get('conclusion') not in {'success','skipped',None}]
                    for task in tasks:
                        if task['phase'] == 'execution':
                            task['failed_jobs'] = failed
                except Exception as exc:
                    for task in tasks:
                        if task['phase'] == 'execution':
                            task['job_diagnostics_error'] = str(exc)
                # Save the extra infrastructure diagnostics in the drafts too.
                write_evidence(args.artifact_dir, tasks)
            result = sync_issues(tasks, client, args.run_id)
        except Exception as exc:
            # Keep reviewable issue drafts even if Actions cannot create issues.
            result = {'error': str(exc), 'drafts': 'failure_tasks.json'}
            print('GitHub-Issues konnten nicht synchronisiert werden; lokale Aufgaben bleiben erhalten.')
            (args.artifact_dir/'issue_sync.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
            if summary:
                with Path(summary).open('a', encoding='utf-8') as stream:
                    stream.write('\nIssue-Synchronisierung fehlgeschlagen; Details in `issue_sync.json`, Aufgaben in `failure_tasks.json`.\n')
            return 1
        (args.artifact_dir/'issue_sync.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        if summary:
            with Path(summary).open('a', encoding='utf-8') as stream:
                stream.write('\n'+'\n'.join(f"- [{r['action']}]({r['url']})" for r in result)+'\n')
    print(f'{len(tasks)} Plan-B-Folgeaufgaben dokumentiert')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
