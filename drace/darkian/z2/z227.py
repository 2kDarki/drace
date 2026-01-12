import builtins
import ast

from drace.types import Context, Dict


def _is_not_synthetic_name(name: str) -> bool:
    if any(name.startswith(p) for p in ["_V", "_A"]):
        try: int(name[2]); return False
        except ValueError: pass

    return True


def iter_used_names(node: ast.AST) -> set[str]:
    used: set[str] = set()

    def visit(n: ast.AST):
        # Stop at nested scopes
        if n is not node and isinstance(n,
            (ast.FunctionDef, ast.AsyncFunctionDef,
            ast.ClassDef, ast.Lambda)): return

        if isinstance(n, ast.Name) and isinstance(n.ctx,
                ast.Load):
            if _is_not_synthetic_name(n.id): used.add(n.id)

        for child in ast.iter_child_nodes(n): visit(child)

    visit(node)
    return used


def get_enclosing_locals(node: ast.AST) -> set[str]:
    """
    Collect names visible from enclosing *non-module* scopes.
    Module scope is handled explicitly elsewhere.
    """
    visible = set()
    cur     = node.parent

    while cur and not isinstance(cur, ast.Module):
        # -------- Function / AsyncFunction scope --------
        if isinstance(cur, (ast.FunctionDef,
                ast.AsyncFunctionDef)):
            # Parameters
            for arg in cur.args.args + cur.args.kwonlyargs:
                visible.add(arg.arg)
            if cur.args.vararg:
                visible.add(cur.args.vararg.arg)
            if cur.args.kwarg:
                visible.add(cur.args.kwarg.arg)

            # Local assignments
            for sub in cur.body:
                if isinstance(sub, (ast.Assign,
                        ast.AnnAssign)):
                    targets = sub.targets if hasattr(sub,
                              "targets") else [sub.target]
                    for t in targets:
                        visible |= extract_names(t)

                elif isinstance(sub, (ast.For,
                        ast.AsyncFor)):
                    visible |= extract_names(sub.target)

                elif isinstance(sub, ast.ExceptHandler) \
                    and sub.name: visible.add(sub.name)

                elif isinstance(sub, (ast.FunctionDef,
                        ast.AsyncFunctionDef, ast.ClassDef)):
                    visible.add(sub.name)

        # -------- Class scope --------
        elif isinstance(cur, ast.ClassDef):
            # Only the class name is visible to inner scopes
            visible.add(cur.name)

        # Move upward
        cur = cur.parent

    return visible


def extract_names(node):
    """
    Recursively extract name identifiers from ast targets
    (for assignment, tuple unpacking, etc).
    """
    names: set[str] = set()
    if isinstance(node, ast.Name): names.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts: names |= extract_names(elt)
    return names


def get_targets(node: ast.AST) -> list:
    return node.targets \
        if hasattr(node, "targets") \
      else [node.target]


def check_z227(context: Context) -> list[Dict]:
    """
    Z227: Detect hidden dependencies in functions and nested
          functions.

    Hidden dependency: a name used in a function that is not:
      - a parameter or local variable (or nested def/class),
      - an imported name,
      - a built-in,
      - a module-level constant (ALL_CAPS assigned at top
        level).

    Globals (non-constant) and other external names will be
    flagged.
    """
    tree    = context["tree"]
    file    = context["file"]
    results = []

    builtin_names: set[str] = set(dir(builtins))

    # 1. Collect imported names (module‑level)
    imported_names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imported_names.add(alias.asname or
                    alias.name.split(".")[0])

    # 2. Collect module‑level variable names → identify
    #    constants
    module_globals:   set[str] = set()
    module_constants: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = get_targets(node)
            for t in targets:
                if isinstance(t, ast.Name):
                    module_globals.add(t.id)
                    if t.id.isupper():
                        module_constants.add(t.id)
                elif isinstance(t, (ast.Tuple, ast.List)):
                    for elt in t.elts:
                        if isinstance(elt, ast.Name):
                            module_globals.add(elt.id)
                            if elt.id.isupper():
                                module_constants.add(elt.id)
        elif isinstance(node, (ast.FunctionDef,
                ast.AsyncFunctionDef, ast.ClassDef)):
            module_globals.add(node.name)

    # 3. Walk through all functions and check for hidden deps
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef,
                ast.AsyncFunctionDef, ast.Lambda)):
            if isinstance(node.parent, ast.Module): continue
            # Collect used names inside this function
            used_names = iter_used_names(node)

            # Collect locals: arguments, names assigned
            # within the function body, names of nested
            # defs/classes
            local_vars: set[str] = set()
            args = node.args
            for arg in list(args.args) + list(
                args.kwonlyargs): local_vars.add(arg.arg)
            if args.vararg: local_vars.add(args.vararg.arg)
            if args.kwarg: local_vars.add(args.kwarg.arg)
            for sub in ast.iter_child_nodes(node):
                if isinstance(sub, (ast.FunctionDef,
                        ast.AsyncFunctionDef, ast.ClassDef,
                        ast.Lambda)):
                    local_vars.add(sub.name if hasattr(sub,
                        "name") else "<lambda>")
            # Also treat names assigned inside as locals
            for sub in ast.walk(node):
                if isinstance(sub, (ast.Assign,
                        ast.AnnAssign)):
                    targets = get_targets(sub)
                    for t in targets:
                        local_vars |= extract_names(t)
                elif isinstance(sub, (ast.For,
                        ast.comprehension)):
                    target = getattr(sub, "target", None)
                    if target is not None:
                        local_vars |= extract_names(target)
                elif isinstance(sub, ast.ExceptHandler
                    ) and sub.name: local_vars.add(sub.name)

            # Determine visible names from enclosing
            # (non-module) scopes
            visible_from_enclosing = get_enclosing_locals(
                                     node)

            # Now compute hidden dependencies
            hidden = used_names - local_vars \
                   - visible_from_enclosing - builtin_names \
                   - imported_names - module_constants \
                   - module_globals

            if hidden:
                results.append({
                    'file': file,
                    'line': node.lineno,
                    'col': 1,
                    'code': 'Z227',
                    'msg': "function uses hidden "
                          f"dependencies: {sorted(hidden)}"
                })

    return results
