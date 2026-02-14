from tuikit.textools import Align, wrap_text


def wrap(doc: str, indent: int = 0) -> str:
    """Render wrapped prose that matches Drace's pydoc style."""
    return wrap_text(
        doc,
        indent,
        inline=True,
        order="   ",
        sub_indent=4,
    )


center = Align(offset=4).center


drace = f"""
{center(" DRACE ", "=")}

{wrap(
    "Drace is a pragmatic Python linter and formatter focused on readability, "
    "maintainability, and practical engineering feedback."
)}

{wrap(
    "The project combines style checks, semantic checks, and custom Darkian "
    "rules under one CLI so teams can lint, format, and score code with "
    "consistent behavior."
)}

Capabilities:
{wrap("- Linting pipeline that remains useful even when files contain syntax errors.", 2)}
{wrap("- Formatter that applies rule-provided fixes, including multi-line edits.", 2)}
{wrap("- Strict CI mode (--strict-fix) for non-zero exit when findings remain.", 2)}
{wrap("- Score mode for quick health snapshots across files or repositories.", 2)}
{wrap("- Config system for defaults such as line length, ignored files, and rule filters.", 2)}

Workflow:
{wrap("- Discover Python files from a file path or directory target.", 2)}
{wrap("- Run style + pyflakes + Darkian checks in one pass.", 2)}
{wrap("- Apply formatter fixes in stable bottom-up order over multiple passes.", 2)}
{wrap("- Report findings and/or scores with readable, aligned terminal output.", 2)}

Quick start:
    drace lint src/
    drace format src/ --diff
    drace format src/ --strict-fix
    drace score src/
    drace config list
"""


cli = f"""{center(" CLI ", "=")}\n
{wrap(
    "The CLI dispatches Drace commands and shares a consistent argument model "
    "for linting, formatting, scoring, and configuration."
)}

Commands:
{wrap("- drace lint <path> [--score] [--color]", 2)}
{wrap("- drace format <path> [--diff] [--score] [--strict-fix] [--color]", 2)}
{wrap("- drace score <path> [--color]", 2)}
{wrap("- drace config [args]", 2)}

Behavior:
{wrap("- If no command is provided, Drace uses the configured default mode.", 2)}
{wrap("- -h/--help show a single custom help screen for the tool.", 2)}
{wrap("- --color and --score behave as toggles relative to configured defaults.", 2)}
{wrap("- format --strict-fix fails when unresolved findings remain after format.", 2)}
{wrap("- format --strict-fix and --diff are mutually exclusive.", 2)}

Examples:
    drace -h
    drace lint src/
    drace format src/ --diff
    drace format src/ --strict-fix
    drace score src/
"""


config = f"""{center(" CONFIG ", "=")}\n
{wrap(
    "Drace configuration supports persistent defaults via JSON and a command "
    "interface that accepts both direct and interactive edits."
)}

Keys:
{wrap("- mode, line_len, max_fn_steps, max_coupling", 2)}
{wrap("- wrap, color, score", 2)}
{wrap("- only_rules, ignored_rules, ignored_files", 2)}
{wrap("- delay", 2)}

Operations:
{wrap("- List all values: drace config list", 2)}
{wrap("- Show one value: drace config <key> or drace config show <key>", 2)}
{wrap("- Set value: drace config <key> <value>", 2)}
{wrap("- Reset one/all: drace config reset <key|all>", 2)}
{wrap("- Interactive menu: drace config", 2)}

Separators:
{wrap("- Assignment separators: =, :, ::", 2)}
{wrap("- List modifiers: + (append), - (remove)", 2)}

Notes:
{wrap("- Changes are persisted immediately in drace/defaults.json.", 2)}
{wrap("- List updates normalize path fragments to stable leaf names.", 2)}
{wrap("- The placeholder token 'hapana' is used internally for key-only lookups.", 2)}
"""


engine = f"""{center(" ENGINE ", "=")}\n
{wrap(
    "Linting and formatting share Darkian discovery, tolerant parsing helpers, "
    "and repository-level file discovery."
)}

Lint stack:
{wrap("- Style checks (Darkian-patched pycodestyle)", 2)}
{wrap("- Pyflakes checks (mapped to Drace codes)", 2)}
{wrap("- Darkian rule checks (Z-series functions)", 2)}

Formatter stack:
{wrap("- Collect inline fixes from check_* findings", 2)}
{wrap("- Collect dedicated fixes_* functions", 2)}
{wrap("- Apply valid fix payloads over repeated passes until stable", 2)}

Filtering:
{wrap("- only_rules and ignored_rules filter both linter and formatter discovery.", 2)}
{wrap("- Embedded vendor paths are skipped from Drace findings by default.", 2)}
"""
