import subprocess
import sys
from pathlib import Path


def test_backend_version_docstring_gate_passes() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "interrogate",
            "--fail-under=100",
            "backend/core/version.py",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
