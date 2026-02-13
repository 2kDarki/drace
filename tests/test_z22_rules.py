from drace.darkian.z2.z221 import check_z221
from drace.darkian.z2.z222 import check_z222
from drace.darkian.z2.z223 import check_z223
from drace.darkian.z2.z224 import check_z224
from drace.darkian.z2.z225 import check_z225
from drace.darkian.z2.z226 import check_z226
from drace.darkian.z2.z228 import check_z228
from drace.darkian.z2.z229 import check_z229
from drace import utils


def _context(source: str):
    lines = source.strip("\n").splitlines()
    tree, _ = utils.tolerant_parse_module(lines, True)
    utils.annotate_parents(tree)
    tree.parent = tree
    return {"lines": lines, "tree": tree, "file": "sample.py"}


def test_z221_flags_bloated_function():
    src = """
def x():
    if a: pass
    if b: pass
    if c: pass
    if d: pass
    if e: pass
    if f: pass
    if g: pass
"""
    results = check_z221(_context(src))
    assert any(item["code"] == "Z221" for item in results)


def test_z222_flags_external_coupling():
    src = """
def x():
    one.a
    two.b
    three.c
    four.d
    five.e
    six.f
    seven.g
    eight.h
    nine.i
"""
    results = check_z222(_context(src))
    assert any(item["code"] == "Z222" for item in results)


def test_z223_flags_implicit_state_mutation():
    src = """
def x(arg):
    external.value = 1
"""
    results = check_z223(_context(src))
    assert any(item["code"] == "Z223" for item in results)


def test_z224_flags_parameter_explosion():
    src = """
def x(a, b, c, d, e, f, g):
    return a
"""
    results = check_z224(_context(src))
    assert any(item["code"] == "Z224" for item in results)


def test_z225_flags_large_dict():
    src = """
data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}
"""
    results = check_z225(_context(src))
    assert any(item["code"] == "Z225" for item in results)


def test_z226_flags_temporal_sequence():
    src = """
value = 1
value = 2
value = 3
"""
    results = check_z226(_context(src))
    assert any(item["code"] == "Z226" for item in results)


def test_z228_flags_returning_internal_structures():
    src = """
CACHE = {}

def x():
    global CACHE
    return CACHE
"""
    results = check_z228(_context(src))
    assert any(item["code"] == "Z228" for item in results)


def test_z229_flags_many_return_shapes():
    src = """
def x(a):
    if a == 0:
        return 1
    if a == 1:
        return "ok"
    if a == 2:
        return [1]
    if a == 3:
        return {"a": 1}
    return None
"""
    results = check_z229(_context(src))
    assert any(item["code"] == "Z229" for item in results)
