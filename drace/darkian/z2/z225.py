import ast

from drace.types import Context, Dict


MAX_DICT_KEYS = 5
MAX_PUBLIC_ATTRS = 5


def _is_schema_like_dict(node: ast.Dict) -> bool:
    """
    Ignore declarative schemas (e.g., config maps with type/default tuples).
    """
    if not node.keys or not node.values:
        return False

    for key, value in zip(node.keys, node.values):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            return False
        if not isinstance(value, (ast.Tuple, ast.List)) or len(value.elts) != 2:
            return False
    return True


def check_z225(context: Context) -> list[Dict]:
    """
    Z225: flag overloaded data structures.
    Targets large dicts or classes with many public attrs.
    """
    tree = context["tree"]
    file = context["file"]
    results: list[Dict] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict) and len(node.keys) > MAX_DICT_KEYS:
            parent = getattr(node, "parent", None)
            if (
                isinstance(parent, ast.Call)
                and isinstance(parent.func, ast.Attribute)
                and parent.func.attr == "items"
            ):
                continue
            if _is_schema_like_dict(node):
                continue

            results.append({
                "file": file,
                "line": node.lineno,
                "col": 1,
                "code": "Z225",
                "msg": "dict has too many keys; consider splitting responsibilities",
            })
            continue

        if isinstance(node, ast.ClassDef):
            public_attrs: list[str] = []
            for sub in node.body:
                if (
                    isinstance(sub, ast.Assign)
                    and sub.targets
                    and isinstance(sub.targets[0], ast.Name)
                ):
                    public_attrs.append(sub.targets[0].id)
                elif (
                    isinstance(sub, ast.AnnAssign)
                    and isinstance(sub.target, ast.Name)
                ):
                    public_attrs.append(sub.target.id)
            if len(public_attrs) > MAX_PUBLIC_ATTRS:
                results.append({
                    "file": file,
                    "line": node.lineno,
                    "col": 1,
                    "code": "Z225",
                    "msg": "class has many public attributes; consider SRP",
                })

    return results
