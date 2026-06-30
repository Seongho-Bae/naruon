import subprocess
import sys
from pathlib import Path


def _run_interrogate(executable: str, repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            executable,
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


def test_backend_version_docstring_gate_passes() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    results = [_run_interrogate(sys.executable, repo_root)]
    if results[0].returncode != 0 and "No module named interrogate" in results[0].stderr:
        results.append(_run_interrogate("python3", repo_root))

    assert any(result.returncode == 0 for result in results), "\n".join(
        result.stdout + result.stderr for result in results
    )
