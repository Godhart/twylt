from pathlib import Path
import tomllib
import twylt

EXPECTED_PACKAGE_VERSION = "1.1.1"

def test_release_version_is_consistent():
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as f:
        project_version = tomllib.load(f)["project"]["version"]

    assert project_version == EXPECTED_PACKAGE_VERSION
    assert twylt.__version__ == EXPECTED_PACKAGE_VERSION
    assert project_version == twylt.__version__


def test_release_documents_and_verifier_versions_are_current():
    root = Path(__file__).resolve().parents[1]
    assert (root / "README.md").read_text(encoding="utf-8").splitlines()[0] == "# TWYLT 1.1.1"
    assert (root / "TWYLT.md").read_text(encoding="utf-8").splitlines()[0] == "# TWYLT 1.8"
    verifier = (root / "scripts" / "verify_package.py").read_text(encoding="utf-8")
    assert "twylt.__version__=='1.1.1'" in verifier


def test_mit_license_is_declared_and_present():
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as f:
        project = tomllib.load(f)["project"]
    assert project["license"] == {"file": "LICENSE"}
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License\n")
    assert "Permission is hereby granted, free of charge" in license_text
