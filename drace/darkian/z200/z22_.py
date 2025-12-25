import builtins
import ast

from drace import utils

# =================== Z220 to Z229 Draft ====================

BUILTINS = set(dir(builtins))

# Helper utilities

def _get_assignments(node):
    return [n for n in ast.walk(node) if isinstance(n, (ast.Assign, ast.AnnAssign))]

def _get_function_defs(node):

    return [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]

def _hash_node(node: ast.AST) -> str:
    """Return a normalized string representation for repeated logic detection."""

    name_map     = {}
    name_counter = [0]

    def _normalize_name(name):
        if name not in name_map:
            name_map[name] = f"var{name_counter[0]}"
            name_counter[0] += 1
        return name_map[name]

    def _clone(n):
        if isinstance(n, ast.AST):
            new_node = n.__class__()
            for field, value in ast.iter_fields(n):
                if field in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset'):
                    continue
                if isinstance(value, ast.AST) or isinstance(value, list):
                    setattr(new_node, field, _clone(value))
                elif isinstance(value, str):
                    setattr(new_node, field, "_str")
                elif isinstance(value, (int, float, bool)):
                    setattr(new_node, field, "_const")
                elif isinstance(value, ast.AST):
                    setattr(new_node, field, _clone(value))
                else:
                    setattr(new_node, field, value)

            if isinstance(n, ast.Name):
                new_node.id = _normalize_name(n.id)

            return new_node
        elif isinstance(n, list):
            return [_clone(x) for x in n]
        else:
            return n

    cleaned = _clone(node)
    return ast.dump(cleaned, annotate_fields=False, include_attributes=False)


# --------------- Z221: Orthogonal Functions ----------------
def Z221_check(tree, file: str) -> list[dict]:
    results = []

    composite_blocks = (ast.If, ast.For, ast.While, ast.Try, 
                        ast.With, ast.Match)
    for func in _get_function_defs(tree):
        top_blocks = [n for n in func.body if isinstance(
                      n, composite_blocks)]
        steps      = len(top_blocks)
        if steps > utils.MAX_STEPS:
            message = f"function has {steps} top-level " \
                    + "steps review for possible " \
                    + "decomposition if clarity or cohesion"\
                    + " is affected"
            results.append({
                'file': file,
                'line': func.lineno,
                'col': 1,
                'code': 'Z221',
                'msg': message
            })
    return results


# ---------------- Z222: Tight Coupling ----------------
def Z222_check(tree, file: str) -> list[dict]:
    results = []

    for func in _get_function_defs(tree):
        local_vars = {n.id for n in ast.walk(func) if 
                     isinstance(n, ast.Name) and
                     isinstance(getattr(n, 'ctx', None),
                     ast.Store)}
        ignored    = BUILTINS | local_vars | {arg.arg for arg
                     in func.args.args}
        external_objects = set()
        for node in ast.walk(func):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                name = node.value.id
                if name not in ignored:
                    external_objects.add(name)

        if len(external_objects) > utils.MAX_COUPLING:
            results.append({
                'file': file,
                'line': func.lineno,
                'col': 1,
                'code': 'Z222',
                'msg': f'function uses {len(external_objects)} external objects; may be tightly coupled'
            })

    return results


# -------------- Z223: Implicit State Mutation --------------
def Z223_check(tree, file: str) -> list[dict]:
    results = []

    for func in _get_function_defs(tree):
        for node in ast.walk(func):
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Attribute):
                attr = node.targets[0]
                if isinstance(attr.value, ast.Name) and attr.value.id not in {arg.arg for arg in func.args.args} | {'self'}:
                    results.append({
                        'file': file,
                        'line': node.lineno,
                        'col': 1,
                        'code': 'Z223',
                        'msg': 'assignment mutates external state implicitly; make explicit'
                    })
    return results


# ---------------- Z224: Parameter Explosion ----------------
def Z224_check(tree, file: str) -> list[dict]:
    results = []

    for func in _get_function_defs(tree):
        if len(func.args.args) > 6:
            results.append({
                'file': file,
                'line': func.lineno,
                'col': 1,
                'code': 'Z224',
                'msg': f'function has {len(func.args.args)} parameters; consider grouping or refactoring'
            })
    return results


# ------------ Z225: Overloaded Data Structures -------------
def Z225_check(tree, file: str) -> list[dict]:
    results = []

    for node in ast.walk(tree):
        # --- Skip dicts used in .items() pattern ---
        if isinstance(node, ast.Dict) and len(node.keys) > 5:
            parent = getattr(node, 'parent', None)
            if isinstance(parent, ast.Call) and isinstance(
                    parent.func, ast.Attribute):
                if parent.func.attr == 'items': continue

            results.append({
                'file': file,
                'line': node.lineno,
                'col': 1,
                'code': 'Z225',
                'msg': 'dict has too many keys; consider splitting responsibilities'
            })

        elif isinstance(node, ast.ClassDef):
            public_attrs = [
                n.targets[0].id for n in node.body
                if isinstance(n, ast.Assign)
                and isinstance(n.targets[0], ast.Name)
            ]
            if len(public_attrs) > 5:
                results.append({
                    'file': file,
                    'line': node.lineno,
                    'col': 1,
                    'code': 'Z225',
                    'msg': 'class has many public attributes; consider SRP'
                })

    return results


# ---------------- Z226: Temporal Coupling ----------------
def Z226_check(lines: list[str], file: str) -> list[dict]:
    # Simplified heuristic: look for consecutive assigns to same variable across lines
    results = []
    last_assigned = {}
    for i, line in enumerate(lines):
        tree = utils.tolerant_parse_module(line)
        if not tree.body: continue
        node = tree.body[0]
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            var = node.targets[0].id
            if var in last_assigned and i - last_assigned[var] <= 2:
                results.append({
                    'file': file,
                    'line': i + 1,
                    'col': 1,
                    'code': 'Z226',
                    'msg': f'variable {var} assigned in temporal sequence; possible temporal coupling'
                })
            last_assigned[var] = i
    return results


# ---------------- Z228: Abstraction Leak ----------------
def Z228_check(tree, file: str) -> list[dict]:
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Return):
            if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                results.append({
                    'file': file,
                    'line': node.lineno,
                    'col': 1,
                    'code': 'Z228',
                    'msg': 'returning internal data structure; consider interface or copy'
                })
    return results


# --------------- Z229: Unstable API Patterns ---------------
def Z229_check(tree, file: str) -> list[dict]:
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
            types_seen = set()
            for r in returns:
                if hasattr(r.value, '__class__'):
                    types_seen.add(type(r.value).__name__)
            if len(types_seen) > 3:
                results.append({
                    'file': file,
                    'line': node.lineno,
                    'col': 1,
                    'code': 'Z229',
                    'msg': 'function has multiple return types; consider consistent API'
                })
    return results

# ------------------------ Run Checks -----------------------
def check(lines: list[str], tree, file: str) -> list[dict]:
    rules = [Z221_check, Z222_check, Z223_check, Z224_check,
             Z225_check, Z228_check, Z229_check]

    results = []
    for rule in rules:
        results.extend(rule(tree, file))

    results.extend(Z226_check(lines, file))

    return results
