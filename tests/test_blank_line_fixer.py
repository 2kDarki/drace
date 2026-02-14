from drace import utils
from drace.darkian.z1.z104 import fixes_z104


def _context(source: str, file: str = "sample.py"):
    lines = source.splitlines()
    tree, _ = utils.tolerant_parse_module(lines, True)
    utils.annotate_parents(tree)
    tree.parent = tree
    return {"lines": lines, "tree": tree, "file": file}


def test_fixes_z104_collapses_long_blank_runs():
    src = "a = 1\n\n\n\nb = 2\n"
    fixes = fixes_z104(_context(src))
    assert fixes == [
        {
            "op": "replace_block",
            "start": 2,
            "end": 4,
            "content": ["", ""],
        }
    ]
