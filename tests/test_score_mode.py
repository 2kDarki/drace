from pathlib import Path

from drace.reporters import linting


def test_score_mode_is_silent_except_score(monkeypatch, capsys, tmp_path: Path):
    sample = tmp_path / "sample.py"
    sample.write_text("if True:\n    pass\n", encoding="utf-8")

    monkeypatch.setattr(linting, "MODE", "score")
    linting.SCORE = 0
    linting.FILES = 0
    linting.CODES = set()

    linting.lint_cmd(str(sample), score=True, first=True, done=True)
    out = capsys.readouterr().out

    assert "sample.py:" not in out
    assert "Z200" not in out
    assert "code " in out
