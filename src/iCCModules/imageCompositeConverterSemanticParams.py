"""Semantic badge-parameter dispatch helpers."""

from __future__ import annotations



def makeBadgeParamsImpl(
    w: int,
    h: int,
    base_name: str,
    img,
    *,
    get_base_name_fn,
    build_ar0100_badge_params_fn,
    make_ac08_badge_params_fn,
):
    """Build badge parameters for supported semantic families.

    The dispatcher keeps AR0100 handling and AC08 handling centralized so the
    monolith can delegate with a thin compatibility wrapper.
    """

    name = str(get_base_name_fn(base_name)).upper()

    ar0100_params = build_ar0100_badge_params_fn(w, h, name)
    if ar0100_params is not None:
        return ar0100_params

    ac08_params = make_ac08_badge_params_fn(w, h, name, img)
    if ac08_params is not None:
        return ac08_params

    return None
