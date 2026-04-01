"""Compatibility test module for the parameter-filling tool.

Some workflows reference this file name directly. Keep it as a thin alias to the
canonical test module so both entry points execute the same assertion logic.
"""

from __future__ import annotations

from tests.detailtests.test_fill_missing_parameters_tool import (
    test_fill_missing_parameters_updates_signature_and_calls,
)

__all__ = ["test_fill_missing_parameters_updates_signature_and_calls"]
