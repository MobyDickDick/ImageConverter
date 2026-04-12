"""Filename/base-name normalization helpers for imageCompositeConverter."""

from __future__ import annotations

import os
import re


def getBaseNameFromFileImpl(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r"(-\d+)$", "", name)
    while True:
        prev = name
        name = re.sub(r"_sia$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"_([1-9]|L|M|S|[1-9]S|W|X)$", "", name, flags=re.IGNORECASE)
        if name == prev:
            break
    return name
