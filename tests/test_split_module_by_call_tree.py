from __future__ import annotations

from pathlib import Path

from tools.split_module_by_call_tree import parse_call_tree_edges, write_import_loader


def test_parse_call_tree_edges_supports_comma_delimiter(tmp_path: Path) -> None:
    csv_path = tmp_path / "calls.csv"
    csv_path.write_text(
        "edge_caller,edge_callee\nmain,alpha\nmain,beta\n",
        encoding="utf-8",
    )

    edges = parse_call_tree_edges(csv_path)

    assert edges["main"] == {"alpha", "beta"}


def test_write_import_loader_uses_regular_import_statements(tmp_path: Path) -> None:
    loader = tmp_path / "__init__.py"
    snippets = {
        "alpha": "def alpha():\n    return 1\n",
        "beta": "def beta():\n    return alpha()\n",
        "MyClass.method": "def method(self):\n    return 1\n",
    }

    write_import_loader(loader, snippets)

    content = loader.read_text(encoding="utf-8")
    assert "from .alpha import alpha" in content
    assert "from .beta import beta" in content
    assert "MyClass.method" not in content
