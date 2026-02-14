from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_drace(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "drace", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_strict_fix_passes_when_all_findings_are_fixable(tmp_path: Path):
    sample = tmp_path / "strict_pass.py"
    sample.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "",
                "a=1",
                "long_name =2",
                "bbb=   3",
                "cccc =4",
                "",
                "print(sys.version)",
                "print(os.name)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    proc = _run_drace("format", str(sample), "--strict-fix")
    assert proc.returncode == 0


def test_strict_fix_fails_when_findings_remain(tmp_path: Path):
    sample = tmp_path / "strict_fail.py"
    sample.write_text(
        "def broken(\n    return 1\n",
        encoding="utf-8",
    )

    proc = _run_drace("format", str(sample), "--strict-fix")
    assert proc.returncode == 1
    assert "strict-fix failed" in proc.stdout


def test_strict_fix_rejects_diff_mode(tmp_path: Path):
    sample = tmp_path / "strict_diff.py"
    sample.write_text("x=1\n", encoding="utf-8")

    proc = _run_drace("format", str(sample), "--strict-fix", "--diff")
    assert proc.returncode == 1
    assert "--strict-fix cannot be combined with --diff" in proc.stdout
