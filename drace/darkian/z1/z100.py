import ast
import re

from drace.types import Context, Dict
from drace.constants import KEYWORDS


_ASSIGN_RE = re.compile(r"(?<![=!<>+\-*/%&|^])=(?!=)")


def _find_assignment_pos(line: str) -> int | None:
    """
    Return column index (0-based) of the assignment '=' for
    real assignments, or None
    """
    m = _ASSIGN_RE.search(line)
    if not m: return None
    return m.start()


def _is_simple_assignment(node: ast.AST) -> bool:
    """
    Return True for top-level Assign or AnnAssign statements
    that are not inside control-flow statements
    """
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False

    # Walk up the parent chain to ensure it's not inside an
    # `If`, `For`, etc.
    control_structs = (ast.If, ast.For, ast.While, ast.With,
                       ast.Try, ast.Match)
    parent = getattr(node, 'parent', None)
    while parent:
        if isinstance(parent, ast.Module): break
        if isinstance(parent, control_structs): return False
        parent = getattr(parent, 'parent', None)

    return True


def _line_indentation(line: str) -> int:
    """Count leading spaces (or tabs)."""
    return len(line) - len(line.lstrip(' '))


def _is_simple_assignment_line(line: str) -> bool:
    """Naive assignment check, will improve if needed."""
    stripped = line.lstrip()
    # Exclude if line starts with control keyword followed by
    # assignment
    if any(stripped.startswith(kw) for kw in KEYWORDS):
        return False

    return '=' in stripped and not stripped.startswith('#')


def _group_assignments_by_indent(assign_ln:
        list[int], lines: list[str]) -> list[list[int]]:
    groups        = []
    current_group = []
    last_indent   = None

    for i, lineno in enumerate(assign_ln):
        line = lines[lineno - 1]
        if not _is_simple_assignment_line(line): continue

        indent = _line_indentation(line)

        if not current_group:
            current_group.append(lineno)
            last_indent = indent
            continue

        prev_lineno = assign_ln[i - 1]
        if lineno == prev_lineno + 1:
            prev_line = lines[prev_lineno].strip()
            if indent == last_indent and prev_line:
                current_group.append(lineno)
            else:
                groups.append(current_group)
                current_group = [lineno]
                last_indent   = indent
        else:
            groups.append(current_group)
            current_group = [lineno]
            last_indent   = indent

    if current_group: groups.append(current_group)

    return groups


def _collect_assignment_lines_and_blocks(tree
        ) -> list[tuple[int, ast.AST]]:
    """
    Return list of (lineno, node) for assignment-like
    statements found in AST, sorted by lineno.
    """
    out = []

    for node in ast.walk(tree):
        if _is_simple_assignment(node):
            # Some AnnAssign (x: int = 1) may not have lineno
            # if generated; check presence
            if hasattr(node, "lineno"):
                out.append((node.lineno, node))

    out.sort(key=lambda t: t[0])
    return out


def check_z100(context: Context) -> list[Dict]:
    """
    Z100: Enforce vertical alignment of `=` in real
          assignment blocks.
    """
    lines     = context["lines"]
    tree      = context["tree"]
    file      = context["file"]
    results   = []
    assigns   = _collect_assignment_lines_and_blocks(tree)
    assign_ln = [ln for ln, _ in assigns]
    groups    = _group_assignments_by_indent(assign_ln, lines)

    for group in groups:
        # build the lines corresponding to those assignment
        # line numbers
        eq_positions = []
        eq_pos_map   = {}
        for idx, ln in enumerate(group):
            line = lines[ln - 1]
            pos  = _find_assignment_pos(line)
            if pos is None: continue
            eq_positions.append(pos)
            eq_pos_map[ln] = pos
        if not eq_positions: continue
        target = max(eq_positions)
        for ln, pos in eq_pos_map.items():
            if pos != target:
                results.append({
                    "file": file,
                    "line": ln,
                    "col": pos + 1,
                    "code": "Z100",
                    "msg": "assignment not vertically aligned"
                })

    return results
