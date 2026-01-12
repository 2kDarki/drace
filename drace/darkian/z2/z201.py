import ast

from drace.types import Context, Dict
from drace import utils


CONTROL_NODE_TYPES = (ast.If, ast.For, ast.While, ast.With,
                      ast.Try, ast.AsyncFor, ast.AsyncWith)


def _is_comment_or_empty(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#")


def _is_semicolon_compound(line: str) -> bool:
    """
    Return True if the physical line contains multiple
    independent Python statements
    separated by semicolons. We use
    `utils.tolerant_parse_module` to avoid false positives
    (strings, SQL, etc).
    """
    tree = utils.tolerant_parse_module(line)
    # Treat as compound only if parse produced 2+ top-level
    # statements
    return len(getattr(tree, "body", [])) >= 2


def check_z201(context: Context) -> list[Dict]:
    """
    Z201: Warn against over-compacted blocks.

    Flags:
      - control blocks written on a single physical line whose
        total length > utils.LINE_LEN
      - semicolon-joined single physical lines that parse to
        multiple statements and exceed utils.LINE_LEN

    Conservative: uses AST to avoid false positives.
    """
    lines   = context["lines"]
    tree    = context["tree"]
    file    = context["file"]
    results = []
    src     = "\n".join(lines)
    for node in ast.walk(tree):
        if isinstance(node, CONTROL_NODE_TYPES):
            # Ensure node has location info
            if not hasattr(node, "lineno") \
                or not hasattr(node, "end_lineno"): continue
            # Only care about nodes that occupy a single
            # physical line
            if node.lineno != node.end_lineno: continue
            # Get src for the node; ast.get_source_segment
            # may return None in some cases
            try: node_src = ast.get_source_segment(src, node)\
                         or ""
            except Exception:
                # Fallback: slice from lineno..end_lineno
                start    = node.lineno - 1
                node_src = lines[start].rstrip("\n")
            if not node_src: continue

            col = (getattr(node, "col_offset", 0) + 1) if \
                   hasattr(node, "col_offset") else 1
            if len(node_src) > utils.LINE_LEN:
                results.append({
                    "file": file,
                    "line": node.lineno,
                    "col": col,
                    "code": "Z201",
                    "msg": "overly compact block exceeds "
                           "line length; consider splitting"
                })

    for i, raw in enumerate(lines):
        if _is_comment_or_empty(raw): continue
        # Only consider physically single lines (they already
        # are, since iterating lines)
        if ";" not in raw: continue
        # Quick length check first to avoid repeated parsing
        if len(raw) <= utils.LINE_LEN: continue
        # Try AST parse to verify this line is truly multiple
        # statements
        if _is_semicolon_compound(raw):
            results.append({
                "file": file,
                "line": i + 1,
                "col": 1,
                "code": "Z201",
                "msg": "overly compact block exceeds line "
                       "length; consider splitting"
            })

    return results
