from __future__ import annotations

from src.iCCModules import imageCompositeConverterAudit as audit_helpers


def test_collect_description_fragments_keeps_lookup_order() -> None:
    raw_desc = {
        "ac0811_s": "variant",
        "AC0811": "base",
    }

    rows = audit_helpers.collectDescriptionFragmentsImpl(
        raw_desc,
        base_name="AC0811",
        img_filename="ac0811_s.jpg",
        get_base_name_fn=lambda value: value,
    )

    assert rows == [
        {"source": "base_name", "key": "AC0811", "text": "base"},
        {"source": "variant_name", "key": "ac0811_s", "text": "variant"},
    ]


def test_collect_description_fragments_skips_duplicate_lookup_keys_and_texts() -> None:
    rows = audit_helpers.collectDescriptionFragmentsImpl(
        {"AC0800": "ring family"},
        base_name="AC0800",
        img_filename="AC0800.jpg",
        get_base_name_fn=lambda value: value,
    )

    assert rows == [
        {"source": "base_name", "key": "AC0800", "text": "ring family"},
    ]


def test_collect_description_fragments_prefers_exact_variant_when_filename_collapses_to_base() -> None:
    rows = audit_helpers.collectDescriptionFragmentsImpl(
        {
            "AC0VR2": "family alias with checkmark",
            "AC0VR2_AB_M": "exact custom panel variant",
        },
        base_name="AC0VR2",
        img_filename="AC0VR2_AB_M.jpg",
        get_base_name_fn=lambda value: "AC0VR2" if str(value).startswith("AC0VR2") else str(value),
    )

    assert rows == [
        {"source": "variant_name", "key": "AC0VR2_AB_M", "text": "exact custom panel variant"},
    ]
