"""API for running pyflakes."""
from drace.utils import tolerant_parse_module
from .reporter import Reporter
from .checker import Checker


__all__ = ['check']


def check(filename: str, reporter: Reporter):
    """
    Check the Python source given by C{source} for flakes.
    """
    with open(filename) as f: source = f.read()

    # First, compile into an AST and handle syntax errors.
    tree = tolerant_parse_module(source)

    # Okay, it's syntactically valid.  Now check it.
    w = Checker(tree, filename=filename)
    w.messages.sort(key=lambda m: m.lineno)
    for warning in w.messages: reporter.flake(warning)
