from functools import lru_cache
from pathlib import Path
import importlib.util
import site
import sys
import os

from drace.types import Context, Dict, Fix
from drace.utils import Align, find_proot


GROUPS = ("FUTURE", "STANDARDS", "THIRD_PARTIES", "LOCALS")


def _project_modules(proot) -> list[Path]:
    modules = []
    for child in Path(proot).iterdir():
        if child.is_dir():
            dir = str(child).split(os.sep)[-1]
            if dir == "__pycache__": continue
            modules.append(dir)
            modules.extend(_project_modules(child))

    return modules


def _render_darkian_block(grouped_lines: dict[str, list[str]]) -> str:
    sections: list[str] = []
    center = Align(offset=2).center

    for group in GROUPS:
        lines = grouped_lines.get(group, [])
        if not lines: continue
        if group == "FUTURE":
            sections.extend(lines)
            sections.append("")
            continue

        if group == "STANDARDS":
            sections.append(f"# {center(' STANDARDS ', '=')}")
        elif group == "THIRD_PARTIES":
            sections.append(f"# {center(' THIRD PARTIES ', '=')}")
        elif group == "LOCALS":
            sections.append(f"# {center(' LOCALS ', '=')}")

        sections.extend(lines)
        sections.append("")

    while sections and sections[-1] == "": sections.pop()
    return "\n".join(sections)


def _site_roots() -> set[str]:
    roots = set()
    for getter in (site.getsitepackages, site.getusersitepackages):
        try: value = getter()
        except Exception: continue
        if isinstance(value, str):
            roots.add(os.path.abspath(value))
        else: roots |= {os.path.abspath(item) for item in value}
    return roots


@lru_cache(maxsize=2048)
def _classify_import(name: str, project_root: str) -> str:
    if name == "__future__": return "FUTURE"
    if name.startswith("."): return "LOCALS"
    if not name: return "LOCALS"

    try: spec = importlib.util.find_spec(name.split(".", 1)[0])
    except Exception: spec = None

    if spec is None: return "LOCALS"

    origin = getattr(spec, "origin", None)
    if origin in ("built-in", "frozen"): return "STANDARDS"

    if origin is None:
        if "." in name: name = name.split(".")[0]
        if name in _project_modules(project_root):
            return "LOCALS"
        return "THIRD_PARTIES"

    origin       = os.path.abspath(origin)
    origin_lower = origin.lower()
    proot        = project_root.lower()

    if origin_lower.startswith(proot): return "LOCALS"

    for root in _site_roots():
        if origin_lower.startswith(root.lower()):
            return "THIRD_PARTIES"

    stdlib = os.path.abspath(sys.base_prefix).lower()
    if origin_lower.startswith(stdlib): return "STANDARDS"

    return "LOCALS" if name in _project_modules(project_root) \
      else "THIRD_PARTIES"


def _module_name_from_import(stmt: str) -> str:
    stripped = stmt.strip()
    if stripped.startswith("from "):
        parts = stripped.split()
        return parts[1] if len(parts) > 1 else ""
    if stripped.startswith("import "):
        first = stripped[len("import "):].split(",", 1)[0].strip()
        return first.split()[0] if first else ""
    return ""


def _collect_import_blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    blocks: list[tuple[int, list[str]]] = []
    start = None
    current: list[str] = []

    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("import ") or s.startswith("from "):
            if start is None:
                start = i
            current.append(raw.rstrip("\n"))
            continue

        if current:
            blocks.append((start, current))
            current = []
            start = None

    if current:
        blocks.append((start, current))
    return blocks


def _replacement_block(grouped: dict[str, list[str]]) -> list[str]:
    replacement: list[str] = []
    non_empty_groups = 0
    for group in GROUPS:
        items = sorted(grouped[group], key=len, reverse=True)
        if not items:
            continue
        if non_empty_groups:
            replacement.append("")
        replacement.extend(items)
        non_empty_groups += 1
    return replacement


def check_z101(context: Context) -> list[Dict]:
    """
    Z101: enforce Darkian import block ordering.
    """
    lines = context["lines"]
    file = context["file"]
    project_root = find_proot(file)
    results: list[Dict] = []

    for start_idx, block in _collect_import_blocks(lines):
        grouped: dict[str, list[str]] = {group: [] for group in GROUPS}
        current_order: list[str] = []

        for statement in block:
            module_name = _module_name_from_import(statement)
            group = _classify_import(module_name, project_root)
            grouped[group].append(statement)
            current_order.append(statement)

        expected_grouped: dict[str, list[str]] = {}
        expected_order: list[str] = []
        for group in GROUPS:
            items = sorted(grouped[group], key=len, reverse=True)
            expected_grouped[group] = items
            expected_order.extend(items)

        if current_order == expected_order:
            continue

        suggestion = _render_darkian_block(expected_grouped)
        replacement = _replacement_block(grouped)
        fix: Fix = {
            "op": "replace_block",
            "start": start_idx + 1,
            "end": start_idx + len(block),
            "content": replacement,
        }
        results.append({
            "file": file,
            "line": start_idx + 1,
            "col": 1,
            "code": "Z101",
            "msg": (
                "import block not ordered by Darkian Standard "
                "(grouped + descending line length).#\n"
                f"{suggestion}"
            ),
            "fix": fix,
        })

    return results
