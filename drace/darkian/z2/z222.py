import builtins
import ast

from drace.constants import MAX_COUPLING
from drace.types import Context, Dict

from ._common import iter_function_defs


BUILTINS = set(dir(builtins))


def _extract_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts:
            names |= _extract_names(elt)
    return names


def _collect_locals(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    locals_: set[str] = set()
    args = func.args
    for arg in args.posonlyargs + args.args + args.kwonlyargs:
        locals_.add(arg.arg)
    if args.vararg:
        locals_.add(args.vararg.arg)
    if args.kwarg:
        locals_.add(args.kwarg.arg)

    for node in ast.walk(func):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if hasattr(node, "targets") else [node.target]
            for target in targets:
                locals_ |= _extract_names(target)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            locals_ |= _extract_names(node.target)
        elif isinstance(node, ast.comprehension):
            locals_ |= _extract_names(node.target)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            locals_.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            locals_.add(node.name)
    return locals_


def _collect_module_defined_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".", 1)[0])
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if hasattr(node, "targets") else [node.target]
            for target in targets:
                names |= _extract_names(target)
    return names


def _collect_enclosing_locals(node: ast.AST) -> set[str]:
    names: set[str] = set()
    cur = getattr(node, "parent", None)
    while cur and not isinstance(cur, ast.Module):
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names |= _collect_locals(cur)
        cur = getattr(cur, "parent", None)
    return names


def _iter_used_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    used: set[str] = set()

    def walk(node: ast.AST) -> None:
        if node is not func and isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
        for child in ast.iter_child_nodes(node):
            walk(child)

    walk(func)
    return used


def check_z222(context: Context) -> list[Dict]:
    """
    Z222: flag functions that use many external objects (high coupling pressure).
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []
    module_defined = _collect_module_defined_names(tree)

    for func in iter_function_defs(tree):
        local_vars = _collect_locals(func)
        enclosing_locals = _collect_enclosing_locals(func)
        external_objects = {
            name for name in _iter_used_names(func)
            if (
                name not in local_vars
                and name not in enclosing_locals
                and name not in module_defined
                and name not in BUILTINS
            )
        }

        if len(external_objects) > MAX_COUPLING:
            results.append({
                "file": file,
                "line": func.lineno,
                "col": 1,
                "code": "Z222",
                "msg": (
                    f"function uses {len(external_objects)} external objects; "
                    "may be tightly coupled"
                ),
            })

    return results
