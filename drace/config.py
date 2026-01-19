"""
This module provides the configuration interface for Drace —
both as a command-line utility and an interactive USSD-like
menu. It supports setting, resetting, and retrieving
persistent user-defined options for Drace's behavior.

Key Features:
- Persistent config management via a JSON file
- CLI commands to view, update, or reset individual or all
  config options
- USSD-style interactive interface for ease of use
- Supports type-aware casting, list manipulation
  (add/remove), and safe validation

Functions:
- config_cmd: Entry point for handling config commands from
  CLI
- sanitize_args: Parses and normalizes CLI arguments
- interactive: Interactive USSD-like interface for setting
  config options
- _handle_list: Handles list config operations (+ append, -
  remove)
- list_items, choose, transmit, etc. assist in formatting and
  interaction

Classes:
- Config: Manages loading, saving, setting, and resetting of
          config values

Notes:
- The term 'hapana' (Shona for "nothing") is used internally
  to represent a placeholder value in scenarios where no
  explicit value is given.

This module is designed to be user-friendly, flexible, and
forgiving — in line with Drace's pragmatic philosophy.
"""
# ========================= STANDARDS =======================
from typing import NoReturn
import json
import sys
import os
import re

# ======================= THIRD-PARTIES =====================
from tuikit.listools import list_items, choose, pick_from
from tuikit.logictools import any_eq, any_in
from tuikit.textools import strip_ansi

# ========================== LOCALS =========================
from .utils import APP_COLOR, YELLOW, GOOD, BAD, CURSOR, CMDS
from .utils import DEFAULTS_PATH, transmit, center, color
from .docs import config as doc
from .utils import underline
from . import help_menu


__doc__  = doc  # override for calls
DEFAULTS = {
    "mode":          [str, "lint"],
    "line_len":      [int, 79],
    "max_fn_steps":  [int, 6],
    "max_coupling":  [int, 3],
    "wrap":          [bool, True],
    "color":         [bool, True],
    "score":         [bool, True],
    "only_rules":    [list, None],
    "ignored_rules": [list, None],
    "ignored_files": [list, None],
    "delay":         [float, 0.01]
}


class Config:
    """
    Handles persistent user configuration for Drace.

    Loads, sets, and resets user-defined settings. Values are
    saved to a JSON file (`DEFAULTS_PATH`), and changes are
    applied instantly.

    This class is tightly integrated with the CLI and
    USSD-style interface.

    Attributes:
        path (str): Path to the config file.
        defaults (dict): The current active defaults.
    """
    def __init__(self):
        """Initializes the config system by loading existing or default values."""
        self.path     = DEFAULTS_PATH
        self.defaults = self._load()

    def _load(self) -> dict:
        """
        Loads config from file. If it doesn't exist, calls
        `reset()` to generate default values.

        Returns:
            dict: The active configurations
        """
        if os.path.exists(self.path):
            with open(self.path) as f: return json.load(f)

        self.reset()
        return self.defaults

    def _save(self) -> None:
        """Persists the current defaults to json."""
        with open(self.path, 'w') as f:
            json.dump(self.defaults, f)

    def set(self, key: str, value: int | float | bool | list):
        """
        Sets a config value and saves to json.

        Args:
            key (str): The config key
            value (int|float|bool|list): The new value to
                                         assign
        """
        self.defaults[key] = value
        self._save()

    def get(self, key: str, fallback=None
           ) -> int | float | bool | list | None:
        """
        Retrieves a config value.

        Args:
            key (str): The config key.
            fallback: Optional value to return if key doesn't
                      exist

        Returns:
            Any: The config value or fallback.
        """
        return self.defaults.get(key, fallback)

    def reset(self, target: str = "hapana"):
        """
        Resets one or all config values to their defaults.

        Args:
            target (str): The key to reset, or "hapana"/"all"
                          to reset everything
        """
        if target and not any_eq("hapana", "all", eq=target):
            if target not in DEFAULTS:
                transmit(f"unknown reset target: {target}\n")
                return
            self.defaults[target] = DEFAULTS[target][1]
        else:
            defaults = {}
            for k, v in DEFAULTS.items(): defaults[k] = v[1]
            self.defaults = defaults
        self._save()


