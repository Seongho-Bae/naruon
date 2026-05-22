from pathlib import Path
import re


def test_final_docker_image_does_not_install_build_dependencies():
    dockerfile = Path(__file__).resolve().parents[2] / "Dockerfile"
    dockerfile_text = dockerfile.read_text(encoding="utf-8")
    normalized_dockerfile = dockerfile_text.replace("\\\n", " ")

    for package_name in ("gcc", "libpq-dev"):
        assert not re.search(
            rf"\bapt-get\s+install\b[^;&\n]*\b{re.escape(package_name)}\b",
            normalized_dockerfile,
        )
