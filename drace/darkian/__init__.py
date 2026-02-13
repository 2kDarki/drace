# ======================= STANDARDS =========================
from collections.abc import Callable
from pathlib import Path
import importlib

# ========================= LOCALS ==========================
from drace.types import Context, Dict


ROOT = Path(__file__).resolve().parent


def _is_private(name: str) -> bool:
    return name.startswith("_") or name.startswith(".")


def get_rules(
    ignore: tuple[str, ...],
    only: list[str],
) -> list[Callable[[Context], list[Dict]]]:
    """
    Dynamically discover and load linting rule functions.

    Discovery rules:
    - Only imports python files from non-private series dirs.
    - Rule file name maps to rule code (e.g. z221.py -> Z221).
    - Only callables prefixed with `check_` are registered.
    """
    ignore_set = {name.upper() for name in ignore}
    only_set = {name.upper() for name in only}
    rules: list[Callable[[Context], list[Dict]]] = []

    for series_dir in sorted(ROOT.iterdir()):
        if not series_dir.is_dir() or _is_private(series_dir.name):
            continue

        for module_file in sorted(series_dir.iterdir()):
            if not module_file.is_file() or module_file.suffix != ".py":
                continue
            if _is_private(module_file.name):
                continue

            code = module_file.stem.upper()
            if only_set and code not in only_set:
                continue
            if code in ignore_set:
                continue

            module = importlib.import_module(
                f"{__package__}.{series_dir.name}.{module_file.stem}"
            )
            for attr in sorted(dir(module)):
                if not attr.startswith("check_"):
                    continue
                fn = getattr(module, attr)
                if callable(fn):
                    rules.append(fn)

    return rules
