from pathlib import Path
import importlib.util
import site
import ast
import os
import re

from drace.utils import Align, any_eq, all_in, find_proot
from drace.constants import KEYWORDS


PROOT      = None
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
    control_structs = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.Match)
    parent = getattr(node, 'parent', None)
    while parent:
        if isinstance(parent, control_structs): return False
        parent = getattr(parent, 'parent', None)

    return True


def _line_indentation(line: str) -> int:
    """Count leading spaces (or tabs)"""
    return len(line) - len(line.lstrip(' '))


def _is_assignment_line(line: str) -> bool:
    """naive assignment check, will improve if needed"""
    stripped = line.lstrip()
    # Exclude if line starts with control keyword followed by
    # assignment
    if any(stripped.startswith(kw) for kw in KEYWORDS):
        return False

    return '=' in stripped and not stripped.startswith('#')


def _group_assignments_by_indent(assign_line_numbers: list[int], lines: list[str]) -> list[list[int]]:
    groups        = []
    current_group = []
    last_indent   = None

    for i, lineno in enumerate(assign_line_numbers):
        line   = lines[lineno - 1]
        indent = _line_indentation(line)

        if not current_group:
            current_group.append(lineno)
            last_indent = indent
            continue

        prev_lineno = assign_line_numbers[i - 1]
        if lineno == prev_lineno + 1:
            if indent == last_indent and lines[prev_lineno].strip():
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


def _collect_assignment_lines_and_blocks(tree) -> list[tuple[int, ast.AST]]:
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


def _group_consecutive_lines(lines: list[int]) -> list[list[int]]:
    if not lines: return []
    groups = [[lines[0]]]
    for ln in lines[1:]:
        if ln == groups[-1][-1] + 1: groups[-1].append(ln)
        else: groups.append([ln])
    return groups


def _module_spec_origin(name: str) -> str | None:
    """
    Try to locate module spec origin. Returns:
      - absolute path to the module file if found
      - the strings 'builtin' for builtins
      - '__future__' for __future__
      - None when spec couldn't be resolved
    """
    if name == "__future__": return name
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        prefix = ".".join(parts[:i])
        try: spec = importlib.util.find_spec(prefix)
        except Exception: spec = None
        if spec:
            origin   = getattr(spec, "origin", None)
            builtins = ("built-in", "frozen")
            if origin is None or any_eq(builtins, eq=origin):
                return "builtin"
            # Normalize to absolute path if it looks like a
            # filesystem path
            try: origin_abs = os.path.abspath(origin)
            except Exception: origin_abs = origin
            return origin_abs
        # heuristic for relative imports
        elif name.startswith("."): return PROOT.lower()
    return None


def _is_editable_third_party(path: str) -> bool:
    """Check for .pth files that indicate editable install"""
    if PROOT.lower() in path: return False

    try: pkgs = os.listdir(site.getsitepackages()[0])
    except FileNotFoundError: return False

    editables = [pkg.split(".", 1)[1].replace("pth", 
                "dist-info") for pkg in pkgs if all_in(
                "editable", "pth", eq=pkg)]

    for editable in editables:
        for pkg in pkgs:
            if editable == pkg: return True

    return False


def _classify_import(name: str, cwd: str) -> str:
    """
    Return one of: 'FUTURE', 'STANDARDS', 'THIRD_PARTIES', 
    'LOCALS'
    Robust against origin values that are special tokens or 
    non-absolute paths.
    """
    if name == "__future__": return "FUTURE"

    origin = _module_spec_origin(name)
    # If we couldn't resolve an origin, conservatively call 
    # it THIRD_PARTIES
    if not origin: return "THIRD_PARTIES"

    # Handle special tokens
    if origin == "__future__": return "FUTURE"
    if origin == "builtin": return "STANDARDS"

    # At this point origin should be a path-like string 
    # (absolute or relative).
    # Make both cwd and origin absolute if possible.
    try: cwd_abs = os.path.abspath(cwd) if cwd else None
    except Exception: cwd_abs = cwd

    try: origin_abs = os.path.abspath(origin)
    except Exception: origin_abs = origin

    origin_l = origin_abs.lower() if isinstance(origin_abs, str) else ""
    
    # Heuristic: if 'python' appears in the origin path 
    # (stdlib) -> STANDARDS
    if "python" in origin_l and "site-packages" not in origin_l and "dist-packages" not in origin_l:
        return "STANDARDS"

    # site-packages and dist-packages indicate third-party
    if "site-packages" in origin_l or "dist-packages" in origin_l or _is_editable_third_party(origin_l):
        return "THIRD_PARTIES"

    # Fallback: if not stdlib or 3rd-party, then local
    return "LOCALS"


def _import_key_length(line: str) -> int:
    """Used to sort imports by descending physical line length."""
    return len(line.rstrip("\n"))


