"""Interactive help screens for Drace CLI and config commands."""
# ========================= STANDARDS =======================
import sys

# ======================= THIRD-PARTIES =====================
from tuikit.logictools import any_in

# ========================== LOCALS =========================
from .utils import GOOD, APP_COLOR, center, wrap_text, color
from .utils import underline


def main(to: str | None = None):
    """Render Drace help screens and exit cleanly."""
    def heading():
        print(f"\n{header}\n")

    head   = f" {to.upper()} " if to is not None else " "
    header = center(f"《 DRACE{head}HELP 》", "=", APP_COLOR,
             GOOD)

    if to:
        heading()
        if to == "config": config()
    else:
        desc = drace(heading)
        if desc is not None: return desc

    underline(hue=GOOD, alone=True)
    sys.exit(0)


def drace(heading):
    """Render the main CLI help text when a help flag is present."""
    if not any_in("-h", "--help", "-help", eq=sys.argv): return ""
    heading()
    score_help = wrap_text(
        "Toggle score after linting or formatting; relative to default set",
        18,
        inline=True,
        order="                  ",
    )
    color_help = wrap_text(
        "Toggle colorized output; relative to default set",
        18,
        inline=True,
        order="                  ",
    )
    diff_help = wrap_text(
        "Show diff instead of modifying files (used with format)",
        18,
        inline=True,
        order="                  ",
    )
    strict_help = wrap_text(
        "Fail if findings remain after format (CI gate; format only)",
        18,
        inline=True,
        order="                  ",
    )
    help_help = wrap_text(
        "Show this help message and exit",
        18,
        inline=True,
        order="                  ",
    )
    notes_1 = wrap_text(
        "• Cross-file analysis, resilience to syntax errors, and rule "
        "flexibility are part of Drace’s core goals.",
        2,
    )
    notes_2 = wrap_text(
        "• Defaults are user-friendly and can be fine-tuned in seconds.",
        2,
    )
    text = f"""Usage:
    drace [command] [options] <path>

Commands:

1. lint
    {wrap_text(
        "Lint Python files and show potential issues, suggestions, or design "
        "improvements.",
        3,
        3,
    )}
   Example: drace lint src/

2. format
{wrap_text("Format Python files using Drace’s code styling rules.", 3, 3)}
   Example: drace format myfile.py --diff

3. score
{wrap_text("Calculate a linting score based on rules triggered.", 3, 3)}
   Example: drace score .

4. config
{wrap_text("Configure defaults either interactively or via command line.", 3, 3)}
{wrap_text("Example: drace config line_len 100", 3, 3)}
{wrap_text("Example: drace config (opens interactive mode)", 3, 3)}

Common Options:

  --score         {score_help}
  --color         {color_help}
  --diff          {diff_help}
  --strict-fix    {strict_help}
  -h, --help      {help_help}

Config Usage:
    drace config help

Notes:
{notes_1}
{notes_2}

Docs:
    README.md
    docs/README.md"""
    print(text)


def config():
    """Render detailed help for `drace config`."""
    # ============ SECTION 1: CHANGING DEFAULTS =============
    print(color("Changing defaults", "", "", True, True))

    # subsection 1: format
    print(color("\n  1. Formats:", GOOD))
    print("   • drace config key value")
    print("   • drace config key=value")
    print("   • drace config key = value")
    print("   • drace config key:value")
    print("   • drace config key : value")
    print("   • drace config key + value (appends to list)")
    print("   • drace config key - value (remove from list)")

    # subsection 2: examples
    print(color("\n  2. Examples:", GOOD))
    print("   • drace config line_len 59")
    print("   • drace config color :: on")
    print("   • drace config score====yes")
    print("   • drace config ignored_rules + Z100 Z200...\n")

    # ============ SECTION 2: RESETTING DEFAULTS ============
    print(color("Resetting defaults", "", "", True, True))

    # subsection 1: format
    print(color("\n  1. Formats:", GOOD))
    print("   • drace config reset      Restore defaults")
    print("   • drace config reset all  Same as above")
    print("   • drace config reset key  Reset one key")

    # subsection 2: examples
    print(color("\n  2. Examples:", GOOD))
    print("   • drace config reset")
    print("   • drace config reset all")
    print("   • drace config reset wrap\n")

    # ============= SECTION 3: VIEWING DEFAULTS =============
    print(color("Viewing defaults", "", "", True, True))

    # subsection 1: format
    print(color("\n  1. Formats:", GOOD))
    print("   • drace config list       List all defaults")
    print("   • drace config key        Show one default")
    print("   • drace config show key   Same as above")

    # subsection 2: examples
    print(color("\n  2. Examples:", GOOD))
    print("   • drace config list")
    print("   • drace config line_len")
    print("   • drace config show line_len\n")

    # ============= SECTION 4: INTERACTIVE MODE =============
    print(color("Interactive mode", "", "", True, True))

    # subsection 1: format
    print(color("\n  1. Format:", GOOD))
    print("   • drace config")

    # subsection 2: info
    print(color("\n  2. Info:", GOOD))
    print(wrap_text(
        "• Opens a USSD-style interactive menu to set defaults",
        5,
        3,
    ))
    print(wrap_text(
        "• The setting rules in <Changing defaults> apply here, except "
        "you don't have to include the key:\n",
        5,
        3,
    ))
    print(wrap_text(
        "   >>> + Z100 Z200  # if you had chosen ignored_rules and wanted "
        "to append more rules\n",
        24,
        3,
    ))

    # ============= SECTION 4: INTERACTIVE MODE =============
    print(color("Notes:", "", "", True, True))

    print(wrap_text(
        "• if '-' or '+' is not found when setting a list default "
        "it will be overridden",
        5,
        3,
    ))