def sanitize_args(args) -> list[str] | NoReturn:
    """
    Normalizes and interprets CLI arguments for `drace
    config`.

    Handles flexible separators (`=`, `:`, `+`, `-`) and
    reconstructs input into a standard [key, value(s)]
    format. Also simulates modifier flags (`+`, `-`) by
    appending them to `sys.argv` for later checks.

    Special handling for:
      - Single argument lookups (e.g. `drace config wrap`)
      - Key-only commands like `reset`, `show`, `list`, and
        `help`
      - Embedded separators (e.g. `line_len=100`,
        `ignored_rules+Z100`)
      - Gracefully handles unknown keys with user feedback

    'hapana' is used as a placeholder value when only a key
    is passed (e.g. `drace config line_len`) to differentiate
    it from `None` or other falsy values — since those might
    be valid defaults. This allows `config_cmd()` to detect
    intent (like showing a value) without conflict.

    Args:
        args (list): Raw CLI arguments passed to the config
                     command

    Returns:
        list: A cleaned list of [key, value(s)] or control
              command
    """
    sep = ["=", ":", "+", "-"]

    if args:
        if len(args) > 2:
            clean = [args[0]]
            if any_in(sep, eq=args[1]):
                if len(args) > 3: clean.append(args[2:])
                else: clean.append(args[2])
            else: clean.append(args[1:])
            args = clean
        elif len(args) == 2:
            clean = []
            for arg in args:
                # allow for an arbitrary number of separators
                for s in sep:
                    if s in arg:
                        sys.argv.append(s)
                        s  *= arg.count(s)
                        arg = arg.replace(s, "")
                clean.append(arg)
            args = clean
        else:
            if any_in(sep, eq=args[0]):
                # allow for an arbitrary number of separators
                sep[0] *= max(args[0].count("="), 1)
                sep[1] *= max(args[0].count(":"), 1)
                pattern = "|".join(map(re.escape, sep)) \
                        + r"|\s+"
                args    = re.split(pattern, args[0])
            else:
                extras = ["reset", "show", "list", "help"]
                args   = args[0]
                if args not in config.defaults:
                    if args not in extras:
                        transmit(f"unknown key: {args}\n",
                                  BAD)
                        sys.exit(1)
                args = [args, "hapana"]

        if isinstance(args[1], str):
            args[1] = args[1].split()
            if len(args[1]) == 1: args[1] = args[1][0]

    return args


def interactive() -> list[str] | NoReturn:
    """
    Launches an interactive USSD-like menu for configuring
    Drace defaults.

    Prompts the user to select a config option and input a
    new value.

    Displays current value and hints. Gracefully handle
    exits (via Ctrl+C, Ctrl+D, or explicit "Back" choice).

    Returns a list containing the selected config key and its
    new value.
    """
    head = center("《 DRACE CONFIG 》", "=", GOOD, APP_COLOR)
    print(f"\n{head}")

    cmd = color("drace config reset", YELLOW)
    transmit(f"use {cmd} to restore defaults\n")

    # list keys USSD-style and get choice
    list_items(DEFAULTS, guide="Choose option to change")
    choice = choose(DEFAULTS, getch=True, src=interactive,
             hue=APP_COLOR)

    if choice is None: print(); sys.exit(0)

    # retrieve value and present to user
    option   = pick_from(DEFAULTS.keys(), choice)
    value    = config.get(option)
    key, val = color(option, GOOD), color(value, YELLOW)
    message  = f"{key} ::: {val} ::: New value:"
    transmit(message)

    try: new = input(CURSOR).strip()
    except (KeyboardInterrupt, EOFError) as e:
        if isinstance(e, EOFError): print()
        sys.exit(1)
    finally: underline(hue=APP_COLOR, alone=True)

    return [option, new]


