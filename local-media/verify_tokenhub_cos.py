#!/usr/bin/env python3
"""Verify the configured COS credentials with a disposable object."""

from __future__ import annotations

import uuid

from tokenhub import _cos_client, configuration


def main() -> int:
    settings, missing = configuration()
    if missing:
        raise RuntimeError("Missing configuration: " + ", ".join(missing))

    client = _cos_client(settings)
    bucket = settings["TENCENT_COS_BUCKET"]
    key = f"media-app-input/connection-check-{uuid.uuid4().hex}.txt"
    try:
        client.put_object(Bucket=bucket, Key=key, Body=b"ok")
        response = client.get_object(Bucket=bucket, Key=key)
        if response["Body"].get_raw_stream().read() != b"ok":
            raise RuntimeError("COS returned unexpected content")
    finally:
        client.delete_object(Bucket=bucket, Key=key)

    print("COS upload, download, and cleanup succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
