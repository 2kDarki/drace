from pathlib import Path
import subprocess
import sys

from drace import config as config_module


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_drace(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "drace", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_help_flag_shows_custom_help():
    proc = _run_drace("-h")
    assert proc.returncode == 0
    assert "《 DRACE HELP 》" in proc.stdout


def test_help_long_flag_shows_custom_help():
    proc = _run_drace("--help")
    assert proc.returncode == 0
    assert "《 DRACE HELP 》" in proc.stdout


def test_run_script_targets_drace_cli():
    content = (REPO_ROOT / "run.py").read_text(encoding="utf-8")
    assert "from drace.cli import main" in content


def test_sanitize_args_does_not_mutate_sys_argv(monkeypatch):
    fake_argv = ["python", "-m", "drace", "config", "ignored_rules+Z100"]
    monkeypatch.setattr(config_module.sys, "argv", list(fake_argv))

    _args, op = config_module.sanitize_args(["ignored_rules+Z100"])

    assert config_module.sys.argv == fake_argv
    assert op == "+"
