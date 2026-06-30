"""Release version helpers."""

from functools import lru_cache
from pathlib import Path


def _version_file_candidates() -> tuple[Path, ...]:
    """Return a tuple of Path objects representing potential VERSION file locations."""
    current_file = Path(__file__).resolve()
    return (
        current_file.parents[2] / "VERSION",
        current_file.parents[1] / "VERSION",
    )


@lru_cache(maxsize=1)
def get_release_version() -> str:
    """Return the application's runtime release version from the VERSION file."""
    for version_file in _version_file_candidates():
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
    candidates = ", ".join(str(path) for path in _version_file_candidates())
    raise RuntimeError(f"release VERSION file is missing; checked: {candidates}")
