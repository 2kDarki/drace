from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import difflib
import os

from drace import utils
from drace.constants import BAD, COLOR, GOOD, PROMPT, YELLOW
from drace.darkian import get_fixers, get_rules
from drace.linter import engine
from drace.types import Context, Dict, Fix
from drace.utils import color, pc_colored, transmit


def _build_context(lines: list[str], file: str) -> Context:
    tree, _ = utils.tolerant_parse_module(lines, True)
    utils.annotate_parents(tree)
    tree.parent = tree
    return {"lines": lines, "tree": tree, "file": file}


def _collect_fixes(
    context: Context,
    rules: list[Callable[[Context], list[Dict]]],
    fixers: list[Callable[[Context], list[Fix]]],
) -> list[Fix]:
    fixes: list[Fix] = []

    for rule in rules:
        findings = rule(context)
        for finding in findings:
            fix = finding.get("fix")
            if isinstance(fix, dict) and fix.get("op"):
                fixes.append(fix)

    for fixer in fixers:
        generated = fixer(context)
        for fix in generated:
            if isinstance(fix, dict) and fix.get("op"):
                fixes.append(fix)

    return fixes


def _fix_span(fix: Fix) -> tuple[int, int]:
    if fix["op"] == "replace_block":
        start = int(fix.get("start", 1))
        end = int(fix.get("end", start))
        return start, end

    line = int(fix.get("line", 1))
    return line, line


def _apply_fixes(lines: list[str], fixes: list[Fix]) -> list[str]:
    updated = list(lines)
    ordered = sorted(fixes, key=lambda f: _fix_span(f)[0], reverse=True)

    for fix in ordered:
        op = fix["op"]
        if op == "replace_line":
            line = int(fix.get("line", 0))
            content = fix.get("content")
            if not isinstance(content, str) or line < 1 or line > len(updated):
                continue
            updated[line - 1] = content
            continue

        if op == "replace_block":
            start = int(fix.get("start", 0))
            end = int(fix.get("end", 0))
            content = fix.get("content")
            if (
                not isinstance(content, list)
                or start < 1
                or end < start
                or end > len(updated)
                or not all(isinstance(item, str) for item in content)
            ):
                continue
            updated[start - 1 : end] = content

    return updated


def _format_source(
    text: str,
    file: str,
    rules: list[Callable[[Context], list[Dict]]],
    fixers: list[Callable[[Context], list[Fix]]],
    max_passes: int = 4,
) -> str:
    has_trailing_newline = text.endswith("\n")
    lines = text.splitlines()

    for _ in range(max_passes):
        context = _build_context(lines, file)
        fixes = _collect_fixes(context, rules, fixers)
        if not fixes:
            break

        updated = _apply_fixes(lines, fixes)
        if updated == lines:
            break
        lines = updated

    rendered = "\n".join(lines)
    if has_trailing_newline:
        rendered += "\n"
    return rendered


def _print_diff(file: str, original: str, formatted: str) -> None:
    original_lines = original.splitlines(keepends=True)
    formatted_lines = formatted.splitlines(keepends=True)
    rel = os.path.relpath(file, start=os.getcwd())
    diff = difflib.unified_diff(
        original_lines,
        formatted_lines,
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
        n=3,
    )
    for line in diff:
        rendered = line
        if COLOR:
            if line.startswith("--- ") or line.startswith("+++ "):
                rendered = color(line.rstrip("\n"), PROMPT) + "\n"
            elif line.startswith("@@ "):
                rendered = color(line.rstrip("\n"), YELLOW) + "\n"
            elif line.startswith("+"):
                rendered = color(line.rstrip("\n"), GOOD) + "\n"
            elif line.startswith("-"):
                rendered = color(line.rstrip("\n"), BAD) + "\n"
            elif line.startswith("\\ No newline at end of file"):
                rendered = color(line.rstrip("\n"), YELLOW) + "\n"
        print(rendered, end="")


def _score_files(files: list[Path]) -> None:
    scores = []
    for file in files:
        file_str = str(file)
        if engine._is_embedded_vendor(file_str):
            continue
        results = engine.scrutinize(file_str)
        all_issues = len(results)
        all_lines = 1
        if results:
            with open(file_str, encoding="utf-8") as handle:
                all_lines = sum(1 for _ in handle)
        score = 100 if all_lines == 0 else 100 * (1 - all_issues / all_lines)
        scores.append(max(0, score))

    final_score = sum(scores) / max(len(scores), 1)
    transmit(f"code {pc_colored(final_score)} Darkian Standard\n", end="")


def count_unresolved(path: Path | str) -> int:
    path = Path(path)
    files = utils.discover_code_files(path)
    unresolved = 0
    for file in files:
        file_str = str(file)
        if engine._is_embedded_vendor(file_str):
            continue
        unresolved += len(engine.scrutinize(file_str))
    return unresolved


def format_cmd(path: Path | str, diff: bool = False, score: bool = False) -> int:
    path = Path(path)
    files = utils.discover_code_files(path)
    rules = get_rules(engine.IGNORE, engine.ONLY)
    fixers = get_fixers(engine.IGNORE, engine.ONLY)
    changed = 0

    for file in files:
        file_str = str(file)
        if engine._is_embedded_vendor(file_str):
            continue

        original = file.read_text(encoding="utf-8")
        formatted = _format_source(original, file_str, rules, fixers)
        if formatted == original:
            continue

        changed += 1
        if diff:
            _print_diff(file_str, original, formatted)
            if not formatted.endswith("\n"):
                print("\\ No newline at end of file")
            print()
        else:
            file.write_text(formatted, encoding="utf-8")
            transmit(f"formatted {file_str}\n")

    if diff:
        transmit(f"done: {changed} file(s) would change\n")
    else:
        transmit(f"done: {changed} file(s) changed\n")

    if score and files:
        _score_files(files)

    return changed
