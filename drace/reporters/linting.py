from pathlib import Path
import time
import os

from tuikit.textools import pathit, visual_width
from drace.constants import BAD, MODE, SEP, SPEED, WHITE, WRAP, YELLOW
from drace.linter import engine
from drace.utils import (
    color,
    format_order,
    pc_colored,
    transmit,
    wrap_text,
)


def _new_state() -> dict:
    return {"score": 0.0, "files": 0, "codes": set()}


def lint_cmd(path: str, score: bool, first: bool,
             done: bool = False, cmd: str | None = None,
             state: dict | None = None) -> int:
    if cmd is None:
        cmd = MODE
    state = state or _new_state()
    results = engine.scrutinize(path)

    is_score_mode = cmd == "score"
    mode = "linting" if cmd == "lint" else "scoring"
    if not is_score_mode:
        if cmd == "lint" and results:
            transmit(f"{mode} {color(pathit(path), WHITE)}\n")
        elif first:
            if not done: path = str(Path(path).resolve().parent)
            path = color(path.split(os.sep)[-1], WHITE)
            if results: transmit(f"{mode} {path}")

    if results:
        ldeno = len(str(max(r['line'] for r in results)))
        cdeno = len(str(max(r['col'] for r in results)))
        state["codes"].update(r['code'] for r in results)

        act_on = results if cmd == "lint" and not is_score_mode else []
        for r in act_on:
            code  = r['code']
            bold  = code == "E001"
            file  = r['file'].split(os.sep)[-1]
            line  = color(format_order(r['line'], ldeno),
                    YELLOW)
            col   = format_order(r['col'], cdeno)
            ccode = color(code, BAD, bold=bold)
            msg   = r['msg'].strip()

            if code == "Z101":
                msg, rest = msg.split("#", 1)
                check_msg = msg.split(":", 1)
                if len(check_msg) > 1 and check_msg[1] != "":
                    msg = check_msg[0] + ":"
                    if check_msg[1] != "\n":
                        msg += "\n\n" + check_msg[1].strip()

            prefix = f"{file}{SEP}{line}{SEP}{col} {ccode} "
            text   = f"{prefix}{msg}"
            indent = visual_width(prefix) if WRAP else 0
            print(wrap_text(text, indent))
            if code == "Z101": print(f"\n#{rest}\n")
            time.sleep(SPEED)

    if score or cmd == "score":
        score_it(results, done, mode, state)
    else: print()

    return 1 if "E001" in state["codes"] else 0


def score_it(results: list[dict], done: bool,
             mode: str, state: dict) -> None:
    end        = "\n" if mode == "linting" else ""
    all_issues = len(results)
    all_lines = 1
    if results:
        with open(results[0]["file"]) as handle:
            all_lines = sum(1 for _ in handle)

    score = 100 if all_lines == 0 else 100 \
          * (1 - all_issues / all_lines)

    state["score"] += score
    state["files"] += 1
    if done:
        score = state["score"] / max(state["files"], 1)

    if done:
        score = pc_colored(max(0, score))
        print()
        transmit(f"code {score} Darkian Standard\n", end=end)
