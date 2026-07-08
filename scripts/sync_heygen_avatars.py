#!/usr/bin/env python3
"""Fetch HeyGen avatar metadata and merge heygen_name into config/avatars.json."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from services.avatar_registry import config_path, merge_api_names

HEYGEN_BASE = os.getenv("HEYGEN_BASE_URL", "https://api.heygen.com").rstrip("/")


def fetch_api_avatars(api_key: str) -> list[dict]:
    url = f"{HEYGEN_BASE}/v2/avatars"
    req = urllib.request.Request(
        url,
        headers={"X-Api-Key": api_key, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HeyGen API error ({exc.code}): {raw}") from exc

    if body.get("error"):
        err = body["error"]
        raise RuntimeError(err.get("message") or str(err))

    data = body.get("data") or {}
    avatars = data.get("avatars") or data.get("avatar_list") or []
    if not isinstance(avatars, list):
        raise RuntimeError(f"Unexpected avatars payload: {body}")
    return avatars


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("HEYGEN_API_KEY", "").strip()
    if not api_key:
        print("HEYGEN_API_KEY is not set.", file=sys.stderr)
        return 1

    path = config_path()
    if not path.is_file():
        print(f"Avatar config not found: {path}", file=sys.stderr)
        return 1

    print(f"Syncing avatar metadata into {path} ...")
    api_avatars = fetch_api_avatars(api_key)
    summary = merge_api_names(api_avatars)
    print(
        f"Done. total={summary['total']} updated={summary['updated']} "
        f"missing_from_api={summary['missing']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
