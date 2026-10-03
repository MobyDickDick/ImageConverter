from pathlib import Path

from tools.run_semantic_only_benchmark import SCHEMA_VERSION, _load_cases
from tools.generate_semantic_only_png_fixtures import generate_fixtures


def test_repository_png_benchmark_covers_three_topologies(tmp_path: Path) -> None:
    manifest = Path("config/semantic_only_png_benchmark_v1.json")
    seed, cases = _load_cases(manifest)

    assert SCHEMA_VERSION == "semantic_only_png_benchmark_v1"
    assert seed == 0
    assert {case["topology"] for case in cases} == {
        "circle+text+connector", "rectangle+diagonal", "polygon_path+line",
    }
    generated = generate_fixtures(tmp_path / "first")
    regenerated = generate_fixtures(tmp_path / "second")
    assert [path.name for path in generated] == [Path(case["image_path"]).name for case in cases]
    assert [path.read_bytes() for path in generated] == [path.read_bytes() for path in regenerated]
