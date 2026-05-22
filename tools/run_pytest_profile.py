#!/usr/bin/env python3
"""Run predefined pytest profiles for stable/local workflows."""
from __future__ import annotations

import argparse
import subprocess
import sys

PROFILES = {
    "core-green": [
        "-m",
        "not blocking_conversion and not optional_fixture",
        "tests/detailtests/test_conversion_execution_helpers.py",
        "tests/detailtests/test_iteration_setup_helpers.py",
        "tests/detailtests/test_quality_config_helpers.py",
    ],
    "extended": [
        "-m",
        "not blocking_conversion",
    ],
    "research": [
        "-m",
        "blocking_conversion or optional_fixture",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=sorted(PROFILES))
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    cmd = [sys.executable, "-m", "pytest", "-q", *PROFILES[args.profile], *args.pytest_args]
    print("+", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
