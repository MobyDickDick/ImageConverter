#!/usr/bin/env python3
"""Run a resumable, sharded full-catalog conversion with a timeout per image."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import time
from pathlib import Path

SUPPORTED_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("artifacts/images_to_convert"))
    parser.add_argument(
        "--descriptions-path",
        type=Path,
        default=Path("artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/catalog-conversion"))
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--iterations", type=int, default=64)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def selected_images(input_dir: Path, shard_index: int, shard_count: int) -> list[Path]:
    images = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
    return [path for index, path in enumerate(images) if index % shard_count == shard_index]


def completed_variants(report_path: Path) -> set[str]:
    if not report_path.exists():
        return set()
    with report_path.open(encoding="utf-8", newline="") as handle:
        return {row["variant"] for row in csv.DictReader(handle) if row.get("variant")}


def report_failure(variant: str, status: str, returncode: int) -> None:
    message = f"{variant}: {status} (return code {returncode})"
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::error title=Catalog conversion failed::{message}", flush=True)
    else:
        print(f"[CATALOG] ERROR: {message}", file=sys.stderr, flush=True)


def conversion_environment() -> dict[str, str]:
    env = os.environ.copy()
    py_tag = f"py{sys.version_info.major}{sys.version_info.minor}"
    vendor_site_packages = PROJECT_ROOT / "vendor" / f"linux-{py_tag}" / "site-packages"
    if vendor_site_packages.is_dir():
        existing_pythonpath = env.get("PYTHONPATH")
        pythonpath = [str(vendor_site_packages)]
        if existing_pythonpath:
            pythonpath.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    return env


def main() -> int:
    args = parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("--shard-index must be between 0 and --shard-count - 1")
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be greater than zero")

    shard_dir = args.output_dir / f"shard-{args.shard_index:02d}-of-{args.shard_count:02d}"
    report_path = shard_dir / "catalog_results.csv"
    shard_dir.mkdir(parents=True, exist_ok=True)
    done = completed_variants(report_path) if args.resume else set()
    images = selected_images(args.input_dir, args.shard_index, args.shard_count)
    pending = [path for path in images if path.stem not in done]
    print(
        f"[CATALOG] shard={args.shard_index}/{args.shard_count} "
        f"selected={len(images)} completed={len(done)} pending={len(pending)}",
        flush=True,
    )

    write_header = not report_path.exists() or not args.resume
    mode = "a" if args.resume else "w"
    failure_count = 0
    with report_path.open(mode, encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("variant", "filename", "status", "returncode", "elapsed_seconds"),
        )
        if write_header:
            writer.writeheader()
            handle.flush()

        for position, image_path in enumerate(pending, start=1):
            variant = image_path.stem
            command = [
                sys.executable,
                "-m",
                "src.imageCompositeConverter",
                str(args.input_dir),
                "--descriptions-path",
                str(args.descriptions_path),
                "--output-dir",
                str(shard_dir),
                "--iterations",
                str(args.iterations),
                "--start",
                variant,
                "--end",
                variant,
                "--deterministic-order",
            ]
            env = conversion_environment()
            env["ICC_CONVERSION_TIMEOUT_SEC"] = str(args.timeout_seconds)
            started = time.monotonic()
            status = "completed"
            returncode = 0
            try:
                result = subprocess.run(
                    command,
                    env=env,
                    check=False,
                    timeout=args.timeout_seconds + 15.0,
                )
                returncode = result.returncode
                if returncode != 0:
                    status = "converter_error"
            except subprocess.TimeoutExpired:
                status = "process_timeout"
                returncode = 124
            elapsed = time.monotonic() - started
            writer.writerow(
                {
                    "variant": variant,
                    "filename": image_path.name,
                    "status": status,
                    "returncode": returncode,
                    "elapsed_seconds": f"{elapsed:.3f}",
                }
            )
            handle.flush()
            print(
                f"[CATALOG] {position}/{len(pending)} {variant}: "
                f"{status} rc={returncode} elapsed={elapsed:.1f}s",
                flush=True,
            )
            if status != "completed":
                failure_count += 1
                report_failure(variant, status, returncode)

    print(
        f"[CATALOG] finished={len(pending)} failed={failure_count} "
        f"succeeded={len(pending) - failure_count}",
        flush=True,
    )
    return 1 if failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
