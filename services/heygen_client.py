"""
HeyGen talking-head client — full-script presenter videos with custom motion.

Uses POST /v3/videos (type: avatar). Tries Avatar V first, falls back to Avatar IV.
Polls GET /v3/videos/{video_id} until completed, then downloads the MP4.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.avatar_registry import get_random_avatar_id, is_configured
from services.motion_resolver import resolve_motion_prompt

HEYGEN_BASE = os.getenv("HEYGEN_BASE_URL", "https://api.heygen.com").rstrip("/")

DEFAULT_VOICE_SPEED = float(os.getenv("HEYGEN_VOICE_SPEED", "1.0"))
DEFAULT_FIT = os.getenv("HEYGEN_FIT", "cover").strip() or "cover"

POLL_INTERVAL_SEC = int(os.getenv("HEYGEN_POLL_INTERVAL_SEC", "15"))
MAX_POLL_ATTEMPTS = int(os.getenv("HEYGEN_MAX_POLL_ATTEMPTS", "80"))  # ~20 min at 15s

DEFAULT_RESOLUTION = os.getenv("HEYGEN_RESOLUTION", "720p").strip() or "720p"
DEFAULT_ASPECT_RATIO = os.getenv("HEYGEN_ASPECT_RATIO", "9:16").strip() or "9:16"
DEFAULT_EXPRESSIVENESS = os.getenv("HEYGEN_EXPRESSIVENESS", "medium").strip() or "medium"
DEFAULT_ENGINE = os.getenv("HEYGEN_ENGINE", "avatar_v").strip() or "avatar_v"
FALLBACK_ENGINE = os.getenv("HEYGEN_ENGINE_FALLBACK", "avatar_iv").strip() or "avatar_iv"


def is_heygen_configured() -> bool:
    api_key = os.getenv("HEYGEN_API_KEY", "").strip()
    voice_id = os.getenv("HEYGEN_VOICE_ID", "").strip()
    return bool(api_key and voice_id and is_configured())


def prepare_script_for_heygen(script_text: str) -> str:
    """Return cleaned spoken script for HeyGen (plain text — no SSML extras)."""
    return extract_spoken_script(script_text)


def extract_spoken_script(script_text: str) -> str:
    """
    Return spoken text ONLY for HeyGen. Strips:
      - Word count / Note metadata lines
      - ALL-CAPS section labels (HOOK:, PROMISE + PROOF TEASE:, etc.)
      - Delivery cues in square brackets
      - Blank lines

    The full script is sent as-is — no truncation.
    """
    lines = []
    for line in script_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Word count:"):
            continue
        if stripped.startswith("Note:"):
            continue
        spoken = re.sub(r"^[A-Z][A-Z0-9\s→/&+\-]*:\s*", "", stripped)
        spoken = re.sub(r"\[[^\]]*\]", "", spoken).strip()
        if spoken:
            lines.append(spoken)

    text = " ".join(lines)
    return re.sub(r"\s+", " ", text).strip()


def _api_key() -> str:
    key = os.getenv("HEYGEN_API_KEY", "").strip()
    if not key:
        raise RuntimeError("HeyGen is not configured (missing HEYGEN_API_KEY).")
    return key


def _api_request(method: str, path: str, payload: dict | None = None) -> dict:
    url = f"{HEYGEN_BASE}{path}"
    headers = {
        "X-Api-Key": _api_key(),
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(raw)
            msg = (err.get("error") or {}).get("message") or raw
        except json.JSONDecodeError:
            msg = raw
        raise RuntimeError(f"HeyGen API error ({e.code}): {msg}") from e

    if body.get("error"):
        err = body["error"]
        raise RuntimeError(err.get("message") or str(err))
    return body


def _engines_to_try() -> list[str]:
    engines = [DEFAULT_ENGINE]
    if FALLBACK_ENGINE and FALLBACK_ENGINE != DEFAULT_ENGINE:
        engines.append(FALLBACK_ENGINE)
    return engines


def _build_video_payload(
    script_text: str,
    avatar_id: str,
    voice_id: str,
    motion_prompt: str | None,
    engine: str,
) -> dict:
    payload: dict = {
        "type": "avatar",
        "avatar_id": avatar_id,
        "script": script_text,
        "voice_id": voice_id,
        "resolution": DEFAULT_RESOLUTION,
        "aspect_ratio": DEFAULT_ASPECT_RATIO,
        "fit": DEFAULT_FIT,
        "engine": {"type": engine},
        "voice_settings": {
            "speed": DEFAULT_VOICE_SPEED,
            "pitch": 0,
            "locale": "en-US",
        },
    }
    safe_motion = resolve_motion_prompt(avatar_id, motion_prompt)
    if safe_motion:
        payload["motion_prompt"] = safe_motion
    # expressiveness is Avatar IV only — Avatar V rejects it.
    if engine == "avatar_iv":
        payload["expressiveness"] = DEFAULT_EXPRESSIVENESS
    return payload


def _should_retry_with_fallback(error: RuntimeError, engine: str, engines: list[str]) -> bool:
    if engine == engines[-1]:
        return False
    msg = str(error).lower()
    if "heygen api error (400)" in msg or "heygen api error (403)" in msg:
        return True
    for keyword in ("avatar_v", "engine", "eligib", "not support", "unsupported"):
        if keyword in msg:
            return True
    return False


def _create_video(
    script_text: str,
    avatar_id: str,
    motion_prompt: str | None,
) -> tuple[str, str]:
    voice_id = os.getenv("HEYGEN_VOICE_ID", "").strip()
    if not voice_id:
        raise RuntimeError("HeyGen is not configured (missing HEYGEN_VOICE_ID).")
    avatar_id = (avatar_id or "").strip()
    if not avatar_id:
        raise RuntimeError("No HeyGen avatar_id provided.")

    engines = _engines_to_try()
    last_error: RuntimeError | None = None

    for engine in engines:
        payload = _build_video_payload(
            script_text, avatar_id, voice_id, motion_prompt, engine,
        )
        try:
            result = _api_request("POST", "/v3/videos", payload)
            data = result.get("data") or {}
            video_id = data.get("video_id")
            if not video_id:
                raise RuntimeError(f"HeyGen did not return a video_id: {result}")
            return video_id, engine
        except RuntimeError as exc:
            last_error = exc
            if _should_retry_with_fallback(last_error, engine, engines):
                continue
            raise

    if last_error:
        raise last_error
    raise RuntimeError("HeyGen video generation failed.")


def _poll_video_url(video_id: str) -> str:
    for _ in range(MAX_POLL_ATTEMPTS):
        result = _api_request("GET", f"/v3/videos/{video_id}")
        data = result.get("data") or {}
        status = (data.get("status") or "").lower()

        if status == "completed":
            video_url = data.get("video_url")
            if not video_url:
                raise RuntimeError("HeyGen reported completed but returned no video_url.")
            return video_url
        if status == "failed":
            msg = data.get("failure_message") or data.get("error") or "HeyGen video generation failed."
            raise RuntimeError(str(msg))

        time.sleep(POLL_INTERVAL_SEC)

    raise RuntimeError("HeyGen video generation timed out.")


def _download_video(video_url: str) -> bytes:
    req = urllib.request.Request(video_url)
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def complete_talking_head_videos_parallel(
    pending_by_key: dict[str, dict],
    *,
    max_workers: int = 5,
) -> dict[str, dict]:
    """Poll and download multiple HeyGen jobs concurrently."""
    results: dict[str, dict] = {}

    def _finish(key: str, pending: dict) -> tuple[str, dict]:
        try:
            return key, complete_talking_head_video(pending)
        except Exception as exc:
            return key, {**pending, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_finish, key, pending): key
            for key, pending in pending_by_key.items()
        }
        for future in as_completed(futures):
            key, video = future.result()
            results[key] = video
    return results


def start_talking_head_videos_parallel(
    jobs: list[tuple[str, str, str | None, str | None]],
    *,
    max_workers: int = 5,
) -> dict[str, dict]:
    """
    Submit multiple HeyGen jobs concurrently.

    Each job: (key, script_text, avatar_id, motion_prompt).
    """
    results: dict[str, dict] = {}

    def _start(job: tuple[str, str, str | None, str | None]) -> tuple[str, dict]:
        key, script, avatar_id, motion = job
        try:
            return key, start_talking_head_video(script, avatar_id=avatar_id, motion_prompt=motion)
        except Exception as exc:
            return key, {"error": str(exc)}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_start, job): job[0] for job in jobs}
        for future in as_completed(futures):
            key, pending = future.result()
            results[key] = pending
    return results


def complete_talking_head_video(pending: dict) -> dict:
    """Poll HeyGen until ready and download bytes for a job started earlier."""
    video_id = (pending.get("video_id") or "").strip()
    if not video_id:
        raise RuntimeError("No video_id to resume.")
    video_url = _poll_video_url(video_id)
    video_bytes = _download_video(video_url)
    return {
        **pending,
        "video_url": video_url,
        "bytes": video_bytes,
        "status": "completed",
    }


def start_talking_head_video(
    script_text: str,
    *,
    avatar_id: str | None = None,
    motion_prompt: str | None = None,
) -> dict:
    """Submit a HeyGen job and return metadata (no polling/download yet)."""
    if not is_heygen_configured():
        raise RuntimeError("HeyGen is not configured.")

    if avatar_id is None:
        avatar_id = get_random_avatar_id()
    avatar_id = (avatar_id or "").strip()

    spoken_plain = extract_spoken_script(script_text)
    if not spoken_plain:
        raise RuntimeError("Script is empty after cleaning.")

    spoken = prepare_script_for_heygen(script_text)
    if not spoken:
        spoken = spoken_plain

    safe_motion = resolve_motion_prompt(avatar_id, motion_prompt)
    video_id, engine = _create_video(
        spoken,
        avatar_id,
        safe_motion,
    )
    return {
        "video_id": video_id,
        "avatar_id": avatar_id,
        "engine": engine,
        "motion_prompt": safe_motion,
        "script_spoken": spoken_plain,
        "status": "processing",
    }


def generate_talking_head_video(
    script_text: str,
    *,
    avatar_id: str | None = None,
    motion_prompt: str | None = None,
) -> dict:
    """
    Generate one talking-head video (Avatar V, with Avatar IV fallback).

    Args:
        script_text: Full script (metadata/cues stripped automatically).
        avatar_id: HeyGen photo-avatar look ID; defaults to first enabled registry entry.
        motion_prompt: Custom motion for gestures/expression.

    Returns:
        dict with video_id, video_url, bytes, avatar_id, engine, motion_prompt, script_spoken.
    """
    pending = start_talking_head_video(
        script_text,
        avatar_id=avatar_id,
        motion_prompt=motion_prompt,
    )
    return complete_talking_head_video(pending)
