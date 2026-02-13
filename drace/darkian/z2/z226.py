import ast

from drace.types import Context, Dict


WINDOW = 2
MIN_REPEATS = 2


def _references_name(node: ast.AST | None, name: str) -> bool:
    if node is None:
        return False
    return any(
        isinstance(sub, ast.Name)
        and isinstance(sub.ctx, ast.Load)
        and sub.id == name
        for sub in ast.walk(node)
    )


def _assign_target_name(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    if (
        isinstance(node, ast.Assign)
        and node.targets
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0].id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    return None, None


def _scan_body(body: list[ast.stmt], file: str) -> list[Dict]:
    results: list[Dict] = []
    last_seen: dict[str, int] = {}
    repeats: dict[str, int] = {}

    for idx, stmt in enumerate(body):
        name, value = _assign_target_name(stmt)
        if name is not None:
            if _references_name(value, name):
                last_seen[name] = idx
                continue

            if name in last_seen and idx - last_seen[name] <= WINDOW:
                repeats[name] = repeats.get(name, 0) + 1
                if repeats[name] == MIN_REPEATS:
                    results.append({
                        "file": file,
                        "line": stmt.lineno,
                        "col": getattr(stmt, "col_offset", 0) + 1,
                        "code": "Z226",
                        "msg": (
                            f"variable {name} reassigned repeatedly in a short "
                            "sequence; possible temporal coupling"
                        ),
                    })
            else:
                repeats[name] = 0
            last_seen[name] = idx

    return results


def check_z226(context: Context) -> list[Dict]:
    """
    Z226: flag assignment sequences that depend on temporal proximity.
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []

    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (
            isinstance(body, list)
            and body
            and all(isinstance(item, ast.stmt) for item in body)
        ):
            results.extend(_scan_body(body, file))

    return results