def _render_darkian_block(grouped_lines: dict[str, list[str]], preserve_order: list[str]) -> str:
    """
    Build the Darkian-standard import block string.

    `grouped_lines` maps group name -> list of import lines
    (strings).
    `preserve_order` ensures FUTURE comes first etc.
    """
    sections = []
    # FUTURE at top if present
    for group in preserve_order:
        lines = grouped_lines.get(group, [])
        if not lines:
            continue
        if group == "FUTURE":
            sections.append("\n".join(lines))
            sections.append("")  # blank line separator
            continue
        # add section header for non-FUTURE groups
        center = Align(offset=2).center
        if group == "STANDARDS":
            sections.append(f"\n# {center(' STANDARDS ', '=')}")
        elif group == "THIRD_PARTIES":
            sections.append(f"# {center(' THIRD PARTIES ', '=')}")
        elif group == "LOCALS":
            sections.append(f"# {center(' LOCALS ', '=')}")
        sections.extend(lines)
        sections.append("")  # blank line after section

    # trim trailing blank lines
    while sections and sections[-1] == "": sections.pop()
    return "\n".join(sections)


def rule_alignment(lines: list[str], tree, file: str) -> list[dict]:
    """
    Z100: Enforce vertical alignment of `=` in real assignment blocks.
    Z101: In import blocks, order imports by descending line length — grouped by Darkian Standard.
    """
    global PROOT
    PROOT   = find_proot(file)
    results = []
    cwd     = os.getcwd()

    # ======= Z100: assignment alignment (AST-driven) =======
    assigns = _collect_assignment_lines_and_blocks(tree)
    assign_line_numbers = [ln for ln, _ in assigns]
    groups = _group_assignments_by_indent(
             assign_line_numbers, lines)

    for group in groups:
        # build the lines corresponding to those assignment
        # line numbers
        block_lines  = [lines[ln - 1] for ln in group]
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
                    "msg": "assignment not vertically aligned",
                })

    # ====== Z101: import ordering and Darkian grouping =====
    # Collect contiguous import blocks: sequence of
    # import/from lines (allow inline comments but break on 
    # other code)
    import_blocks: list[tuple[int, list[tuple[int, str]]]] = []
    cur_block: list[tuple[int, str]] = []
    cur_start = None
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("import ") or s.startswith("from "):
            if cur_start is None: cur_start = i
            cur_block.append((i, raw))
        else:
            if cur_block:
                import_blocks.append((cur_start, cur_block))
                cur_block = []
                cur_start = None
    if cur_block:
        import_blocks.append((cur_start, cur_block))

    for i, (start_idx, block) in enumerate(import_blocks):
        # block: list of (index, line)
        # Build classification per import line; also preserve
        # original text
        grouped: dict[str, list[tuple[str, int]]] = {"FUTURE": [], "STANDARDS": [], "THIRD_PARTIES": [], "LOCALS": []}
        for idx, (li, line) in enumerate(block):
            stripped = line.strip()
            # parse the import name for heuristics:
            # handle 'from X import ...' or 'import X as Y'
            # or 'import X, Y'
            module_name = None
            if stripped.startswith("from "):
                # from X import ...
                parts = stripped.split()
                if len(parts) >= 2:
                    module_name = parts[1]
            elif stripped.startswith("import "):
                # import a, b as c
                rest = stripped[len("import "):].split(",")[0].strip()
                # take first module name, remove 'as ...' if
                # present
                module_name = rest.split()[0]
            if module_name is None: module_name = ""

            grp = _classify_import(module_name, cwd)
            # store original line and its raw length for
            # later sorting by descending length
            grouped.setdefault(grp, []).append((line.rstrip("\n"), start_idx + idx + 1))

        # If everything already ordered by descending length 
        # within each section and sections in right order,
        # skip
        # Build grouped lines sorted by descending length
        preserve_order = ["FUTURE", "STANDARDS", "THIRD_PARTIES", "LOCALS"]
        grouped_sorted_texts: dict[str, list[str]] = {}
        correct_order = []
        for g in preserve_order:
            items = grouped.get(g, [])
            if not items:
                grouped_sorted_texts[g] = []
                continue
            # sort by descending length of the import text
            sorted_items = sorted(items, key=lambda t:
                           len(t[0]), reverse=True)
            grouped_sorted_texts[g] = [t[0] for t in 
                                       sorted_items]
            correct_order.extend(grouped_sorted_texts[g])

        current_order = []
        for _, statement in import_blocks[i][1]:
            current_order.append(statement)

        # If not out of order overall, continue
        if current_order == correct_order: continue

        # Otherwise, produce a suggestion block in Darkian 
        # format
        suggestion_text = _render_darkian_block(
                          grouped_sorted_texts,
                          preserve_order)

        # Build Z101 results for every line that is 
        # out-of-order (we'll flag the original positions)
        # For clarity give one aggregated result at the start
        # of the block with the suggestion
        results.append({
            "file": file,
            "line": start_idx + 1,
            "col": 1,
            "code": "Z101",
            "msg": f"import block not ordered by Darkian Standard (descending length per section). Suggestion:{suggestion_text}"
        })

    return results
