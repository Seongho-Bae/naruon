from pathlib import Path
import subprocess
import sys

def test_backend_version_docstring_gate_passes() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    results = []

    # Try different python executables to find interrogate
    for exe in [sys.executable, "python3", "python"]:
        result = subprocess.run(
            [
                exe,
                "-m",
                "interrogate",
                "--fail-under=100",
                "core/version.py",
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        results.append(result)
        if result.returncode == 0:
            break

    assert any(result.returncode == 0 for result in results), "\n".join(
        result.stdout + result.stderr for result in results
    )
