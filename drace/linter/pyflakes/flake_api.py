"""API for running pyflakes."""
# ======================== STANDARDS ========================
from io import StringIO

# ========================== LOCALS =========================
from drace.utils import tolerant_parse_module
from .reporter import Reporter
from .checker import Checker


__all__ = ['check']


def check(filename: str, buffer: StringIO):
    """
    Check the Python source given by C{source} for flakes.
    """
    with open(filename) as f: source = f.read()
    reporter = Reporter(buffer, buffer)

    # First, compile into an AST and handle syntax errors.
    tree = tolerant_parse_module(source)

    # Okay, it's syntactically valid.  Now check it.
    w = Checker(tree, filename=filename)
    w.messages.sort(key=lambda m: m.line)
    for warning in w.messages: reporter.flake(warning)
