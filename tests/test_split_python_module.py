from __future__ import annotations

from pathlib import Path

from tools.split_python_module import split_python_module


def test_function_strategy_keeps_functions_intact(tmp_path: Path) -> None:
    source = tmp_path / "demo.py"
    source.write_text(
        "import os\n\n"
        "def alpha():\n"
        "    return os.getcwd()\n\n"
        "def beta():\n"
        "    return alpha()\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    chunk_count, loader, chunk_dir = split_python_module(
        source_path=source,
        output_dir=output_dir,
        max_lines=4,
        loader_name="demo_loader.py",
        strategy="functions",
        call_table_path=None,
    )

    assert chunk_count >= 2
    assert loader.exists()
    chunks = {path.name: path.read_text(encoding="utf-8") for path in chunk_dir.glob("*.py")}
    assert any(name.endswith("alpha.py") for name in chunks)
    assert any(name.endswith("beta.py") for name in chunks)
    assert sum("def alpha():" in text for text in chunks.values()) == 1
    assert sum("def beta():" in text for text in chunks.values()) == 1


def test_call_table_written(tmp_path: Path) -> None:
    source = tmp_path / "demo.py"
    source.write_text(
        "def alpha():\n"
        "    return 1\n\n"
        "def beta():\n"
        "    return alpha()\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    call_table = tmp_path / "calls.csv"
    split_python_module(
        source_path=source,
        output_dir=output_dir,
        max_lines=100,
        loader_name="demo_loader.py",
        strategy="functions",
        call_table_path=call_table,
    )

    assert call_table.exists()
    rows = call_table.read_text(encoding="utf-8").strip().splitlines()
    assert rows[0] == "caller,callee"
    assert "beta,alpha" in rows
