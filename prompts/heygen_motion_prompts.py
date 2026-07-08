"""
HeyGen Avatar custom motion prompts — sent to the API via motion_resolver.

Prop-holding avatars (holds_prop: true in avatars.json) are excluded from the
auto batch and use frozen-hand motion if used manually.
"""

DEFAULT_MOTION = (
    "Look at camera with a warm confident smile. Lean in slightly on the key point. "
    "Use one subtle open-hand gesture while speaking. End with a small approving nod. "
    "Keep movement professional and natural."
)


def get_heygen_motion_system_prompt() -> str:
    return (
        "You write custom motion prompts for HeyGen Avatar talking-head videos. "
        "The avatar lip-syncs a full script; your prompt controls body language, "
        "facial expression, and hand gestures ONLY — not what they say.\n\n"
        "RULES:\n"
        "- Output 2–4 short sentences of plain English (under 60 words total).\n"
        "- Use HeyGen-friendly actions: look at camera, lean in, warm smile, confident, "
        "subtle hand gesture, open palms, small nod, point gently, thumbs up at the end.\n"
        "- Match the script tone (empathetic, authoritative, energetic, etc.).\n"
        "- Keep hand movement subtle and professional — one or two gestures max.\n"
        "- Keep body language calm and steady — no sudden energy spikes.\n"
        "- NEVER include: walking, standing up, sitting down, camera movement, scene changes, "
        "steam, smoke, vapor, or background animation.\n"
        "- Output ONLY the motion prompt — no labels, markdown, quotes, or emojis."
    )


def heygen_motion_prompt_user(topic_label: str, data: dict, script: str) -> str:
    return f"""Write ONE HeyGen custom motion prompt for this talking-head clip.

Topic: {topic_label}
Product: {data['title']}
Audience: {data['audience']}

Script context (match the emotional tone, do NOT quote spoken lines):
{script[:500]}

Reference style (vary gestures to suit this topic):
"{DEFAULT_MOTION}"

Requirements:
- Start engaged: look at camera, warm expression.
- One body cue: lean in OR grounded open posture.
- One hand gesture tied to the message (open palm, subtle point, or thumbs up).
- End with a natural close: small nod or relaxed smile.
- Professional presenter; subtle movement only.
- No steam, smoke, or environmental effects.

Return ONLY the motion prompt (2–4 short sentences)."""
