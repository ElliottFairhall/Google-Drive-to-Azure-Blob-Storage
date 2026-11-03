"""Guard the dependency manifest against encoding damage."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_requirements_is_plain_utf8() -> None:
    """A UTF-16 file (NUL bytes) is unreadable to pip tooling and Dependabot."""
    raw = (ROOT / "requirements.txt").read_bytes()
    assert b"\x00" not in raw
    raw.decode("utf-8")


def test_requirements_pin_every_package_with_a_floor() -> None:
    """Each requirement names a minimum version."""
    lines = [
        line
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert lines
    assert all(">=" in line for line in lines), lines
