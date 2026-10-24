"""Remove disposable project test data after preserving seed metadata.

Only declared test workspaces and regenerated synthetic evidence are eligible;
source images, regression fixtures, accepted SVGs and dependencies are retained.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = ('overlap_outlines_v1', 'rounded_overlap_v1', 'overlap_composition_v1',
             'rounded_outlines_v1', 'rounded_composition_v1', 'component_splits_v1')
SKIP = {'.git', '.venv', 'venv', 'vendor', 'node_modules', '__pycache__', 'site-packages'}
METADATA = ('generation.json', 'report.json', 'manifest.json', 'checks.json')


def metadata_files(target):
    if not target.is_dir():
        return []
    # Enumerate the same metadata with Rust's fast directory walker when
    # available; no generated-data directory is omitted from seed harvesting.
    if shutil.which('rg'):
        command = ['rg', '--files', '--hidden', '--no-ignore']
        for name in METADATA:
            command.extend(['-g', name])
        for name in sorted(SKIP):
            command.extend(['-g', f'!**/{name}/**'])
        result = subprocess.run([*command, str(target)], capture_output=True, text=True, check=False)
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr)
        return [Path(line) for line in result.stdout.splitlines()]
    paths = []
    for base, dirs, files in os.walk(target, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP and not (Path(base)/d).is_symlink()]
        paths.extend(Path(base)/name for name in files if name in METADATA)
    return paths


def seed_values(value, prefix=''):
    found = {}
    if isinstance(value, dict):
        for key, child in value.items():
            name = f'{prefix}.{key}' if prefix else key
            if 'seed' in key.casefold():
                found[name] = child
            elif isinstance(child, (dict, list)):
                found.update(seed_values(child, name))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            found.update(seed_values(child, f'{prefix}[{i}]'))
    return found


def targets(root):
    # Independent targets let inaccessible legacy pytest directories remain
    # intact while other verified test runs can still be cleaned safely.
    result = list((root/'.tmp').iterdir()) if (root/'.tmp').exists() else []
    result.extend(root/p for p in ('artifacts/pytest', 'artifacts/plan-b-acceptance',
                              '.pytest_cache', '__pycache__', '.coverage',
                              'imageCompositeConverter.local.log') if (root/p).exists())
    for code in ('src', 'tests', 'tools'):
        if (root/code).exists():
            result.extend((root/code).rglob('__pycache__'))
    evaluation = root/'artifacts/evaluation'
    if evaluation.exists():
        for folder in evaluation.iterdir():
            if folder.is_dir() and (folder.name == 'plan_b_variations'
                                   or folder.name.startswith(('plan_b_random_', 'conversion_search_'))):
                result.append(folder)
            elif folder.name in SYNTHETIC:
                result.extend(p for p in folder.iterdir() if p.is_dir())
                result.extend(p for p in folder.iterdir() if p.is_file()
                              and p.name not in ('README.md', 'checks.json', 'summary.json', '.gitignore'))
    return result


def clean(root=ROOT, *, apply=False, inventory_path=None, from_inventory=None):
    root = root.resolve()
    candidates = targets(root)
    # Resolve every target before any removal. Symlinks/junctions may never
    # redirect cleanup outside the explicitly named project directory.
    resolved_targets = {}
    for path in candidates:
        resolved_targets[path] = path.resolve()
        if not resolved_targets[path].is_relative_to(root) or resolved_targets[path] == root:
            raise ValueError(f'Cleanup target escapes project: {path}')
    seeds = {}
    journal = root/'config/preserved_test_seeds.json'
    if journal.exists():
        seeds.update(json.loads(journal.read_text(encoding='utf-8')))
    eligible, skipped, inventory = [], [], []
    prior = None
    if from_inventory:
        plan = json.loads(Path(from_inventory).read_text(encoding='utf-8'))
        prior = {row['target']: row for row in plan['eligible']}
    git = subprocess.run(['git', '-C', str(root), 'worktree', 'list', '--porcelain'],
                         capture_output=True, text=True, check=False)
    worktrees = [Path(line[9:]).resolve() for line in git.stdout.splitlines() if line.startswith('worktree ')]
    for target in candidates:
        relative = target.relative_to(root).as_posix()
        if ((target/'.git').exists() if target.is_dir() else False) or any(
                path.is_relative_to(resolved_targets[target]) for path in worktrees):
            skipped.append(dict(target=relative, reason='Protected Git checkout'))
            continue
        if prior is not None and relative not in prior:
            skipped.append(dict(target=relative, reason='Not approved by the read-only inventory'))
            continue

        def read_seed(path):
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError(f'Seed file escapes project: {path}')
            raw = path.read_bytes()
            # Legacy PowerShell reports may carry a BOM; some append several
            # complete JSON documents. Read all of them without dropping any
            # seed, while genuinely truncated metadata still blocks removal.
            encoding = ('utf-32' if raw.startswith((b'\xff\xfe\0\0', b'\0\0\xfe\xff'))
                        else 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
            text = raw.decode(encoding)
            values, decoder, position = [], json.JSONDecoder(), 0
            try:
                while position < len(text):
                    if text[position].isspace():
                        position += 1
                        continue
                    value, position = decoder.raw_decode(text, position)
                    values.append(value)
            except json.JSONDecodeError:
                # Deliberately invalid JSON fixtures contain no seed to save.
                # Any seed text or escaped key keeps the whole run protected.
                if 'seed' not in text.casefold() and '\\u' not in text:
                    return path, {}
                raise
            if not values:
                raise ValueError(f'Empty seed metadata: {path}')
            value = values[0] if len(values) == 1 else values
            return path, seed_values(value)

        try:
            paths = metadata_files(target) if prior is None else []
            records = []
            with ThreadPoolExecutor(max_workers=8) as workers:
                for path, values in workers.map(read_seed, paths):
                    if values:
                        records.append((path.relative_to(root).as_posix(), values))
            # Inventory every file, including files that contain no metadata.
            files = []
            # Use the same portable walker for review and application. rg is
            # optional for metadata discovery, never a cleanup prerequisite.
            if target.is_dir():
                def failed(error):
                    raise error
                for base, dirs, names in os.walk(target, followlinks=False, onerror=failed):
                    if not Path(base).resolve().is_relative_to(root):
                        raise ValueError(f'Inventory directory escapes project: {base}')
                    for name in names:
                        file = Path(base)/name
                        files.append(file.relative_to(root).as_posix())
            else:
                files = [target.relative_to(root).as_posix()]
            if prior is not None and set(files) != set(prior[relative]['files']):
                raise ValueError('Files changed since the read-only inventory; preserved for review')
            # Also inspect differently named metadata and replay journals.
            # The common names above are a fast first pass, not an allowlist
            # that could discard a seed held in e.g. trial-settings.json.
            additional = [root/name for name in files
                          if Path(name).suffix in ('.json', '.jsonl') and root/name not in paths]
            with ThreadPoolExecutor(max_workers=8) as workers:
                for path, values in workers.map(read_seed, additional):
                    if values:
                        records.append((path.relative_to(root).as_posix(), values))
            seeds.update(records)
            eligible.append(target)
            inventory.append(dict(target=target.relative_to(root).as_posix(), files=files,
                                  metadata_files=len(paths)+len(additional), seed_records=len(records)))
        except (OSError, ValueError, RuntimeError) as error:
            skipped.append(dict(target=target.relative_to(root).as_posix(), reason=str(error)))
        if (len(eligible)+len(skipped)) % 100 == 0:
            print(f'Inventoried {len(eligible)} targets; preserved {len(skipped)} protected or unreadable targets', flush=True)
    if inventory_path:
        Path(inventory_path).write_text(json.dumps(dict(eligible=inventory, skipped=skipped),
                                                  ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if apply:
        journal.parent.mkdir(parents=True, exist_ok=True)
        pending = journal.with_suffix('.json.tmp')
        with pending.open('w', encoding='utf-8') as stream:
            stream.write(json.dumps(seeds, ensure_ascii=False, indent=2)+'\n')
            stream.flush()
            os.fsync(stream.fileno())
        pending.replace(journal)
        for path in eligible:
            # Recheck immediately before removal, after seed extraction.
            resolved = path.resolve()
            if resolved == root or not resolved.is_relative_to(root):
                raise ValueError(f'Cleanup target escapes project: {path}')
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        temporary = root/'.tmp'
        if temporary.is_dir() and not any(temporary.iterdir()):
            temporary.rmdir()
    print(f"{'Removed' if apply else 'Would remove'} {len(eligible)} test data paths; preserved {len(seeds)} seed records; retained {len(skipped)} protected, changed or unreadable targets", flush=True)
    return dict(paths=len(eligible), seed_records=len(seeds), skipped=skipped)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--from-inventory', type=Path)
    args = parser.parse_args()
    result = clean(apply=args.apply, inventory_path=args.inventory, from_inventory=args.from_inventory)
    return 1 if any(row['reason'] != 'Protected Git checkout' for row in result['skipped']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
