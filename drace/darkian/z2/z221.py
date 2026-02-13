import ast

from drace.types import Context, Dict
from drace.constants import MAX_STEPS

from ._common import iter_function_defs


def _is_guard_if(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    if node.orelse or len(node.body) != 1:
        return False
    return isinstance(node.body[0], (ast.Return, ast.Raise, ast.Continue, ast.Break))


def check_z221(context: Context) -> list[Dict]:
    """
    Z221: flag functions with too many top-level structural steps.
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []

    composite_blocks = (
        ast.If,
        ast.For,
        ast.While,
        ast.Try,
        ast.With,
        ast.Match,
        ast.AsyncFor,
        ast.AsyncWith,
    )

    for func in iter_function_defs(tree):
        top_blocks = []
        for node in func.body:
            if not isinstance(node, composite_blocks):
                continue
            if _is_guard_if(node):
                continue
            top_blocks.append(node)
        steps = len(top_blocks)
        if steps > MAX_STEPS:
            results.append({
                "file": file,
                "line": func.lineno,
                "col": 1,
                "code": "Z221",
                "msg": (
                    f"function has {steps} top-level steps; review for possible "
                    "decomposition if clarity or cohesion is affected"
                ),
            })

    return results
