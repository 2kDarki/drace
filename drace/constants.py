from pathlib import Path
import json
import sys
import os

from tuikit.textools import style_text as color
from tuikit.logictools import any_eq


DEFAULTS_PATH = Path(__file__).parent / "defaults.json"
if os.path.exists(DEFAULTS_PATH):
    with open(DEFAULTS_PATH) as f: defaults = json.load(f)
else: defaults = {}

COLOR = defaults.get("color", True)
if "--color" in sys.argv: COLOR = not COLOR

MODES         = ["lint", "format", "score"]
MODE          = sys.argv[1] if any_eq(MODES, sys.argv[1:]) \
           else defaults.get("mode", "lint")
ONLY          = defaults.get("only_rules",    None) or []
IGNORED_RULES = defaults.get("ignored_rules", None) or []
IGNORED_FILES = defaults.get("ignored_files", None) or []
SCORE         = defaults.get("score", True)
WRAP          = defaults.get("wrap",  True)
MAX_COUPLING  = defaults.get("max_coupling", 8)
MAX_STEPS     = defaults.get("max_fn_steps", 6)
LINE_LEN      = defaults.get("line_len",    88)
SPEED         = defaults.get("delay",     0.01)
HOLD          = 0.05
WHITE         = "white"
YELLOW        = "yellow" if COLOR else WHITE
GOOD          = "green" if COLOR else WHITE
BAD           = "red" if COLOR else WHITE
PROMPT        = "cyan" if COLOR else WHITE
APP_COLOR     = "magenta" if COLOR else WHITE
APP           = "[drace]"
INDENT        = len(APP) + 1
DRACE         = color(f"{APP} ", APP_COLOR)
CURSOR        = color(" " * (INDENT - 4) + ">>> ", APP_COLOR)
SEP           = color(":", PROMPT)
CMDS          = MODES + ["config"]
KEYWORDS      = ("if ", "for ", "while ", "with ", "elif ",
                 "else:", "try:", "except ", "finally:")


def override(args):
    if "--score" in sys.argv: args.score = not SCORE
    return args
