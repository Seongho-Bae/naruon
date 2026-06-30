import inspect

from backend.core import version


def test_backend_version_docstrings_are_complete() -> None:
    assert inspect.getdoc(version) == "Release version helpers."
    assert inspect.getdoc(version._version_file_candidates)
    assert inspect.getdoc(version.get_release_version)
