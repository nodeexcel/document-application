"""
Persist HeyGen videos to the output folder so they survive session expiry / page reload.
"""

from __future__ import annotations

import json
import os
from typing import Any

VIDEO_KEYS = (
    "problem_promise",
    "three_mistakes",
    "before_after",
    "myth_truth",
    "fast_tip",
)

VIDEO_FILENAMES = {
    "problem_promise": "01_Problem_Promise.mp4",
    "three_mistakes": "02_Three_Mistakes.mp4",
    "before_after": "03_Before_After.mp4",
    "myth_truth": "04_Myth_Truth.mp4",
    "fast_tip": "05_Fast_Tip.mp4",
}

MANIFEST_NAME = "videos_manifest.json"


def videos_dir(output_folder: str) -> str:
    path = os.path.join(output_folder, "Avatar_Video")
    os.makedirs(path, exist_ok=True)
    return path


def video_file_path(output_folder: str, key: str) -> str:
    return os.path.join(videos_dir(output_folder), VIDEO_FILENAMES[key])


def manifest_path(output_folder: str) -> str:
    return os.path.join(output_folder, MANIFEST_NAME)


def _manifest_entry(video: dict, key: str, output_folder: str) -> dict:
    entry: dict[str, Any] = {
        "video_id": video.get("video_id"),
        "avatar_id": video.get("avatar_id"),
        "engine": video.get("engine"),
        "status": video.get("status"),
        "error": video.get("error"),
        "video_url": video.get("video_url"),
        "file_path": video.get("file_path") or video_file_path(output_folder, key),
    }
    return {k: v for k, v in entry.items() if v is not None}


def save_manifest(output_folder: str, videos: dict) -> None:
    if not output_folder or not os.path.isdir(output_folder):
        return
    manifest = {
        key: _manifest_entry(videos[key], key, output_folder)
        for key in VIDEO_KEYS
        if key in videos and videos[key]
    }
    with open(manifest_path(output_folder), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def persist_video(output_folder: str, key: str, video: dict, all_videos: dict | None = None) -> dict:
    """Write MP4 bytes to disk and return metadata (bytes kept for immediate UI use)."""
    if not output_folder:
        return video

    out = dict(video)
    path = video_file_path(output_folder, key)
    out["file_path"] = path

    data = out.get("bytes")
    if data:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    merged = dict(all_videos or load_videos_from_disk(output_folder))
    merged[key] = out
    save_manifest(output_folder, merged)
    return out


def persist_all_videos(output_folder: str, videos: dict) -> dict:
    updated = dict(videos)
    for key, video in videos.items():
        if video and (video.get("bytes") or video.get("video_id")):
            updated[key] = persist_video(output_folder, key, video) if video.get("bytes") else video
    save_manifest(output_folder, updated)
    return updated


def get_video_bytes(video: dict | None) -> bytes | None:
    if not video:
        return None
    if video.get("bytes"):
        return video["bytes"]
    path = video.get("file_path")
    if path and os.path.isfile(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def video_is_ready(video: dict | None) -> bool:
    if not video or video.get("error"):
        return False
    if video.get("bytes"):
        return True
    path = video.get("file_path")
    return bool(path and os.path.isfile(path) and os.path.getsize(path) > 0)


def load_videos_from_disk(output_folder: str) -> dict:
    """Load video metadata and verify files exist on disk."""
    if not output_folder or not os.path.isdir(output_folder):
        return {}

    loaded: dict = {}
    manifest_file = manifest_path(output_folder)
    if os.path.isfile(manifest_file):
        with open(manifest_file, encoding="utf-8") as f:
            manifest = json.load(f)
        for key, entry in manifest.items():
            path = entry.get("file_path") or video_file_path(output_folder, key)
            entry = dict(entry)
            entry["file_path"] = path
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                entry["status"] = "completed"
            loaded[key] = entry
        return loaded

    # Fallback: discover MP4s without manifest
    vdir = os.path.join(output_folder, "Avatar_Video")
    if not os.path.isdir(vdir):
        return {}
    for key, filename in VIDEO_FILENAMES.items():
        path = os.path.join(vdir, filename)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            loaded[key] = {"file_path": path, "status": "completed"}
    return loaded


def merge_session_videos(output_folder: str, session_videos: dict | None) -> dict:
    """Merge in-memory session state with on-disk videos (disk wins for missing bytes)."""
    disk = load_videos_from_disk(output_folder)
    merged = dict(disk)
    for key, video in (session_videos or {}).items():
        if not video:
            continue
        existing = merged.get(key, {})
        combined = {**existing, **video}
        if video_is_ready(combined):
            merged[key] = combined
        elif video.get("video_id") or video.get("error"):
            merged[key] = combined
    return merged


def output_folder_has_videos(output_folder: str) -> bool:
    videos = load_videos_from_disk(output_folder)
    return any(video_is_ready(v) for v in videos.values())
