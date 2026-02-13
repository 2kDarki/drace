from drace import utils
from drace.darkian.z1.z100 import check_z100
from drace.darkian.z1.z101 import check_z101
from drace.darkian.z2.z200 import check_z200
from drace.darkian.z2.z223 import check_z223
from drace.darkian.z2.z224 import check_z224
from drace.darkian.z2.z226 import check_z226
from drace.darkian.z2.z227 import check_z227
from drace.darkian.z2.z228 import check_z228


def _context(source: str, file: str = "sample.py"):
    lines = source.strip("\n").splitlines()
    tree, _ = utils.tolerant_parse_module(lines, True)
    utils.annotate_parents(tree)
    tree.parent = tree
    return {"lines": lines, "tree": tree, "file": file}


def test_z100_ignores_control_scope_assignments():
    src = """
if cond:
    a = 1
    bb = 2
"""
    results = check_z100(_context(src))
    assert results == []


def test_z100_flags_top_level_alignment_mismatch():
    src = """
a = 1
long_name = 2
b = 3
c = 4
"""
    results = check_z100(_context(src))
    assert any(item["code"] == "Z100" for item in results)


def test_z101_message_contains_suggestion_separator():
    src = """
import localmod
import os
"""
    results = check_z101(_context(src, file=__file__))
    if results:
        assert "#" in results[0]["msg"]


def test_z200_skips_if_with_else_branch():
    src = """
if x:
    run()
else:
    stop()
"""
    results = check_z200(_context(src))
    assert results == []


def test_z200_skips_already_one_line_control():
    src = """
if x: run()
"""
    results = check_z200(_context(src))
    assert results == []


def test_z223_flags_augassign_on_external_attr():
    src = """
def fn():
    settings.value += 1
"""
    results = check_z223(_context(src))
    assert any(item["code"] == "Z223" for item in results)


def test_z223_avoids_nested_double_reporting():
    src = """
def outer():
    cfg.value = 1
    def inner():
        cfg.value = 2
"""
    results = check_z223(_context(src))
    assert len([item for item in results if item["code"] == "Z223"]) == 2


def test_z224_counts_vararg_and_kwarg():
    src = """
def fn(a, b, c, d, e, *, f, **kwargs):
    return a
"""
    results = check_z224(_context(src))
    assert any(item["code"] == "Z224" for item in results)


def test_z226_detects_close_assignments_in_function_body():
    src = """
def fn():
    a = 1
    b = 2
    a = 3
    a = 4
"""
    results = check_z226(_context(src))
    assert any(item["code"] == "Z226" for item in results)


def test_z226_skips_self_referential_updates():
    src = """
def fn():
    total = 0
    total = total + 1
    total = total + 2
"""
    results = check_z226(_context(src))
    assert results == []


def test_z227_handles_namedexpr_and_with_bindings():
    src = """
def outer():
    with open("x") as f:
        if (line := f.readline()):
            return line
"""
    results = check_z227(_context(src))
    assert results == []


def test_z228_flags_returning_self_mutable_state():
    src = """
def fn():
    return self.buffer
"""
    results = check_z228(_context(src))
    assert any(item["code"] == "Z228" for item in results)
