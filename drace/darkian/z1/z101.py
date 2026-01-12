import importlib.util
import site
import os

from drace.utils import Align, any_eq, all_in, any_in
from drace.types import Context, Dict
from drace.utils import find_proot


PROOT = None


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
                if name not in PROOT: return "builtin"

            # Normalize to absolute path if it looks like a
            # filesystem path
            try: origin_abs = os.path.abspath(origin)
            except Exception: origin_abs = origin
            return origin_abs

        # Heuristic for relative imports
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
    try: origin_abs = os.path.abspath(origin)
    except Exception: origin_abs = origin

    origin_l = origin_abs.lower() if isinstance(origin_abs,
               str) else ""

    # Heuristic: if 'python' appears in the origin path
    # (stdlib) -> STANDARDS
    if "python" in origin_l and not any_in("site-packages",
        "dist-packages", eq=origin_l): return "STANDARDS"

    # site-packages and dist-packages indicate third-party
    if any_in("site-packages", "dist-packages", eq=origin_l)\
            or _is_editable_third_party(origin_l):
        return "THIRD_PARTIES"

    # Fallback: if not stdlib or 3rd-party, then local
    return "LOCALS"


def _import_key_length(line: str) -> int:
    """
    Used to sort imports by descending physical line length.
    """
    return len(line.rstrip("\n"))


def _render_darkian_block(grouped_lines: dict[str,
        list[str]], preserve_order: list[str]) -> str:
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
        if not lines: continue
        if group == "FUTURE":
            sections.append("\n".join(lines))
            sections.append("")  # blank line separator
            continue
        # add section header for non-FUTURE groups
        center = Align(offset=2).center
        if group == "STANDARDS":
            sections.append(f"\n# {center(' STANDARDS ',
                '=')}")
        elif group == "THIRD_PARTIES":
            sections.append(f"# {center(' THIRD PARTIES ',
                '=')}")
        elif group == "LOCALS":
            sections.append(f"# {center(' LOCALS ', '=')}")
        sections.extend(lines)
        sections.append("")  # blank line after section

    # Trim trailing blank lines
    while sections and sections[-1] == "": sections.pop()
    return "\n".join(sections)


def check_z101(context: Context) -> list[Dict]:
    """
    In import blocks, order imports by descending line
    length — grouped by Darkian Standard.
    """
    global PROOT
    lines   = context["lines"]
    file    = context["file"]
    PROOT   = find_proot(file)
    results = []
    cwd     = os.getcwd()

    # Collect contiguous import blocks: sequence of
    # import/from lines (allow inline comments but break on
    # other code)
    import_blocks = []
    cur_block     = []
    cur_start     = None
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
    if cur_block: import_blocks.append((cur_start, cur_block))

    for i, (start_idx, block) in enumerate(import_blocks):
        # block: list of (index, line)
        # Build classification per import line; also preserve
        # original text
        grouped: dict[str, list[tuple[str, int]]] = {
            "FUTURE": [],
            "STANDARDS": [],
            "THIRD_PARTIES": [],
            "LOCALS": []
        }
        for idx, (li, line) in enumerate(block):
            stripped = line.strip()
            # parse the import name for heuristics:
            # handle 'from X import ...' or 'import X as Y'
            # or 'import X, Y'
            module_name = None
            if stripped.startswith("from "):
                # from X import ...
                parts = stripped.split()
                if len(parts) >= 2: module_name = parts[1]
            elif stripped.startswith("import "):
                # import a, b as c
                rest = stripped[len("import "):].split(","
                       )[0].strip()
                # take first module name, remove 'as ...' if
                # present
                module_name = rest.split()[0]
            if module_name is None: module_name = ""

            grp = _classify_import(module_name, cwd)
            # store original line and its raw length for
            # later sorting by descending length
            grouped.setdefault(grp, []).append((
                line.rstrip("\n"), start_idx + idx + 1))

        # If everything already ordered by descending length
        # within each section and sections in right order,
        # skip
        # Build grouped lines sorted by descending length
        preserve_order = ["FUTURE", "STANDARDS",
                          "THIRD_PARTIES", "LOCALS"]
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
            "msg": "import block not ordered by Darkian "
                   "Standard (descending length per "
                  f"section). Suggestion:{suggestion_text}"
        })

    return results
