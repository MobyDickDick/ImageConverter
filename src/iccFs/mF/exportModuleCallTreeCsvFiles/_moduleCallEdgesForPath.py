def moduleCallEdgesForPath(module_path: str | os.PathLike[str]) -> tuple[dict[str, int], list[dict[str, object]]]:
    """Return module-local callables and caller->callee edges for the given source file."""
    source_path = Path(module_path)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    callable_lines: dict[str, int] = {}
    local_function_names: set[str] = set()

    class CallableCollector(ast.NodeVisitor):
        def __init__(self):
            self._class_stack: list[str] = []

        def visitClassDef(self, node: ast.ClassDef):
            self._class_stack.append(node.name)
            self.generic_visit(node)
            self._class_stack.pop()

        def visitFunctionDef(self, node: ast.FunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            callable_lines[scoped_name] = node.lineno
            local_function_names.add(node.name)
            self.generic_visit(node)

        def visitAsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            callable_lines[scoped_name] = node.lineno
            local_function_names.add(node.name)
            self.generic_visit(node)

    CallableCollector().visit(tree)
    edges: list[dict[str, object]] = []

    class CallEdgeCollector(ast.NodeVisitor):
        def __init__(self):
            self._scope_stack: list[str] = []
            self._class_stack: list[str] = []

        def currentScope(self) -> str:
            return ".".join(self._scope_stack)

        def visitClassDef(self, node: ast.ClassDef):
            self._class_stack.append(node.name)
            self.generic_visit(node)
            self._class_stack.pop()

        def visitFunctionDef(self, node: ast.FunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            self._scope_stack.append(scoped_name)
            self.generic_visit(node)
            self._scope_stack.pop()

        def visitAsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            self._scope_stack.append(scoped_name)
            self.generic_visit(node)
            self._scope_stack.pop()

        def visitCall(self, node: ast.Call):
            caller = self.currentScope()
            callee = ""
            raw_callee = dottedAttrName(node.func)
            if isinstance(node.func, ast.Name):
                if node.func.id in local_function_names:
                    callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                owner = dottedAttrName(node.func.value)
                attr = node.func.attr
                if owner in {"self", "cls"} and self._class_stack:
                    candidate = f"{self._class_stack[-1]}.{attr}"
                    if candidate in callable_lines:
                        callee = candidate
                elif attr in local_function_names:
                    callee = attr

            if caller and callee:
                edges.append(
                    {
                        "caller": caller,
                        "callee": callee,
                        "caller_line": callable_lines.get(caller, 0),
                        "callee_line": callable_lines.get(callee, 0),
                        "call_line": getattr(node, "lineno", 0),
                        "raw_callee": raw_callee,
                    }
                )
            self.generic_visit(node)

    CallEdgeCollector().visit(tree)
    return callable_lines, edges
