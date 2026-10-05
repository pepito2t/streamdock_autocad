"""Keeps pyproject.toml and manifest.json on the same version, optionally matching a git tag."""

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
MANIFEST = ROOT / "com.tmbk.streamdock.autocad.sdPlugin" / "manifest.json"
TAG_PREFIX = "v"
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")


def read_versions() -> dict[str, str]:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"pyproject.toml": pyproject["project"]["version"], "manifest.json": manifest["Version"]}


def check(tag: str | None) -> None:
    versions = read_versions()
    expected = tag.removeprefix(TAG_PREFIX) if tag else next(iter(versions.values()))
    mismatched = {name: version for name, version in versions.items() if version != expected}
    if mismatched:
        details = ", ".join(f"{name}={version}" for name, version in mismatched.items())
        raise SystemExit(f"Version attendue {expected}, trouvé {details}")
    print(f"version {expected} ok")


def bump(version: str) -> None:
    if not VERSION_PATTERN.match(version):
        raise SystemExit(f"Version invalide : {version}")
    PYPROJECT.write_text(
        re.sub(r'^version = ".*"$', f'version = "{version}"', PYPROJECT.read_text(encoding="utf-8"), count=1, flags=re.M),
        encoding="utf-8",
    )
    MANIFEST.write_text(
        re.sub(r'"Version": ".*"', f'"Version": "{version}"', MANIFEST.read_text(encoding="utf-8"), count=1),
        encoding="utf-8",
    )
    print(f"version {version} écrite")


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--tag")
    bump_parser = commands.add_parser("bump")
    bump_parser.add_argument("version")
    args = parser.parse_args(argv)
    if args.command == "check":
        check(args.tag)
    else:
        bump(args.version)


if __name__ == "__main__":
    main(sys.argv[1:])
