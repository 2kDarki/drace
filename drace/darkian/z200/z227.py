import builtins
import ast

from drace import utils

def check(tree, file: str) -> list[dict]:
    """
    Z227: Detect hidden dependencies in functions and nested functions.
    Hidden dependency = a name used in a function that is not:
      - a parameter or local variable (or nested def/class),
      - an imported name,
      - a built-in,
      - a module-level constant (ALL_CAPS assigned at top level).
    Globals (non-constant) and other external names will be flagged.
    """
    results = []
    
    builtin_names: set[str] = set(dir(builtins))

    # 1. Collect imported names (module‑level)
    imported_names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name.split(".")[0])

    # 2. Collect module‑level variable names → identify constants
    module_globals: set[str] = set()
    module_constants: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if hasattr(node, "targets") else [node.target]
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
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            module_globals.add(node.name)
    
    def get_enclosing_locals(node: ast.AST) -> set[str]:
        visible: set[str] = set()
        is_nested = isinstance(node.parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        cur = node

        while hasattr(cur, "parent"):
            if isinstance(cur, ast.Module): break
            is_global = not isinstance(cur.parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for sub in ast.iter_child_nodes(cur):
                # Handle assignments and annotated assignments
                if isinstance(sub, (ast.Assign, ast.AnnAssign)):
                    targets = sub.targets if hasattr(sub, "targets") else [sub.target]
                    for t in targets:
                        for name in extract_names(t):
                            if is_nested:
                                if name.isupper:
                                    visible.add(name)
                            else: visible.add(name)
                # Handle function/class/lambda defs
                elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if is_global:
                        visible.add(sub.name)
                    elif is_nested:
                        visible.add(sub.name)  # Always include function/class names

                elif isinstance(sub, ast.arg):
                    visible.add(sub.arg)

                elif isinstance(sub, ast.ExceptHandler) and sub.name:
                    visible.add(sub.name)
            cur = cur.parent
        return visible


    def extract_names(node):
        """Recursively extract name identifiers from ast targets (for assignment, tuple unpacking, etc)."""
        names: set[str] = set()
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names |= extract_names(elt)
        return names

    # Build parent map: node -> parent node
    utils.annotate_parents(tree)

    # 3. Walk through all functions and check for hidden deps
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if isinstance(node.parent, ast.Module): continue
            # Collect used names inside this function
            used_names: set[str] = {
                n.id for n in ast.walk(node)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
            }

            # Collect locals: arguments, names assigned within the function body, names of nested defs/classes
            local_vars: set[str] = set()
            args = node.args
            for arg in list(args.args) + list(args.kwonlyargs):
                local_vars.add(arg.arg)
            if args.vararg:
                local_vars.add(args.vararg.arg)
            if args.kwarg:
                local_vars.add(args.kwarg.arg)
            for sub in ast.iter_child_nodes(node):
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    local_vars.add(sub.name if hasattr(sub, "name") else "<lambda>")
            # Also treat names assigned inside as locals
            for sub in ast.walk(node):
                if isinstance(sub, (ast.Assign, ast.AnnAssign)):
                    targets = sub.targets if hasattr(sub, "targets") else [sub.target]
                    for t in targets:
                        local_vars |= extract_names(t)
                elif isinstance(sub, (ast.For, ast.comprehension)):
                    target = getattr(sub, "target", None)
                    if target is not None:
                        local_vars |= extract_names(target)
                elif isinstance(sub, ast.ExceptHandler) and sub.name:
                    local_vars.add(sub.name)

            # Determine visible names from enclosing (non-module) scopes
            visible_from_enclosing = get_enclosing_locals(node)

            # Now compute hidden dependencies
            hidden = used_names - local_vars - visible_from_enclosing \
                     - builtin_names - imported_names - module_constants

            
            if hidden:
                results.append({
                    'file': file,
                    'line': node.lineno,
                    'col': 1,
                    'code': 'Z227',
                    'msg': f"function uses hidden dependencies: {sorted(hidden)}"
                })

    return results
