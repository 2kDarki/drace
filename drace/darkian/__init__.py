import importlib
import pkgutil

def get_rules():
    rules = []
    pkg = __package__
    for _, name, _ in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{pkg}.{name}")
        for attr in dir(mod):
            if attr.startswith("rule_"):
                fn = getattr(mod, attr)
                if callable(fn): rules.append(fn)
    return rules
