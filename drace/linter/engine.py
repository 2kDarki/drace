# ======================= STANDARDS =========================
from pathlib import Path
import io
import os

# ========================= LOCALS ==========================
from drace.constants import IGNORED_RULES, ONLY
from drace.darkian import get_rules
from .pycodestyle import Checker
from .pyflakes import flake_api
from drace import utils


IGNORE = ("E113", "E121", "E124", "E126", "E127", "E128",
          "E131", "E221", "E222", "E701", "E702", "E704") \
       + tuple(IGNORED_RULES)

EMBEDDED_VENDOR_PATHS = (
    f"{os.sep}drace{os.sep}linter{os.sep}pycodestyle.py",
    f"{os.sep}drace{os.sep}linter{os.sep}pyflakes{os.sep}",
)


def _is_embedded_vendor(file: str | Path) -> bool:
    normalized = os.path.abspath(str(file))
    return any(marker in normalized for marker in EMBEDDED_VENDOR_PATHS)


def run_style_checks(file: str | Path) -> list[dict]:
    """Run Darkian-patched pycodestyle checks on a file."""
    file = str(file)

    # Build checker and capture final
    checker = Checker(file)
    checker.check_all()

    results = []
    for line, col, code, msg in checker.report.errors:
        if ONLY and code not in ONLY: continue
        if code in IGNORE: continue
        results.append({
            "file": file,
            "line": line,
             "col": col,
            "code": code,
             "msg": " ".join(msg.strip().split()[1:])
        })

    return results


def run_flake_checks(file: str | Path) -> list[dict]:
    """Run pyflakes checks on a file."""
    def format_flake(msg: str) -> tuple[str]:
        code = "Z999"

        checks = (
            ("imported but unused", "W611"),
            ("*' used; unable t", "F403"),
            ("undefined name", "E602"),
            ("but never used", "W612"),
            ("f-string is", "F541"),
        )
        for pattern, mapped_code in checks:
            if pattern in msg:
                code = mapped_code
        if "syntax error" in msg.lower():
            code = "E001"

        if "star imports" in msg:
            code  = "F405"
            parts = msg.split(":")
            stars = parts[1].split(",")
            imp   = "imports:" if len(stars) > 1 else "import:"
            s_str = ""
            for i, star in enumerate(stars):
                sep = "," if s_str else ""
                if i and i == len(stars) - 1: sep = " or"
                s_str += f"{sep} {star.strip()}"
            msg = parts[0].replace("imports", imp) + s_str

        return code, msg

    buffer = io.StringIO()
    flake_api.check(str(file), buffer)

    results = []
    for warning in buffer.getvalue().splitlines():
        parts = warning.split(":", 3)[1:]
        if len(parts) == 3:
            line, col, _  = parts
            code, message = format_flake(_)
            if ONLY and code not in ONLY: continue
            if code in IGNORE: continue
            if "unexpected indent" in message: continue
            if "unterminated stri" in message: continue
            results.append({
                "file": file,
                "line": int(line.strip()),
                 "col": int(col.strip()),
                "code": code,
                 "msg": message
            })

    return results


def run_darkian_checks(file: str | Path) -> list[dict]:
    """Run Darkian checks on a file."""
    lines   = Path(file).read_text(encoding="utf-8")\
              .splitlines()
    file    = str(file)
    results = []

    tree, synerrs = utils.tolerant_parse_module(lines, True)
    utils.annotate_parents(tree)
    tree.parent = tree

    context = {
        "lines": lines,
         "tree": tree,
         "file": file,
    }

    for rule in get_rules(IGNORE, ONLY):
        results.extend(rule(context))

    for synerr in synerrs:
        if "triple-" in synerr[1]: continue
        if "invalid" in synerr[1]: continue
        if "string " in synerr[1]: continue

        results.append({
            "file": file,
            "line": synerr[0],
             "col": 1,
            "code": "E001",
             "msg": f"Syntax Error: {synerr[1]}"
        })

    return results


def scrutinize(file: str | Path) -> list[dict]:
    """Lint a file."""
    if _is_embedded_vendor(file): return []
    final  = []
    final += run_style_checks(file)
    final += run_flake_checks(file)
    final += run_darkian_checks(file)
    return sorted(final, key=lambda x: (x["line"], x["col"]))
