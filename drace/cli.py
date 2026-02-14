#!/usr/bin/env python3
"""Command-line entrypoint for Drace."""
# ========================= STANDARDS =======================
from typing import NoReturn, Callable
from pathlib import Path
import argparse
import sys
import os

# ========================== LOCALS =========================
from .constants import MODE, SCORE, CMDS, override
from .reporters import linting, formatting
from .help_menu import main as drace
from .native_lang import translate
from .config import config_cmd
from .docs import cli
from . import utils


__doc__ = cli


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the Drace CLI.

    Supports four subcommands:
    - format: Format Python files with optional diff and
      score display
    - lint: Lint Python files and optionally display a score
    - score: Show the code quality score for a given path
    - config: View or modify Drace configuration (interactive
      or direct)

    Args:
        argv (list[str]): Command-line args excluding program
            name.

    Returns:
        argparse.Namespace: Parsed command namespace.
    """
    p   = argparse.ArgumentParser(description=drace())
    sub = p.add_subparsers(dest="cmd")

    # formatter
    fmt = sub.add_parser("format")
    fmt.add_argument("path")
    fmt.add_argument("--diff", action="store_true")
    fmt.add_argument("--score", nargs="?", default=SCORE)
    fmt.add_argument("--strict-fix", action="store_true")
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
    Entry point for the Drace CLI.

    Parses command-line arguments, resolves default command
    behavior, and dispatches to command handlers.
    """
    def workflow(
        run: Callable[[str, bool, bool, bool, dict], int],
        state: dict,
    ) -> int:
        nonlocal exit_code
        files = utils.discover_code_files(path)

        try: score = args.score
        except AttributeError: score = False

        for i, file in enumerate(files):
            file = str(file)
            file, discard = translate(file)
            done = i == len(files) - 1
            try: exc = run(file, score, i == 0, done, state)
            except KeyboardInterrupt:
                utils.transmit("user aborted\n", utils.BAD)
                sys.exit(1)
            if not exit_code: exit_code = exc
            if discard: os.remove(file)
        return exit_code

    help_flags = {"-h", "--help", "-help"}
    if len(sys.argv) == 1:
        sys.argv.extend([MODE, "."])
    elif sys.argv[1] not in CMDS and sys.argv[1] not in help_flags:
        sys.argv.insert(1, MODE)

    args = parse_args(sys.argv[1:])
    try: path = Path(args.path)
    except AttributeError: pass

    args      = override(args)
    exit_code = 0
    lint_state = {"score": 0.0, "files": 0, "codes": set()}

    if args.cmd == "format":
        formatting.format_cmd(path, diff=args.diff, score=args.score)
        if args.strict_fix:
            if args.diff:
                utils.transmit(
                    "--strict-fix cannot be combined with --diff\n",
                    utils.BAD,
                )
                exit_code = 1
            else:
                unresolved = formatting.count_unresolved(path)
                if unresolved:
                    utils.transmit(
                        "strict-fix failed: "
                        f"{unresolved} unresolved finding(s)\n",
                        utils.BAD,
                    )
                    exit_code = 1
    elif args.cmd in ["lint", "score"]:
        exit_code = workflow(
            lambda file, score, first, done, state:
            linting.lint_cmd(file, score, first, done, args.cmd, state),
            lint_state,
        )
    elif args.cmd == "config":
        config_cmd(args.args)

    sys.exit(exit_code)


if __name__ == "__main__": main()
