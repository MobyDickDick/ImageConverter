def export_module_call_tree_csv(
    output_csv_path: str | os.PathLike[str] = DEFAULT_CALL_TREE_CSV_PATH,
    module_path: str | os.PathLike[str] = __file__,
) -> str:
    callable_lines, edges = _module_call_edges_for_path(module_path)
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
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "root", "node", "depth", "parent", "node_line", "edge_caller", "edge_callee",
            "edge_call_line", "edge_caller_line", "edge_callee_line", "edge_raw_callee",
        ])
        edge_by_pair = {(str(edge["caller"]), str(edge["callee"])): edge for edge in edges}
        for root, node, depth, parent, node_line in tree_rows:
            edge = edge_by_pair.get((parent, node)) if parent else None
            writer.writerow([
                root, node, depth, parent, node_line,
                parent if edge else "",
                node if edge else "",
                int(edge["call_line"]) if edge else "",
                int(edge["caller_line"]) if edge else "",
                int(edge["callee_line"]) if edge else "",
                str(edge["raw_callee"]) if edge else "",
            ])
    return output_path
""" End move to File mainFiles/export_module_call_tree_csv.py """

""" Start move to File mainFiles/convert_rangeFiles/_in_requested_rangeFiles/get_base_name_from_file.py
import src
"""
def get_base_name_from_file(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r"(-\d+)$", "", name)
    while True:
        prev = name
        name = re.sub(r"_([1-9]|L|M|S|[1-9]S|W|X)$", "", name, flags=re.IGNORECASE)
        if name == prev:
            break
    return name
""" End move to File mainFiles/convert_rangeFiles/_in_requested_rangeFiles/get_base_name_from_file.py """


@dataclass
class Perception:
    img_path: str
    csv_path: str

    def __post_init__(self) -> None:
        self.base_name = get_base_name_from_file(os.path.basename(self.img_path))
        self.img = cv2.imread(self.img_path)
        self.raw_desc = self._load_descriptions()

    def _load_descriptions(self) -> dict[str, str]:
        return _load_description_mapping(self.csv_path)


@dataclass(frozen=True)
class SourceSpan:
    """Optional source location attached to diagnostics for user-facing data files."""

    path: str
    line: int | None = None
    column: int | None = None

    def format(self) -> str:
        location = self.path
        if self.line is not None:
            location += f":{self.line}"
            if self.column is not None:
                location += f":{self.column}"
        return location


