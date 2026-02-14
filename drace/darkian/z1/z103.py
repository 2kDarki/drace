import ast

from drace.types import Context, Fix


def _bound_name(alias: ast.alias) -> str:
    if alias.asname:
        return alias.asname
    return alias.name.split(".", 1)[0]


def _render_alias(alias: ast.alias) -> str:
    if alias.asname:
        return f"{alias.name} as {alias.asname}"
    return alias.name


def _render_import(node: ast.Import, aliases: list[ast.alias]) -> str:
    indent = " " * int(getattr(node, "col_offset", 0))
    joined = ", ".join(_render_alias(alias) for alias in aliases)
    return f"{indent}import {joined}"


def _render_from_import(node: ast.ImportFrom, aliases: list[ast.alias]) -> str:
    indent = " " * int(getattr(node, "col_offset", 0))
    level = "." * int(getattr(node, "level", 0))
    module = node.module or ""
    joined = ", ".join(_render_alias(alias) for alias in aliases)
    return f"{indent}from {level}{module} import {joined}"


def _used_names(tree: ast.Module) -> set[str]:
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
    return used


def fixes_z103(context: Context) -> list[Fix]:
    """
    Remove unused import aliases for single-line import statements.
    """
    tree = context["tree"]
    fixes: list[Fix] = []
    used = _used_names(tree)

    for node in getattr(tree, "body", []):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            continue
        if node.lineno != node.end_lineno:
            continue

        aliases = list(getattr(node, "names", []))
        if not aliases:
            continue
        if any(alias.name == "*" for alias in aliases):
            continue

        kept = [alias for alias in aliases if _bound_name(alias) in used]
        if len(kept) == len(aliases):
            continue

        line = int(node.lineno)
        if not kept:
            fixes.append({"op": "replace_line", "line": line, "content": ""})
            continue

        if isinstance(node, ast.Import):
            content = _render_import(node, kept)
        else:
            content = _render_from_import(node, kept)
        fixes.append({"op": "replace_line", "line": line, "content": content})

    return fixes