def _handle_list(key: str, values: tuple[str | list]
                ) -> list[str] | None:
    """
    Handles list-type config value manipulation (set, add,
    remove).

    Determines whether to:
      - replace the entire list,
      - append new values (if '+' present in sys.argv),
      - remove specified values (if '-' present in sys.argv)

    Args:
        key (str): The config key being modified
        values (list): The new value(s) passed from CLI input

    Returns:
        list | None: The updated list for the given key, or
                     None if resulting list is empty

    Notes:
        - Values are extended or removed based on presence of
          '+' or '-' in sys.argv
        - If the final list contains only one empty string,
          it's interpreted as None
    """
    if isinstance(values[0], str): value = list(values)
    else: value = values[0]

    array = config.get(key) or []

    if "+" in " ".join(sys.argv):  # append
        array.extend(value)
    elif "-" in " ".join(sys.argv):  # remove
        for val in values:
            try: array.remove(val)
            except ValueError: pass
    else: array = value  # override

    if len(array) == 1 and not array[0]: array = None
    if array is not None:
        for i, value in enumerate(array):
            if os.sep in value:
                value = value.split(os.sep)[-1]
            array[i] = value

    return array


def config_cmd(args: list[str] | list) -> None:
    """
    Handles configuration commands for Drace via C9LI or
    interactive prompt.

    Supports viewing, modifying, and resetting user-defined
    configuration options. The function also handles
    displaying help information, listing all current config
    values, and updating individual keys.

    Args:
        args (list[str] | list): Command-line arguments
            passed to `drace config`. If empty or None,
            launches the interactive config menu.

    Supported commands:
        - <key> <value>         Set the value of a config key
        - <key> = <value>       Alternative way to set a
                                value
        - <key> + <value>       Add to list-type config
                                values
        - <key> - <value>       Remove from list-type config
                                values
        - list                  Show all current config
                                values
        - show <key>            Show value of a specific
                                config key
        - reset <key|all>       Reset a key or all config
                                values to defaults
        - help                  how help menu

    Notes:
        - Handles type conversion based on the expected type
          for each key.
        - Allows multiple input styles and separators (e.g.,
          "key ::: value").
        - List-type configs can be modified incrementally.
        - Ignores case for boolean values ("yes", "on", etc)
    """
    def list_all(args: list[str]) -> bool:
        for cmd in ["list"] + list(config.defaults.keys()):
            if args[0] == cmd and args[1] == "hapana":
                return True
        return False

    if not args: args = interactive()

    args = sanitize_args(args)

    if list_all(args):
        transmit("config:")
        for k, v in config.defaults.items():
            s = ":" * (25 - len(k))
            k = color(k, GOOD)
            v = color(v, YELLOW)
            if args and args[0] != "list":
                if args[0] == strip_ansi(k):
                    transmit(f"{k} ::: {v}\n", _list=True)
                    return
            else: transmit(f"{k} {s} {v}", _list=True)
        print(); return

    if args[0] == "help": help_menu.main("config")
    if args[0] == "reset": config.reset(args[1]); return

    if args[0] == "show":
        try:
            key   = color(args[1], GOOD)
            value = config.get(args[1])
            transmit(f"{key} ::: {color(value, YELLOW)}\n")
        except KeyError:
            transmit(f"Unknown key: {args[1]}\n", BAD)
        return

    key, *values = args

    key = key.strip()
    if key not in DEFAULTS:
        transmit(f"unknown key: {key}\n", BAD)
        return

    _type    = DEFAULTS[key][0]
    truthy   = ["1", "true", "yeah", "yes", "y", "on", "ok"]
    exp_list = ""
    try:
        if _type == bool: value = values[0].lower() in truthy
        elif _type == list: value = _handle_list(key, values)
        else:
            if _type == str and values[0] not in CMDS:
                exp_list += ", ".join(CMDS[:-1])
                exp_list += ", or " + CMDS[-1]
                raise ValueError
            value = _type(values[0])
    except (IndexError, ValueError, TypeError):
        transmit(f"Invalid value for {key}. Expected "
               + f"{exp_list or _type.__name__}\n", BAD)
        return

    config.set(key, value)


config = Config()
