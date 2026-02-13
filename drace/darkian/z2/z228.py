import ast

from drace.types import Context, Dict

from ._common import iter_function_defs


def _extract_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts:
            names |= _extract_names(elt)
    return names


def _is_mutable_literal(node: ast.AST | None) -> bool:
    return isinstance(node, (ast.List, ast.Dict, ast.Set))


def _is_mutable_ctor(node: ast.AST | None) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "dict", "set", "defaultdict"}
    )


def _collect_module_mutables(tree: ast.Module) -> set[str]:
    mutables: set[str] = set()
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and (_is_mutable_literal(node.value) or _is_mutable_ctor(node.value))
        ):
            for target in node.targets:
                mutables |= _extract_names(target)
        elif isinstance(node, ast.AnnAssign) and (
            _is_mutable_literal(node.value) or _is_mutable_ctor(node.value)
        ):
            mutables |= _extract_names(node.target)
    return mutables


def _collect_declared_globals(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Global):
            names |= set(node.names)
    return names


def _root_name(node: ast.AST) -> str | None:
    cur = node
    while isinstance(cur, (ast.Attribute, ast.Subscript)):
        cur = cur.value
    if isinstance(cur, ast.Name):
        return cur.id
    return None


def _is_state_leak(
    ret: ast.Return,
    declared_globals: set[str],
    module_mutables: set[str],
) -> bool:
    value = ret.value
    if value is None:
        return False

    if isinstance(value, ast.Attribute):
        return isinstance(value.value, ast.Name) and value.value.id in {"self", "cls"}

    if isinstance(value, ast.Subscript):
        root = _root_name(value)
        if root in {"self", "cls"}:
            return True
        return root in declared_globals and root in module_mutables

    if isinstance(value, ast.Name):
        return value.id in declared_globals and value.id in module_mutables

    return False


def check_z228(context: Context) -> list[Dict]:
    """
    Z228: flag leaking internal mutable state through API returns.
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []
    module_mutables = _collect_module_mutables(tree)

    for func in iter_function_defs(tree):
        declared_globals = _collect_declared_globals(func)
        for node in ast.walk(func):
            if not isinstance(node, ast.Return):
                continue
            if not _is_state_leak(node, declared_globals, module_mutables):
                continue
            results.append({
                "file": file,
                "line": node.lineno,
                "col": getattr(node, "col_offset", 0) + 1,
                "code": "Z228",
                "msg": "returning mutable internal state; consider copy or interface",
            })

    return results
