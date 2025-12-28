from tuikit.textools import Align, wrap_text


def wrap(doc: str, indent: int = 2) -> str:
    return wrap_text(doc, indent, inline=True, order="   ",
           sub_indent=4)


center = Align(offset=4).center

# ========================== KITTY ==========================
drace = f"""
{wrap("Drace is a pragmatic Python linter and formatter that blends opinionated style with practical analysis to help you write cleaner, more maintainable code.", 0)}

{wrap("Unlike traditional tools that crash on invalid syntax or blindly follow style guides, Drace is resilient, human-aware, and configurable — built with the philosophy of The Pragmatic Programmer at its core.", 0)}

Key Features:
{wrap("- Custom rule system (e.g. Z-series) with AST and token-based checks.")}
{wrap("- Formatter designed to work with the linter to support autofixing.")}
{wrap("- Human-friendly output: colored, aligned, and readable by default.")}
{wrap("- Config system that's intuitive for both technical and non-technical users.")}
{wrap("- CLI and interactive (USSD-style) interfaces.")}
{wrap("- Handles fatal syntax errors gracefully — doesn't crash like flake8/black.")}
{wrap("- Cross-file analysis support (e.g. for DRY violations).")}

Philosophy:
{wrap("Drace values clarity over blind convention, balancing PEP8 compliance with real-world code pragmatism. It's ideal for devs who want tooling that thinks with them, not for them.", 0)}
"""

# =========================== CLI ===========================
cli = f"""{center(" CLI ", "=")}\n
{wrap("This module defines the command-line interface for Drace. It handles argument parsing and dispatches execution to the appropriate command module based on user input.", 0)}

Commands:
{wrap("- drace format <path>: Format code and optionally show a diff")}
{wrap("- drace lint <path>: Lint Python files and display suggestions or warnings")}
{wrap("- drace score <path>: Compute and display a score based on linting results")}
{wrap("- drace config [args]: Configure default settings interactively or via command arguments")}

Example usage:
    drace -h/--help
    drace lint project/
    drace format script.py --diff
    drace config line_len 100
"""

# ========================= CONFIG ==========================
config = f"""{center(" CONFIG ", "=")}\n
{wrap("This module provides the configuration interface for Drace — both as a command-line utility and an interactive USSD-like menu. It supports setting, resetting, and retrieving persistent user-defined options for Drace's behavior", 0)}

Key Features:
{wrap("- Persistent config management via a JSON file")}
{wrap("- CLI commands to view, update, or reset individual or all config options")}
{wrap("- USSD-style interactive interface for ease of use")}
{wrap("- Supports type-aware casting, list manipulation (add/remove), and safe validation")}

Functions:
{wrap("- config_cmd: Entry point for handling config commands from CLI")}
{wrap("- sanitize_args: Parses and normalizes CLI arguments")}
{wrap("- interactive: Interactive USSD-like interface for setting config options")}
{wrap("- _handle_list: Handles list config operations (+ append, - remove)")}
{wrap("- list_items, choose, transmit, etc. assist in formatting and interaction")}

Classes:
{wrap("- Config: Manages loading, saving, setting, and resetting of config values")}

Notes:
{wrap("- The term 'hapana' (Shona for 'nothing') is used internally to represent a placeholder value in scenarios where no explicit value is given")}

{wrap("This module is designed to be user-friendly, flexible, and forgiving — in line with Drace's pragmatic philosophy", 0)}
"""
