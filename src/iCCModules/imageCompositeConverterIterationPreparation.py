from __future__ import annotations

import os


def prepareIterationInputsImpl(
    *,
    img_path: str,
    csv_path: str,
    perception_cls,
    reflection_cls,
    detect_gradient_stripe_strategy_fn,
    build_pending_semantic_audit_row_fn,
    should_create_semantic_audit_for_base_name_fn,
    get_base_name_from_file_fn,
    build_semantic_audit_record_kwargs_fn,
    semantic_audit_record_fn,
    np_module,
    print_fn=print,
):
    folder_path = os.path.dirname(img_path)
    filename = os.path.basename(img_path)
    perception = perception_cls(img_path, csv_path)
    if perception.img is None:
        return None

    height, width = perception.img.shape[:2]
    reflection = reflection_cls(perception.raw_desc)
    description, params = reflection.parse_description(perception.base_name, filename)
    stripe_strategy = detect_gradient_stripe_strategy_fn(
        perception.img,
        np_module=np_module,
    )
    semantic_audit_row = build_pending_semantic_audit_row_fn(
        base_name=perception.base_name,
        filename=filename,
        params=params,
        should_create_semantic_audit_for_base_name_fn=should_create_semantic_audit_for_base_name_fn,
        get_base_name_from_file_fn=get_base_name_from_file_fn,
        build_semantic_audit_record_kwargs_fn=build_semantic_audit_record_kwargs_fn,
        semantic_audit_record_fn=semantic_audit_record_fn,
    )

    if not description.strip() and params["mode"] != "semantic_badge":
        print_fn("  -> Überspringe Bild, da keine begleitende textliche Beschreibung vorliegt.")
        return None

    return {
        "folder_path": folder_path,
        "filename": filename,
        "perception": perception,
        "width": width,
        "height": height,
        "description": description,
        "params": params,
        "stripe_strategy": stripe_strategy,
        "semantic_audit_row": semantic_audit_row,
    }
