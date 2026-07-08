"""HeyGen avatar registry — loads look IDs from config/avatars.json."""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "avatars.json"

AVATAR_FIELDS = ("id", "label", "outfit", "pose", "enabled", "heygen_name", "holds_prop")


def config_path() -> Path:
    env_path = os.getenv("HEYGEN_AVATARS_CONFIG", "").strip()
    return Path(env_path) if env_path else DEFAULT_CONFIG_PATH


def _empty_entry(avatar_id: str) -> dict:
    return {
        "id": avatar_id,
        "label": "",
        "outfit": "",
        "pose": "",
        "enabled": True,
    }


def _avatars_from_env() -> list[dict]:
    raw = os.getenv("HEYGEN_AVATAR_IDS", "").strip()
    if not raw:
        return []
    return [_empty_entry(aid.strip()) for aid in raw.split(",") if aid.strip()]


def load_config() -> dict:
    path = config_path()
    if not path.is_file():
        return {"avatars": _avatars_from_env()}

    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid avatar config (expected object): {path}")

    avatars = data.get("avatars")
    if not isinstance(avatars, list):
        raise ValueError(f"Invalid avatar config (avatars must be a list): {path}")

    if avatars:
        return data
    return {"avatars": _avatars_from_env()}


def get_all_avatars() -> list[dict]:
    return list(load_config().get("avatars") or [])


def get_enabled_avatars() -> list[dict]:
    enabled: list[dict] = []
    for entry in get_all_avatars():
        if not entry.get("enabled", True):
            continue
        avatar_id = (entry.get("id") or "").strip()
        if avatar_id:
            enabled.append(entry)
    return enabled


def get_avatar_by_id(avatar_id: str) -> dict | None:
    avatar_id = (avatar_id or "").strip()
    if not avatar_id:
        return None
    for entry in get_all_avatars():
        if (entry.get("id") or "").strip() == avatar_id:
            return entry
    return None


def get_batch_avatar_ids() -> list[str]:
    """Enabled avatars for auto video batches — excludes prop-holding looks."""
    seen: set[str] = set()
    ids: list[str] = []
    for entry in get_enabled_avatars():
        if entry.get("holds_prop") is True:
            continue
        avatar_id = (entry.get("id") or "").strip()
        if avatar_id and avatar_id not in seen:
            seen.add(avatar_id)
            ids.append(avatar_id)
    return ids


def get_enabled_avatar_ids() -> list[str]:
    """Unique enabled avatar look IDs (first registry entry wins for duplicates)."""
    seen: set[str] = set()
    ids: list[str] = []
    for entry in get_enabled_avatars():
        avatar_id = (entry.get("id") or "").strip()
        if avatar_id and avatar_id not in seen:
            seen.add(avatar_id)
            ids.append(avatar_id)
    return ids


def get_avatar_id_for_index(index: int) -> str:
    ids = get_enabled_avatar_ids()
    if not ids:
        return ""
    return ids[index % len(ids)]


def get_random_avatar_id() -> str:
    ids = get_enabled_avatar_ids()
    if not ids:
        return ""
    return random.choice(ids)


def pick_unique_avatar_ids(count: int) -> list[str]:
    """
    Pick up to `count` unique avatar IDs for one product batch.
    Never repeats an ID until all unique avatars are used.
    Prop-holding avatars (holds_prop: true) are excluded from auto selection.
    """
    pool = get_batch_avatar_ids()
    if not pool:
        return [""] * count

    random.shuffle(pool)
    if len(pool) >= count:
        return pool[:count]

    picked = list(pool)
    while len(picked) < count:
        remaining = [aid for aid in pool if aid not in picked]
        if not remaining:
            remaining = pool
        picked.append(random.choice(remaining))
    return picked


def get_avatar_for_index(index: int) -> dict | None:
    avatars = get_enabled_avatars()
    if not avatars:
        return None
    return avatars[index % len(avatars)]


def is_configured() -> bool:
    return bool(get_enabled_avatars())


def save_config(config: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")


def merge_api_names(api_avatars: list[dict]) -> dict:
    """
    Merge HeyGen API avatar names into the registry without touching user fields.

    Returns summary counts: updated, missing.
    """
    by_id = {
        (item.get("avatar_id") or item.get("id") or "").strip(): item
        for item in api_avatars
        if (item.get("avatar_id") or item.get("id") or "").strip()
    }

    config = load_config()
    avatars = config.get("avatars") or []
    updated = 0
    missing = 0

    for entry in avatars:
        avatar_id = (entry.get("id") or "").strip()
        if not avatar_id:
            continue
        api_entry = by_id.get(avatar_id)
        if not api_entry:
            missing += 1
            continue
        api_name = (
            api_entry.get("avatar_name")
            or api_entry.get("name")
            or api_entry.get("preview_name")
            or ""
        ).strip()
        if api_name and entry.get("heygen_name") != api_name:
            entry["heygen_name"] = api_name
            updated += 1

    save_config(config)
    return {"updated": updated, "missing": missing, "total": len(avatars)}
