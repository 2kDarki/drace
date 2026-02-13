import ast


def iter_function_defs(tree: ast.AST) -> list[ast.AST]:
    """Collect function definitions from a syntax tree."""
    return [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
