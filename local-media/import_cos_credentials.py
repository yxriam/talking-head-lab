#!/usr/bin/env python3
"""Import a Tencent CAM credential CSV without printing secret values."""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path


KEY_MAP = {
    "SecretId": "TENCENT_COS_SECRET_ID",
    "SecretKey": "TENCENT_COS_SECRET_KEY",
}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: import_cos_credentials.py <credentials.csv> <env-file>", file=sys.stderr)
        return 2

    csv_path, env_path = map(Path, sys.argv[1:])
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        row = next(csv.DictReader(source), None)

    if not row or any(not row.get(column, "").strip() for column in KEY_MAP):
        print("credential CSV is missing SecretId or SecretKey", file=sys.stderr)
        return 1

    existing = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    replacements = {env_name: row[csv_name].strip() for csv_name, env_name in KEY_MAP.items()}
    written: set[str] = set()
    output: list[str] = []

    for line in existing:
        name = line.split("=", 1)[0] if "=" in line else ""
        if name in replacements:
            output.append(f"{name}={replacements[name]}")
            written.add(name)
        else:
            output.append(line)

    for name, value in replacements.items():
        if name not in written:
            output.append(f"{name}={value}")

    env_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    os.chmod(env_path, 0o600)
    print("Imported TENCENT_COS_SECRET_ID and TENCENT_COS_SECRET_KEY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
