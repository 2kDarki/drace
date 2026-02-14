from drace import utils
from drace.darkian.z1.z100 import check_z100, fixes_z100
from drace.darkian.z1.z101 import check_z101


def _context(source: str, file: str = "sample.py"):
    lines = source.strip("\n").splitlines()
    tree, _ = utils.tolerant_parse_module(lines, True)
    utils.annotate_parents(tree)
    tree.parent = tree
    return {"lines": lines, "tree": tree, "file": file}


def test_z100_emits_replace_line_fix():
    src = """
a=1
long_name =2
bbb=   3
cccc =4
"""
    results = check_z100(_context(src))
    assert results
    assert all(item.get("fix", {}).get("op") == "replace_line" for item in results)
    assert all(isinstance(item.get("fix", {}).get("content"), str) for item in results)

    fixes = fixes_z100(_context(src))
    assert any(fix.get("content") == "long_name = 2" for fix in fixes)


def test_z101_emits_replace_block_fix():
    src = """
import os
import sys
"""
    results = check_z101(_context(src))
    assert results
    fix = results[0].get("fix", {})
    assert fix.get("op") == "replace_block"
    assert fix.get("start") == 1
    assert fix.get("end") == 2
    assert fix.get("content") == ["import sys", "import os"]
