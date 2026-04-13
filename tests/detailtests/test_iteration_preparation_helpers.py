from src.iCCModules import imageCompositeConverterIterationPreparation as iteration_preparation_helpers


class _FakePerception:
    def __init__(self, _img_path: str, _csv_path: str) -> None:
        self.img = _FakeImage(48, 96)
        self.base_name = "AC0800_S"
        self.raw_desc = "desc"


class _FakeImage:
    def __init__(self, height: int, width: int) -> None:
        self.shape = (height, width, 3)


class _FakeReflection:
    def __init__(self, _raw_desc: str) -> None:
        pass

    def parse_description(self, _base_name: str, _filename: str):
        return "Beschreibung", {"mode": "composite"}


def test_prepare_iteration_inputs_impl_builds_iteration_context() -> None:
    captured: dict[str, object] = {}

    def _detect_gradient(_img, *, np_module):
        captured["np_module"] = np_module
        return {"mode": "normal"}

    def _build_pending_row(**kwargs):
        captured["audit_kwargs"] = kwargs
        return {"status": "semantic_pending"}

    result = iteration_preparation_helpers.prepareIterationInputsImpl(
        img_path="input/AC0800_S.jpg",
        csv_path="docs/desc.csv",
        perception_cls=_FakePerception,
        reflection_cls=_FakeReflection,
        detect_gradient_stripe_strategy_fn=_detect_gradient,
        build_pending_semantic_audit_row_fn=_build_pending_row,
        should_create_semantic_audit_for_base_name_fn=lambda _base_name: True,
        get_base_name_from_file_fn=lambda name: name,
        build_semantic_audit_record_kwargs_fn=lambda **kwargs: kwargs,
        semantic_audit_record_fn=lambda **kwargs: kwargs,
        np_module="np-sentinel",
    )

    assert result is not None
    assert result["folder_path"] == "input"
    assert result["filename"] == "AC0800_S.jpg"
    assert result["width"] == 96
    assert result["height"] == 48
    assert result["description"] == "Beschreibung"
    assert result["params"] == {"mode": "composite"}
    assert result["stripe_strategy"] == {"mode": "normal"}
    assert result["semantic_audit_row"] == {"status": "semantic_pending"}
    assert captured["np_module"] == "np-sentinel"
    assert captured["audit_kwargs"]["base_name"] == "AC0800_S"


def test_prepare_iteration_inputs_impl_returns_none_for_missing_description_non_semantic_badge() -> None:
    class _ReflectionNoDesc:
        def __init__(self, _raw_desc: str) -> None:
            pass

        def parse_description(self, _base_name: str, _filename: str):
            return "   ", {"mode": "composite"}

    printed: list[str] = []
    result = iteration_preparation_helpers.prepareIterationInputsImpl(
        img_path="input/AC0800_S.jpg",
        csv_path="docs/desc.csv",
        perception_cls=_FakePerception,
        reflection_cls=_ReflectionNoDesc,
        detect_gradient_stripe_strategy_fn=lambda *_args, **_kwargs: None,
        build_pending_semantic_audit_row_fn=lambda **_kwargs: None,
        should_create_semantic_audit_for_base_name_fn=lambda _base_name: True,
        get_base_name_from_file_fn=lambda name: name,
        build_semantic_audit_record_kwargs_fn=lambda **kwargs: kwargs,
        semantic_audit_record_fn=lambda **kwargs: kwargs,
        np_module="np-sentinel",
        print_fn=printed.append,
    )

    assert result is None
    assert printed == ["  -> Überspringe Bild, da keine begleitende textliche Beschreibung vorliegt."]
