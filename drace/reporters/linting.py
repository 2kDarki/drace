from drace.linter import engine
from drace.utils import *
from pathlib import Path
import time
import os

SCORE = 0
FILES = 0


def format_cmd(path, diff=False):
    # Placeholder
    print(f"[drace] formatting {path} (diff={diff})")


def lint_cmd(path: str, score: bool, first: bool,
             done: bool = False) -> int:
    results = engine.scrutinize(path)

    mode = "scoring" if "score" in sys.argv else "linting"
    if mode == "linting":
        if not results: return 0
        transmit(f"{mode} {color(pathit(path), WHITE)}\n")
    elif first:
        if not done: path = str(Path(path).resolve().parent)
        path = color(path.split(os.sep)[-1], WHITE)
        transmit(f"{mode} {path}")

    if not results: return 0

    ldeno = len(str(max(r['line'] for r in results)))
    cdeno = len(str(max(r['col'] for r in results)))
    codes = set(r['code'] for r in results)

    act_on = results if mode == "linting" else []
    for r in act_on:
        code  = r['code']
        bold  = code == "E001"
        file  = r['file'].split(os.sep)[-1]
        line  = color(format_order(r['line'], ldeno), YELLOW)
        col   = format_order(r['col'], cdeno)
        ccode = color(code, BAD, bold=bold)
        msg   = r['msg'].strip()

        if code == "Z101":
            try: msg, rest = msg.split("#", 1)
            except ValueError: rest = ""
            check_msg = msg.split(":", 1)
            if len(check_msg) > 1 and check_msg[1] != "":
                msg = check_msg[0] + ":"
                if check_msg[1] != "\n":
                    msg += "\n\n" + check_msg[1].strip()

        first      = f"{file}{SEP}{line}{SEP}{col} {ccode} "
        suggestion = f"{first}{msg}"
        indent     = visual_width(first) if WRAP else 0
        print(wrap_text(suggestion, indent))
        if code == "Z101": print(f"\n#{rest}\n")
        time.sleep(SPEED)

    if score or mode == "scoring":
        score_it([results, done], mode)
    else: print()

    return 1 if "E001" in codes else 0


def score_it(linted: list[list[dict], bool],
             mode: str) -> None:
    global FILES, SCORE
    end        = "\n" if mode == "linting" else ""
    results    = linted[0]
    all_issues = len(results)
    all_lines  = sum(1 for _ in open(results[0]['file']))\
              if results else 1

    score = 100 if all_lines == 0 else 100 \
          * (1 - all_issues / all_lines)

    if linted:
        SCORE += score
        FILES += 1
        if linted[1]: score = SCORE / FILES

    if not linted or linted[1]:
        score = pc_colored(max(0, score))
        transmit(f"code {score} Darkian Standard\n", end=end)
