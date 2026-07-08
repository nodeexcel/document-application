"""
Resolve HeyGen motion prompts per avatar look.

Prop-holding avatars (holds_prop: true) get frozen-hand motion only.
All other avatars use the AI-generated motion prompt with light safety guardrails.
"""

from __future__ import annotations

import re

from services.avatar_registry import get_avatar_by_id

# Cup / prop avatars — hands must stay frozen to avoid extra limbs or moving props.
MOTION_HOLDS_PROP = (
    "Keep the entire body almost completely still. Maintain steady eye contact with the camera. "
    "Keep both hands frozen in their exact starting position holding the object — do not move "
    "arms, hands, or fingers at all. Do not add steam, smoke, vapor, heat waves, particles, "
    "liquid movement, or any background animation. Only subtle natural lip-sync and very "
    "small facial micro-expressions."
)

# Fallback when OpenAI returns nothing — matches HeyGen UI examples (lean in, gestures, nod).
MOTION_GESTURE_DEFAULT = (
    "Look at camera with a warm confident smile. Lean in slightly on the key point. "
    "Use one subtle open-hand gesture while speaking. End with a small approving nod. "
    "Keep movement professional, natural, and steady throughout — even speaking pace."
)

_UNSAFE_ENVIRONMENT = re.compile(
    r"\b(steam|smoke|vapor|heat wave|particle|fog|mist|liquid movement|background animation)\b",
    re.IGNORECASE,
)


def avatar_holds_prop(entry: dict | None) -> bool:
    """Only avatars explicitly flagged holds_prop: true use the frozen-hand profile."""
    return bool(entry and entry.get("holds_prop") is True)


def _strip_unsafe_phrases(text: str) -> str:
    cleaned = _UNSAFE_ENVIRONMENT.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;")
    return cleaned


def sanitize_gesture_motion(generated: str | None) -> str:
    """Use AI motion with guardrails — keep gestures, block environmental hallucinations."""
    motion = (generated or "").strip()
    if not motion:
        return MOTION_GESTURE_DEFAULT

    motion = _strip_unsafe_phrases(motion)
    if not motion:
        return MOTION_GESTURE_DEFAULT

    if not _UNSAFE_ENVIRONMENT.search(motion):
        motion = f"{motion.rstrip('.')}. Do not add steam, smoke, or background animation."
    return motion


def resolve_motion_prompt(avatar_id: str, generated_motion: str | None = None) -> str:
    entry = get_avatar_by_id(avatar_id)
    if avatar_holds_prop(entry):
        return MOTION_HOLDS_PROP
    return sanitize_gesture_motion(generated_motion)
