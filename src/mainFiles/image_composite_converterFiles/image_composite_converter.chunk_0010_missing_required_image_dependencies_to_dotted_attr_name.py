
def _missing_required_image_dependencies() -> list[str]:
    return missing_required_image_dependencies(cv2_module=cv2, np_module=np)


""" Start move to File mainFiles/_bootstrap_required_image_dependencies.py
import src
"""
def _bootstrap_required_image_dependencies() -> list[str]:
    global cv2, np
    missing, cv2, np = bootstrap_required_image_dependencies(cv2_module=cv2, np_module=np)
    return missing
""" End move to File mainFiles/_bootstrap_required_image_dependencies.py """


def rgb_to_hex(rgb: np.ndarray) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))



def _dotted_attr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _dotted_attr_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


""" Start move to File mainFiles/export_module_call_tree_csvFiles/_module_call_edges_for_path.py
import src
"""
