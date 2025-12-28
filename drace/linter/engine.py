# ===================== STANDARDS ======================
from pathlib import Path
import io

# ======================= LOCALS =======================
from .pyflakes import reporter as flake_reporter
from drace.constants import IGNORED_RULES
from .pyflakes import api as flake_api
from drace.darkian import get_rules
from .pycodestyle import Checker
from drace import utils


IGNORE = ("E113", "E121", "E124", "E126", "E127", "E128", 
          "E131", "E221", "E701", "E702", "E704") \
       + tuple(IGNORED_RULES)


def run_style_checks(file: str | Path) -> list[dict]:
    """Run Darkian-patched pycodestyle checks on a file"""
    file = str(file)

    # Build checker and capture final
    checker = Checker(file)
    checker.check_all()

    final = []
    for line, col, code, msg in checker.report.errors:
        if code in IGNORE: continue
        final.append({
            "file": file,
            "line": line,
             "col": col,
            "code": code,
             "msg": " ".join(msg.strip().split()[1:])
        })
    return final


def run_flake_checks(file: str | Path) -> list[dict]:
    """Run pyflakes checks on a file"""
    def format_flake(msg: str) -> tuple[str]:
        code = "Z999"
        if "imported but unused" in msg: code = "W611"
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
        if "syntax error" in msg.lower(): code = "E001"
        if "*' used; unable t" in msg: code = "F403"
        if "undefined name" in msg: code = "E602"
        if "but never used" in msg: code = "W612"
        if "f-string is" in msg: code = "F541"

        return code, msg

    buffer   = io.StringIO()
    reporter = flake_reporter.Reporter(buffer, buffer)
    flake_api.checkPath(str(file), reporter)

    final = []
    for line in buffer.getvalue().splitlines():
        parts = line.split(":", 3)[1:]
        if len(parts) == 3:
            lineno, col, msg = parts
            code, message    = format_flake(msg)
            if code in IGNORE: continue
            if "unexpected indent" in message: continue
            if "unterminated stri" in message: continue
            final.append({
                "file": file,
                "line": int(lineno.strip()),
                 "col": int(col.strip()),
                "code": code,
                 "msg": message
            })

    return final


def run_darkian_checks(file: str | Path) -> list[dict]:
    "Run Darkian checks on a file"
    lines         = Path(file).read_text(encoding="utf-8")\
                    .splitlines()
    file          = str(file)
    final         = []
    tree, synerrs = utils.tolerant_parse_module(lines, True)

    for rule in get_rules():
        result = rule(lines, tree, file)
        final.extend(result)

    for synerr in synerrs:
        if "triple-" in synerr[1]: continue
        if "invalid" in synerr[1]: continue
        if "string " in synerr[1]: continue
        final.append({
            "file": file,
            "line": synerr[0],
             "col": 1,
            "code": "E001",
             "msg": f"Syntax Error: {synerr[1]}"
        })

    return final


def scrutinize(file: str | Path) -> list[dict]:
    """Lint a file using pyflakes, pycodestyle, and darkian"""
    final  = []
    final += run_style_checks(file)
    final += run_flake_checks(file)
    final += run_darkian_checks(file)
    return sorted(final, key=lambda x: (x["line"], x["col"]))
