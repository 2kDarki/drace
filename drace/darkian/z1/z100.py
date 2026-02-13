import ast

from drace.types import Context, Dict


MIN_GROUP = 4


def _is_control_scope(node: ast.AST) -> bool:
    return isinstance(
        node,
        (
            ast.If,
            ast.For,
            ast.While,
            ast.With,
            ast.Try,
            ast.Match,
            ast.AsyncFor,
            ast.AsyncWith,
        ),
    )


def _is_top_level_assignment(node: ast.AST) -> bool:
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return False
    if node.lineno != node.end_lineno:
        return False

    parent = getattr(node, "parent", None)
    if isinstance(parent, ast.Module):
        return True
    if _is_control_scope(parent):
        return False
    return False


def _first_target(node: ast.Assign | ast.AnnAssign) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        return node.targets[0] if node.targets else None
    return node.target


def _assignment_eq_col(node: ast.Assign | ast.AnnAssign, line: str) -> int | None:
    """
    Find the physical '=' column from an assignment AST node.
    """
    target = _first_target(node)
    if target is None or not hasattr(target, "end_col_offset"):
        return None

    start = int(getattr(target, "end_col_offset", 0))
    if isinstance(node, ast.AnnAssign):
        # Skip annotation part: x: int = 1
        start = int(getattr(node.annotation, "end_col_offset", start))

    # Look for the first standalone '=' after target/annotation.
    idx = line.find("=", start)
    if idx == -1:
        return None
    # Exclude "==" and walrus.
    if idx > 0 and line[idx - 1] in ("=", ":"):
        return None
    if idx + 1 < len(line) and line[idx + 1] == "=":
        return None
    return idx


def _group_assignments(
    nodes: list[ast.Assign | ast.AnnAssign],
) -> list[list[ast.Assign | ast.AnnAssign]]:
    """
    Group contiguous top-level assignments by indentation.
    """
    groups: list[list[ast.Assign | ast.AnnAssign]] = []
    current: list[ast.Assign | ast.AnnAssign] = []
    prev_lineno = None
    prev_indent = None

    for node in sorted(nodes, key=lambda n: (n.lineno, n.col_offset)):
        if prev_lineno is None:
            current = [node]
        else:
            contiguous = node.lineno == prev_lineno + 1
            same_indent = node.col_offset == prev_indent
            if contiguous and same_indent:
                current.append(node)
            else:
                if current:
                    groups.append(current)
                current = [node]

        prev_lineno = node.lineno
        prev_indent = node.col_offset

    if current:
        groups.append(current)
    return groups


def check_z100(context: Context) -> list[Dict]:
    """
    Z100: Enforce vertical alignment of `=` in real
          assignment blocks.
    """
    lines = context["lines"]
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []

    candidates: list[ast.Assign | ast.AnnAssign] = [
        node for node in ast.walk(tree)
        if _is_top_level_assignment(node)
    ]

    for group in _group_assignments(candidates):
        if len(group) < MIN_GROUP:
            continue
        eq_positions: dict[int, int] = {}
        for node in group:
            line = lines[node.lineno - 1]
            eq_col = _assignment_eq_col(node, line)
            if eq_col is not None:
                eq_positions[node.lineno] = eq_col

        if len(eq_positions) < 2:
            continue

        target_col = max(eq_positions.values())
        for lineno, col in eq_positions.items():
            if col != target_col:
                results.append({
                    "file": file,
                    "line": lineno,
                    "col": col + 1,
                    "code": "Z100",
                    "msg": "assignment not vertically aligned",
                })

    return results
