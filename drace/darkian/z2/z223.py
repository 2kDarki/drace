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


def _collect_locals(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[set[str], set[str]]:
    locals_: set[str] = set()
    declared_global: set[str] = set()
    args = func.args

    for arg in args.posonlyargs + args.args + args.kwonlyargs:
        locals_.add(arg.arg)
    if args.vararg:
        locals_.add(args.vararg.arg)
    if args.kwarg:
        locals_.add(args.kwarg.arg)

    for node in ast.walk(func):
        if isinstance(node, ast.Global):
            declared_global |= set(node.names)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if hasattr(node, "targets") else [node.target]
            for target in targets:
                locals_ |= _extract_names(target)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            locals_ |= _extract_names(node.target)
        elif isinstance(node, ast.comprehension):
            locals_ |= _extract_names(node.target)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            locals_.add(node.name)
    return locals_, declared_global


def _root_name(target: ast.AST) -> str | None:
    node = target
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def _iter_mutation_targets(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.Assign):
        return list(node.targets)
    if isinstance(node, ast.AnnAssign):
        return [node.target]
    if isinstance(node, ast.AugAssign):
        return [node.target]
    return []


def _iter_scope_nodes(func: ast.FunctionDef | ast.AsyncFunctionDef):
    def walk(node: ast.AST):
        if node is not func and isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        yield node
        for child in ast.iter_child_nodes(node):
            yield from walk(child)

    yield from walk(func)


def check_z223(context: Context) -> list[Dict]:
    """
    Z223: flag implicit mutation of external state.
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []

    for func in iter_function_defs(tree):
        local_names, forced_external = _collect_locals(func)
        allowed_roots = local_names | {"self", "cls"}

        for node in _iter_scope_nodes(func):
            targets = _iter_mutation_targets(node)
            for target in targets:
                if isinstance(target, ast.Name) and target.id in forced_external:
                    results.append({
                        "file": file,
                        "line": node.lineno,
                        "col": getattr(node, "col_offset", 0) + 1,
                        "code": "Z223",
                            "msg": (
                            f"assignment mutates external name '{target.id}' "
                            "implicitly; make dependency explicit"
                        ),
                    })
                    continue

                if not isinstance(target, (ast.Attribute, ast.Subscript)):
                    continue

                root = _root_name(target)
                if root is None or root in allowed_roots:
                    continue

                results.append({
                    "file": file,
                    "line": node.lineno,
                    "col": getattr(node, "col_offset", 0) + 1,
                    "code": "Z223",
                    "msg": (
                        "assignment mutates external state implicitly; "
                        "make explicit"
                    ),
                })

    return results
