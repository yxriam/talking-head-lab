#!/usr/bin/env python3
"""Import one secret from a file into an env file without printing its value."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ALLOWED_NAMES = {"TOKENHUB_API_KEY", "TRUTHSCAN_API_KEY"}


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in ALLOWED_NAMES:
        print("usage: import_env_secret.py TOKENHUB_API_KEY <secret-file> <env-file>", file=sys.stderr)
        return 2

    name = sys.argv[1]
    secret = Path(sys.argv[2]).read_text(encoding="utf-8-sig").strip()
    env_path = Path(sys.argv[3])
    if secret.startswith(f"{name}="):
        secret = secret.split("=", 1)[1].strip()
    if not secret or "\n" in secret or "\r" in secret:
        print("secret file must contain exactly one non-empty line", file=sys.stderr)
        return 1

    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    replacement = f"{name}={secret}"
    output: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"{name}="):
            output.append(replacement)
            replaced = True
        else:
            output.append(line)
    if not replaced:
        output.append(replacement)

    env_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    os.chmod(env_path, 0o600)
    print(f"Imported {name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
