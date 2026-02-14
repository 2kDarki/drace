from drace import utils
from drace.darkian.z1.z103 import fixes_z103


def _context(source: str, file: str = "sample.py"):
    lines = source.strip("\n").splitlines()
    tree, _ = utils.tolerant_parse_module(lines, True)
    utils.annotate_parents(tree)
    tree.parent = tree
    return {"lines": lines, "tree": tree, "file": file}


def test_fixes_z103_removes_unused_imports_and_keeps_used_aliases():
    src = """
import os
import sys as system
from pkg import a, b

print(system.version)
print(a)
"""
    fixes = fixes_z103(_context(src))
    by_line = {int(fix["line"]): fix for fix in fixes}

    assert by_line[1]["content"] == ""
    assert by_line[3]["content"] == "from pkg import a"
    assert 2 not in by_line
