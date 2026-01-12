# ======================== STANDARDS ========================
import hashlib
import math
import ast

# ========================== LOCALS =========================
from drace.types import Context, Dict
from drace import utils


class Canonicalizer(ast.NodeTransformer):
    """
    Canonicalize AST blocks while preserving *semantic shape*.
    Separate namespaces for vars / args / attrs.
    Constants are bucketed by kind, not value.
    """

    def __init__(self):
        super().__init__()
        self.var_map  = {}
        self.arg_map  = {}
        self.attr_map = {}

        self._v  = 0
        self._a  = 0
        self._at = 0

    def _map(self, name: str, space: dict, pfx: str) -> str:
        if name not in space:
            space[name] = f"{pfx}{len(space)}"
        return space[name]

    # Identifiers
    def visit_Name(self, node: ast.Name):
        """Keep ctx type (Load/Store) but replace id."""
        new_id = self._map(node.id, self.var_map, "_V")
        return ast.copy_location(ast.Name(id=new_id,
               ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg):
        new_arg = self._map(node.arg, self.arg_map, "_A")
        return ast.copy_location(ast.arg(arg=new_arg,
               annotation=None, type_comment=None), node)

    def visit_Attribute(self, node: ast.Attribute):
        """
        Replace attribute name with placeholder but keep the
        structure (obj.attr -> obj._A0) and map attr name as
        if it were a name (but distinct space)
        """
        node     = self.generic_visit(node)
        new_attr = self._map(node.attr, self.attr_map, "_AT")
        return ast.copy_location(ast.Attribute(
               value=node.value, attr=new_attr,
               ctx=node.ctx), node)

    def visit_Constant(self, node: ast.Constant):
        # Replace with placeholder constant name (string) so
        # ast.dump becomes deterministic
        val = node.value
        if val is None: kind = "NONE"
        elif isinstance(val, str): kind = "STR"
        elif isinstance(val, int): kind = "INT"
        elif isinstance(val, bool): kind = "BOOL"
        elif isinstance(val, float): kind = "FLOAT"
        else: kind = "CONST"

        # Represent placeholder as a NameConstant-like node
        # to avoid mixing types
        return ast.copy_location(ast.Constant(value=kind),
               node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # normalize function name to single token (we don't
        # want to treat different function names as different
        # blocks)
        node      = self.generic_visit(node)
        node.name = "_FN"

        # drop decorators and annotations (they can leak
        # external names)
        node.decorator_list = ["_DEC"]
        node.returns        = None
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        node                = self.generic_visit(node)
        node.name           = "_CLS"
        node.bases          = ["_BASE"] * len(node.bases)
        node.decorator_list = ["_DEC"] \
                           if node.decorator_list else []
        return node


def canonical_block_dump(stmts: list[ast.stmt]) -> str:
    """
    Given a list of statement AST nodes, produce a canonical
    string representation.
    """
    canon = Canonicalizer()
    # Create a synthetic Module containing the stmts to
    # maintain context
    module = ast.Module(body=stmts, type_ignores=[])
    module = canon.visit(module)
    ast.fix_missing_locations(module)

    # Use ast.dump with sorted/consistent fields
    dumped = ast.dump(module, annotate_fields=False,
             include_attributes=False)

    # Hash it for compactness
    hashed = hashlib.sha256(dumped.encode()).hexdigest()
    return hashed, dumped


def _is_trivial_by_line_ranges(matches: list[tuple[int, int]]
                             ) -> bool:
    """
    Check if matched blocks are trivially sequential (e.g.
    multiple 1-line dumps in a row)

    Examples:
      - [(36, 37), (37, 38), (38, 39)] -> True
      - [(36, 38), (37, 39), (38, 40)] -> True
      - [(36, 37), (38, 39), (40, 41)] -> True
    """
    if len(matches) < 2: return False

    matches = sorted(matches)
    for i, (start, end) in enumerate(matches):
        if end - start == 1: return True
        try:
            if matches[i + 1][0] in range(start, end + 1):
                return True
        except IndexError: pass

    return False


def _is_argparse_like(dumped: str) -> bool:
    # A very rough structural match
    return dumped.count("Call(Attribute(Name(") >= 2 and \
           utils.any_in("keyword(", "Constant(", eq=dumped)


def is_trivial_dump(dumped: str,
                    ranges: list[tuple[int, int]]) -> bool:
    """Heuristic to ignore trivial blocks"""
    if len(dumped) < 50: return True
    if _is_argparse_like(dumped): return True
    if _is_trivial_by_line_ranges(ranges): return True
    return False


def has_control_flow(stmts):
    control_nodes = (ast.While, ast.For, ast.If, ast.With,
                     ast.Match, ast.Try)
    return any(isinstance(s, control_nodes) for s in stmts)


def score_candidate(count: int, length: int) -> int:
    return count * math.log(length + 1)


def collect_sequences(tree: ast.AST, min_len: int = 2,
                      max_len: int = 6) -> dict[str,
                      list[tuple[int, int, str]]]:
    """
    Walk the tree and collect contiguous sequences of
    statements from bodies.

    Returns mapping: hash -> list of (start_lineno,
                     end_lineno, dumped)
    """
    sequences = {}

    # Helper to walk every body (list of statements) in
    # relevant nodes
    class BodyWalker(ast.NodeVisitor):
        def _walk_and_visit(self, node, orelse: bool):
            self._walk_body(node.body)
            if orelse: self._walk_body(node.orelse)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef):
            self._walk_and_visit(node, orelse=False)

        def visit_If(self, node: ast.If):
            self._walk_and_visit(node, orelse=True)

        def visit_For(self, node: ast.For):
            self._walk_and_visit(node, orelse=True)

        def visit_While(self, node: ast.While):
            self._walk_and_visit(node, orelse=True)

        def visit_With(self, node: ast.With):
            self._walk_and_visit(node, orelse=False)

        def visit_Try(self, node: ast.Try):
            self._walk_body(node.body)
            self._walk_body(node.orelse)
            self._walk_body(node.finalbody)
            for h in node.handlers: self._walk_body(h.body)
            self.generic_visit(node)

        def visit_Module(self, node: ast.Module):
            self._walk_and_visit(node, orelse=False)

        def _walk_body(self, stmts: list[ast.stmt]):
            # Convert list of stmts into sliding windows of
            # sizes max_len..min_len (longer first)
            n = len(stmts)
            # Build linear list of lineno for bounds
            for length in range(max_len, min_len - 1, -1):
                if n < length: continue
                for i in range(0, n - length + 1):
                    block = stmts[i:i + length]

                    if not hasattr(block[0], "lineno"):
                        continue
                    if not has_control_flow(block): continue

                    h, dumped = canonical_block_dump(block)
                    start     = block[0].lineno
                    end       = getattr(block[-1],
                                "end_lineno",
                                block[-1].lineno)
                    sequences.setdefault(h, []).append((
                        start, end, dumped))

    BodyWalker().visit(tree)
    return sequences


def check_z202(context: Context) -> list[Dict]:
    """
    Z202: find repeated sequences of statements and suggest
          abstraction

    Returns list of issues; each issue contains occurrences
    and a short message
    """
    tree    = context["tree"]
    file    = context["file"]
    seqs    = collect_sequences(tree)
    results = []
    limit   = 8

    # seqs: mapping h -> list[(start, end, dumped)]
    # Build candidate meta list
    candidates = []
    for h, occ in seqs.items():
        # Collapse duplicates that start at same line (keep
        # earliest end)
        seen = {}
        for start, end, dumped in occ:
            key       = (start, end)
            seen[key] = dumped
        occ_unique = [(s, e, seen[(s, e)]) for s, e in seen]
        if len(occ_unique) < 3: continue

        # Prefer non-trivial blocks
        line_ranges   = [(s, e) for s, e, _ in occ_unique]
        _, _, dumped0 = occ_unique[0]
        if is_trivial_dump(dumped0, line_ranges): continue

        # Candidate metadata
        first_start = min(s for s, e, d in occ_unique)
        first_end   = max(e for s, e, d in occ_unique)

        # Length in lines (used for sorting preference)
        length = first_end - first_start + 1
        count  = len(occ_unique)
        candidates.append({
            "hash": h,
            "occurrences": occ_unique,
            "count": count,
            "length": length,
            "score": score_candidate(count, length),
        })

    if not candidates: return []

    # Sort by score
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Greedy select non-overlapping candidates
    selected = []
    occupied = set()

    def range_overlaps_with_occupied(start, end):
        # O(length) check; fine for typical blocks
        for ln in range(start, end + 1):
            if ln in occupied: return True
        return False

    for cand in candidates:
        # Build list of unique (start, end) occurrences for
        # this candidate
        occs = sorted({(s, e) for s, e, d in
               cand["occurrences"]}, key=lambda t: t[0])

        # If all occurrences would overlap existing
        # selections, skip candidate
        non_overlapping_occs = [(s, e) for s, e in occs
                        if not range_overlaps_with_occupied(
                               s, e)]
        if len(non_overlapping_occs) < 2: continue

        # Select this candidate: mark its first
        # non-overlapping occurrence as primary
        primary_start, primary_end = non_overlapping_occs[0]

        # Mark all selected occurrences' lines as occupied to
        # prevent downstream overlaps
        for s, e in non_overlapping_occs:
            for ln in range(s, e + 1): occupied.add(ln)
        selected.append({
            "hash": cand["hash"],
            "primary": (primary_start, primary_end),
            "matches": non_overlapping_occs,
            "count": len(non_overlapping_occs),
            "length": cand["length"],
        })

    # Build results from selected candidates
    results = []
    for s in selected:
        start, _ = s["primary"]
        matches  = s["matches"]

        severity = "HIGH" \
                if s["count"] >= 6 and s["length"] >= 5 \
              else "MEDIUM" if s["count"] >= 4 \
              else "LOW"

        confidence = min(1.0, s["count"] / 6
                   + s["length"] / 10) * 100

        # Build readable match summary; limit shows to first
        # 8 to avoid huge messages
        message = f"repeated block detected ({s['count']} " \
                + f"occurrences, severity={severity}, " \
                + f"confidence={confidence:.2f}%). Consider"\
                +  " extracting a function for the block at"\
                + f" lines {matches[:limit]}"

        if len(matches) > limit:
            message += f" (and {len(matches) - limit} more" \
                     +  " occurrences)"
        results.append({
            "file": file,
            "line": start,
            "col": 1,
            "code": "Z202",
            "msg": message,
        })

    return results
