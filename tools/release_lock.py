#!/usr/bin/env python3
"""Return the frozen course image after validating student release metadata.

This check intentionally does not compare the current source-tree digest: student
submissions are expected to modify the starter. The internal release exporter
performs that source binding before the template is published.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


IMAGE_RE = re.compile(r"^[^\s]+@sha256:[0-9a-f]{64}$")
ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid .env line {number}")
        key, value = line.split("=", 1)
        key = key.strip()
        if key in values:
            raise ValueError(f"duplicate .env key: {key}")
        values[key] = value.strip()
    return values


def locked_image(root: Path = ROOT, expected_image: str = "") -> str:
    env_path = root / ".env"
    lock_path = root / "release.lock.json"
    if not env_path.is_file() or not lock_path.is_file():
        raise ValueError("release metadata is missing; contact the instructor")
    image = read_env(env_path).get("COURSE_IMAGE", "")
    if not IMAGE_RE.fullmatch(image):
        raise ValueError("COURSE_IMAGE is not an immutable manifest digest")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("image") != image:
        raise ValueError(".env and release.lock.json select different images")
    architectures = set(lock.get("validated_native_architectures", []))
    if not {"amd64", "arm64"}.issubset(architectures):
        raise ValueError("release lock does not record both native pilots")
    if expected_image and expected_image != image:
        raise ValueError("COURSE_IMAGE repository variable does not match the committed lock")
    return image


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--expected-image", default="")
    args = parser.parse_args(argv)
    try:
        print(locked_image(args.root, args.expected_image))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
