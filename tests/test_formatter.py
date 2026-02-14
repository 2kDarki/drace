from pathlib import Path
import re

from drace.reporters import formatting


def test_format_write_mode_applies_import_order_and_assignment_alignment(
    tmp_path: Path, monkeypatch
):
    sample = tmp_path / "sample.py"
    sample.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "import localmod",
                "from .pkg import util",
                "",
                "a=1",
                "long_name =2",
                "bbb=   3",
                "cccc =4",
                "",
                "print(sys.version)",
                "print(os.name)",
                "print(localmod)",
                "print(util)",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(formatting, "transmit", lambda *args, **kwargs: None)
    changed = formatting.format_cmd(sample, diff=False, score=False)
    assert changed == 1

    expected = "\n".join(
        [
            "import sys",
            "import os",
            "",
            "from .pkg import util",
            "import localmod",
            "",
            "a         = 1",
            "long_name = 2",
            "bbb       = 3",
            "cccc      = 4",
            "",
            "print(sys.version)",
            "print(os.name)",
            "print(localmod)",
            "print(util)",
        ]
    )
    assert sample.read_text(encoding="utf-8") == expected


def test_format_diff_mode_shows_patch_without_writing(tmp_path: Path, monkeypatch, capsys):
    sample = tmp_path / "sample.py"
    original = "a=1\nlong_name =2\nbbb=   3\ncccc =4\n"
    sample.write_text(original, encoding="utf-8")

    monkeypatch.setattr(formatting, "COLOR", False)
    changed = formatting.format_cmd(sample, diff=True, score=False)
    out = capsys.readouterr().out

    assert changed == 1
    assert "--- a/" in out
    assert "+++ b/" in out
    assert "would change" in out
    assert sample.read_text(encoding="utf-8") == original


def test_format_diff_score_has_no_extra_blank_line(tmp_path: Path, monkeypatch, capsys):
    sample = tmp_path / "sample.py"
    sample.write_text("x=1\ny=2\nz =3\nwwww = 4\n", encoding="utf-8")

    monkeypatch.setattr(formatting, "COLOR", False)
    formatting.format_cmd(sample, diff=True, score=True)
    out = capsys.readouterr().out
    plain = re.sub(r"\x1b\[[0-9;]*m", "", out)

    done_idx = plain.index("would change")
    code_idx = plain.index("code ")
    between = plain[done_idx:code_idx]
    assert "\n\n\n" not in between


def test_diff_colors_follow_toggle(tmp_path: Path, monkeypatch, capsys):
    sample = tmp_path / "sample.py"
    sample.write_text("a=1\nb=2\nc=3\nd =4\n", encoding="utf-8")

    monkeypatch.setattr(formatting, "transmit", lambda *args, **kwargs: None)
    monkeypatch.setattr(formatting, "COLOR", True)
    monkeypatch.setattr(
        formatting,
        "color",
        lambda text, hue, *args, **kwargs: f"<{hue}>{text}</{hue}>",
    )
    formatting.format_cmd(sample, diff=True, score=False)
    out = capsys.readouterr().out
    assert "<green>+" in out or "<red>-" in out


def test_format_noop_returns_zero(tmp_path: Path, monkeypatch):
    sample = tmp_path / "sample.py"
    source = "x = 1\ny = 2\nz = 3\n"
    sample.write_text(source, encoding="utf-8")

    monkeypatch.setattr(formatting, "transmit", lambda *args, **kwargs: None)
    changed = formatting.format_cmd(sample, diff=False, score=False)

    assert changed == 0
    assert sample.read_text(encoding="utf-8") == source


def test_formatter_uses_discovered_rules_and_fixers(tmp_path: Path, monkeypatch):
    sample = tmp_path / "sample.py"
    sample.write_text("a=1\nb=2\n", encoding="utf-8")

    def fake_rule(context):
        return [
            {
                "file": context["file"],
                "line": 1,
                "col": 1,
                "code": "Z900",
                "msg": "rule-generated fix",
                "fix": {
                    "op": "replace_line",
                    "line": 1,
                    "content": "a = 1",
                },
            }
        ]

    def fake_fixer(_context):
        return [
            {
                "op": "replace_line",
                "line": 2,
                "content": "b = 2",
            }
        ]

    monkeypatch.setattr(formatting, "transmit", lambda *args, **kwargs: None)
    monkeypatch.setattr(formatting, "get_rules", lambda *_args: [fake_rule])
    monkeypatch.setattr(formatting, "get_fixers", lambda *_args: [fake_fixer])

    changed = formatting.format_cmd(sample, diff=False, score=False)
    assert changed == 1
    assert sample.read_text(encoding="utf-8") == "a = 1\nb = 2\n"
