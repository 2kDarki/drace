#!/usr/bin/env python3
"""
This module defines the command-line interface for Drace — a
pragmatic linter and formatter for Python code.  

It handles argument parsing and dispatches execution to the
appropriate command module based on user input.

Commands:
- `drace format <path>`: Format code and optionally show a
   diff
- `drace lint <path>`: Lint Python files and display
   suggestions or warnings
- `drace score <path>`: Compute and display a score based on
   linting results
- `drace config [args]`: Configure default settings
  interactively or via command arguments

Example usage:
    drace lint project/
    drace format script.py --diff
    drace config line_len 100
"""
# ========================= STANDARDS =======================
from typing import NoReturn, Callable
from pathlib import Path
import argparse
import sys
import os

# ========================== LOCALS =========================
from .constants import LINE_LEN, MODE, SCORE, CMDS, override
from .reporters import linting, formatting
from .help_menu import main as drace
from .native_lang import translate
from .config import config_cmd
from .docs import cli
from . import utils


__doc__ = cli


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the Drace CLI

    Supports four subcommands:
    - format: Format Python files with optional diff and
      score display
    - lint: Lint Python files and optionally display a score
    - score: Show the code quality score for a given path
    - config: View or modify Drace configuration (interactive
      or direct)

    Args:
        argv (list): List of command-line arguments
                     (excluding program name)

    Returns:
        argparse.Namespace: Parsed arguments with attributes
                            based on subcommand
    """
    p   = argparse.ArgumentParser(description=drace())
    sub = p.add_subparsers(dest="cmd")

    # formatter
    fmt = sub.add_parser("format")
    fmt.add_argument("path")
    fmt.add_argument("--diff", action="store_true")
    fmt.add_argument("--score", nargs="?", default=SCORE)
    fmt.add_argument("--color", action="store_true")

    # linter
    lint = sub.add_parser("lint")
    lint.add_argument("path")
    lint.add_argument("--score", nargs="?", default=SCORE)
    lint.add_argument("--color", action="store_true")

    # scoring
    score = sub.add_parser("score")
    score.add_argument("path")
    score.add_argument("--color", action="store_true")

    # config
    config = sub.add_parser("config")
    config.add_argument("args", nargs="*")

    return p.parse_args(argv)


def main() -> None | NoReturn:
    """
    Entry point for the Drace CLI

    Parses command-line arguments and dispatches to the 
    appropriate handler:
    - format: Formats the given file or directory
    - lint: Lints one or more Python files
    - score: Displays lint score for the given path
    - config: Opens or modifies configuration
    """
    def workflow(run: Callable) -> int:
        nonlocal exit_code
        files = utils.discover_code_files(path)

        try: score = args.score
        except AttributeError: score = False

        for i, file in enumerate(files):
            file = str(file)
            file, discard = translate(file)
            done = i == len(files) - 1
            try: exc = run(file, score, i == 0, done)
            except KeyboardInterrupt:
                utils.transmit("user aborted\n", utils.BAD)
                sys.exit(1)
            if not exit_code: exit_code = exc
            if discard: os.remove(file)
        return exit_code

    
    try:
        if sys.argv[1] not in CMDS:
            sys.argv.insert(1, MODE)
    except IndexError: sys.argv.extend([MODE, "."])

    args = parse_args(sys.argv[1:])
    try: path = Path(args.path)
    except AttributeError: pass

    args      = override(args)
    exit_code = 0
    
    if args.cmd == "format":
        formatting.format_cmd(path, diff=args.diff)
    elif args.cmd in ["lint", "score"]:
        exit_code = workflow(linting.lint_cmd)
    elif args.cmd == "config":
        config_cmd(args.args)

    sys.exit(exit_code)


if __name__ == "__main__": main()
