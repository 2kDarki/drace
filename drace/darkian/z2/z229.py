import ast

from drace.types import Context, Dict

from ._common import iter_function_defs


MAX_RETURN_SHAPES = 3


def _shape(node: ast.AST | None) -> str:
    if node is None:
        return "NoneType"
    if isinstance(node, ast.Constant):
        if node.value is None:
            return "NoneType"
        return type(node.value).__name__
    return type(node).__name__


def check_z229(context: Context) -> list[Dict]:
    """
    Z229: flag functions with highly variable return shapes.
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []

    for node in iter_function_defs(tree):
        returns = [ret for ret in ast.walk(node) if isinstance(ret, ast.Return)]
        types_seen: set[str] = set()

        for ret in returns:
            types_seen.add(_shape(ret.value))

        if len(types_seen) > MAX_RETURN_SHAPES:
            results.append({
                "file": file,
                "line": node.lineno,
                "col": 1,
                "code": "Z229",
                "msg": "function has multiple return types; consider consistent API",
            })

    return results
