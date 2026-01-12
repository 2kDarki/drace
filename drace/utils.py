# ========================= STANDARDS =======================
from typing import NoReturn
from pathlib import Path
import ast
import sys

# ======================= THIRD-PARTIES =====================
from tuikit.logictools import any_eq, any_in, all_in
from tuikit.textools import Align, wrap_text, visual_width
from tuikit.textools import transmit as _transmit
from tuikit.listools import format_order
from tuikit.console import underline
from tuikit.textools import pathit

# ========================== LOCALS =========================
from .constants import *


center = Align().center
MARKER = None


def annotate_parents(node: ast.AST, parent=None) -> None:
    node.parent = parent
    for child in ast.iter_child_nodes(node):
        annotate_parents(child, node)


def _in_docstring(marker: str) -> bool:
    global MARKER
    marker = marker.strip()
    if MARKER and MARKER == marker: return False
    if MARKER and MARKER != marker: return True
    if not MARKER and marker != '"""': return False
    if not MARKER and marker == '"""':
        MARKER = marker
        return True


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _is_top_level_start(line: str) -> bool:
    blocks = ("def ", "class ", "if ", "for ", "while ", "try", "@")
    if line.lstrip().startswith(blocks): return True
    elif line.lstrip().startswith("#"):
        return any(b in line for b in blocks)
    return False


def _split_top_level_blocks(lines: list[str]) -> list[tuple[list[str], int]]:
    blocks       = []
    buffer       = []
    in_block     = False
    block_indent = 0
    start_lineno = 0

    for idx, line in enumerate(lines):
        if _is_top_level_start(line) and _line_indent(line) == 0:
            if buffer:
                blocks.append((buffer, start_lineno))
            buffer       = [line]
            in_block     = True
            block_indent = _line_indent(line)
            start_lineno = idx + 1
        elif in_block:
            if line.strip() == "" or _in_docstring(line) or _line_indent(line) > block_indent:
                buffer.append(line)
            else:
                blocks.append((buffer, start_lineno))
                buffer       = [line]
                in_block     = _is_top_level_start(line)
                start_lineno = idx + 1
        else:
            if not buffer:
                start_lineno = idx + 1
            buffer.append(line)

    if buffer: blocks.append((buffer, start_lineno))
    return blocks


def _shift_node_lines(node: ast.AST, offset: int) -> None:
    for subnode in ast.walk(node):
        if hasattr(subnode, 'lineno'):
            subnode.lineno += offset
        if hasattr(subnode, 'end_lineno'):
            subnode.end_lineno += offset


def try_to_parse(source: str) -> ast.Module | None:
    try: tree = ast.parse(source)
    except SyntaxError: return None
    return tree


def tolerant_parse_module(source: list[str]|str,
                          get: bool = False) -> ast.Module:
    if isinstance(source, str): source = source.splitlines()
    tree = try_to_parse("\n".join(source))
    if tree:
        annotate_parents(tree)
        return (tree, []) if get else tree
    
    nodes   = []
    blocks  = _split_top_level_blocks(source)
    synerrs = []

    for block, lineno_offset in blocks:
        try:
            parsed = ast.parse('\n'.join(block))
            for node in parsed.body:
                _shift_node_lines(node, lineno_offset - 1)
                nodes.append(node)
        except SyntaxError as e:
            lineno = e.lineno + lineno_offset - 1
            try: msg = e.msg[:e.msg.index("(")]
            except ValueError: msg = e.msg
            synerrs.append((lineno, msg))
            continue

    tree = ast.Module(body=nodes, type_ignores=[])
    annotate_parents(tree)
    if get: return tree, synerrs
    return tree


def discover_code_files(path: Path) -> list[Path] | NoReturn:
    supported = [".py"]  # will expand as I learn more langs

    if path.is_file() and path.suffix in supported:
        return [path]
    elif path.is_dir():
        sglobs = ["*"+sfx for sfx in supported]
        files  = []
        for sglob in sglobs: files.extend(path.rglob(sglob))
        return sorted(files)

    transmit(f"path '{path}' does not exist\n", hue=BAD)
    sys.exit(1)


def find_proot(path: Path) -> str:
    path = Path(path).resolve()
    if path.is_file(): path = path.parent

    markers = {
        ".git", "pyproject.toml", "setup.py", "setup.cfg",
        "requirements.txt", ".pdm.toml", "Pipfile"
    }

    for parent in [path, *path.parents]:
        if any((parent / marker).exists() for marker in markers):
            return str(parent)

    # fallback to current dir if no marker found
    return str(path)


def pc_colored(pc):
    pc_map = {"75": GOOD, "45": YELLOW}
    hue    = BAD

    for thresh in pc_map.keys():
        if pc >= int(thresh):
            hue = pc_map[thresh]; break

    return color(format_order(f"{pc:.2f}") + "%", hue)


def transmit(text: str, hue: str = PROMPT, end: str = "\n",
            _list: bool = False) -> None:
    print("        " if _list else f"{end}{DRACE}", end="")
    text = wrap_text(text, I, inline=True, order=APP)
    speed = 0 if _list else SPEED
    _transmit(text, speed=speed, hold=HOLD, hue=hue)
