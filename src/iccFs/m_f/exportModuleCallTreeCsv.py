def exportModuleCallTreeCsv(
    output_csv_path: str | os.PathLike[str] = DEFAULT_CALL_TREE_CSV_PATH,
    module_path: str | os.PathLike[str] = __file__,
) -> str:
    """Export a module-local call tree/table as CSV and return the written path."""
    callable_lines, edges = _moduleCallEdgesForPath(module_path)
    incoming: dict[str, int] = {name: 0 for name in callable_lines}
    adjacency: dict[str, set[str]] = {name: set() for name in callable_lines}
    for edge in edges:
        caller = str(edge["caller"])
        callee = str(edge["callee"])
        adjacency.setdefault(caller, set()).add(callee)
        incoming[callee] = incoming.get(callee, 0) + 1

    roots = sorted([name for name in callable_lines if incoming.get(name, 0) == 0], key=lambda n: callable_lines[n])
    if not roots:
        roots = sorted(callable_lines, key=lambda n: callable_lines[n])

    tree_rows: list[tuple[str, str, int, str, int]] = []

    def walk(node: str, root: str, depth: int, parent: str, path: tuple[str, ...]):
        tree_rows.append((root, node, depth, parent, callable_lines.get(node, 0)))
        for child in sorted(adjacency.get(node, set()), key=lambda n: callable_lines.get(n, 0)):
            if child in path:
                continue
            walk(child, root, depth + 1, node, path + (child,))

    for root in roots:
        walk(root, root, 0, "", (root,))

    output_path = os.fspath(output_csv_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "root",
                "node",
                "depth",
                "parent",
                "node_line",
                "edge_caller",
                "edge_callee",
                "edge_call_line",
                "edge_caller_line",
                "edge_callee_line",
                "edge_raw_callee",
            ]
        )
        edge_by_pair = {(str(edge["caller"]), str(edge["callee"])): edge for edge in edges}
        for root, node, depth, parent, node_line in tree_rows:
            edge = edge_by_pair.get((parent, node)) if parent else None
            writer.writerow(
                [
                    root,
                    node,
                    depth,
                    parent,
                    node_line,
                    parent if edge else "",
                    node if edge else "",
                    int(edge["call_line"]) if edge else "",
                    int(edge["caller_line"]) if edge else "",
                    int(edge["callee_line"]) if edge else "",
                    str(edge["raw_callee"]) if edge else "",
                ]
            )
    return output_path
