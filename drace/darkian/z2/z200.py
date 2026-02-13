import ast
import os

from drace.types import Context, Dict
from drace.constants import LINE_LEN


COMPACTABLE_CONTROLS = (ast.If,)
NESTED_CONTROL = COMPACTABLE_CONTROLS + (ast.Try, ast.Match)


def _has_alt_branch(node: ast.AST) -> bool:
    orelse = getattr(node, "orelse", None)
    return bool(orelse)


def _is_single_simple_stmt(node: ast.AST) -> bool:
    body = getattr(node, "body", [])
    if len(body) != 1:
        return False
    stmt = body[0]
    if isinstance(stmt, NESTED_CONTROL):
        return False
    compactable = (ast.Return, ast.Raise)
    return isinstance(stmt, compactable)


def _one_liner_len(src: str, node: ast.AST) -> int | None:
    if getattr(node, "lineno", -1) == getattr(node, "end_lineno", -2):
        # Already compacted.
        return None
    body = node.body[0]
    header = ast.get_source_segment(src, node) or ""
    inner = ast.get_source_segment(src, body) or ""
    if not header or not inner:
        return None

    # For block nodes, header includes body on single-line forms.
    # Rebuild from the first line up to ":" to estimate compact length.
    header_line = header.splitlines()[0]
    if ":" not in header_line:
        return None
    lead = header_line[: header_line.index(":") + 1].rstrip()
    body = inner.strip()
    if len(body) > 28:
        return None
    if len(lead) > 52:
        return None
    return len(f"{lead} {body}")


def check_z200(context: Context) -> list[Dict]:
    """
    Z200: suggest compact one-liners for very small control blocks.
    """
    tree = context["tree"]
    file = context["file"]
    src = "\n".join(context["lines"])
    results: list[Dict] = []

    if f"{os.sep}drace{os.sep}darkian{os.sep}" in os.path.abspath(file):
        return results

    for node in ast.walk(tree):
        if not isinstance(node, COMPACTABLE_CONTROLS):
            continue
        if isinstance(node, ast.If):
            test = ast.get_source_segment(src, node.test) or ""
            if "__name__" in test and "__main__" in test:
                continue
        if _has_alt_branch(node):
            continue
        if not _is_single_simple_stmt(node):
            continue

        compact_len = _one_liner_len(src, node)
        if compact_len is None or compact_len > LINE_LEN:
            continue

        results.append({
            "file": file,
            "line": node.lineno,
            "col": getattr(node, "col_offset", 0) + 1,
            "code": "Z200",
            "msg": "control block could be compacted to a one-liner",
        })

    return results
