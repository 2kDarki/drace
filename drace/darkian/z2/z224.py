from drace.types import Context, Dict

from ._common import iter_function_defs


MAX_PARAMS = 6


def _param_count(node) -> int:
    args = node.args
    count = len(args.posonlyargs) + len(args.args) + len(args.kwonlyargs)
    if args.vararg:
        count += 1
    if args.kwarg:
        count += 1
    return count


def check_z224(context: Context) -> list[Dict]:
    """
    Z224: flag functions with too many parameters.
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []

    for func in iter_function_defs(tree):
        params = _param_count(func)
        if params > MAX_PARAMS:
            results.append({
                "file": file,
                "line": func.lineno,
                "col": 1,
                "code": "Z224",
                "msg": (
                    f"function has {params} parameters; consider grouping "
                    "or refactoring"
                ),
            })

    return results
