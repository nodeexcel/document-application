"""
Kling B-roll prompt generation.

Cinematic supplementary clips for manual use in Kling (image-to-video or text-to-video).
These are NOT used for HeyGen talking-head generation — paste them into Kling yourself
to create B-roll that supports each script topic.
"""


def get_broll_system_prompt() -> str:
    return (
        "You are a cinematic B-roll director for short-form social video. "
        "Write ONE Kling-ready prompt for a supplementary visual clip that supports "
        "a talking-head video — not the presenter speaking to camera.\n\n"
        "RULES:\n"
        "- Describe a single cinematic scene (environment, action, mood, lighting).\n"
        "- 9:16 vertical, 3–5 seconds feel, smooth natural motion.\n"
        "- No on-screen text, no logos, no split screen, no talking-head close-up.\n"
        "- Product/audience themed but visually generic enough to reuse.\n"
        "- One or two sentences, plain text only — no markdown, labels, or emojis."
    )


def broll_prompt_user(topic_label: str, data: dict, script: str) -> str:
    return f"""Write ONE Kling B-roll prompt for a supplementary clip supporting this topic.

Topic: {topic_label}
Product: {data['title']}
Audience: {data['audience']}
Transformation: {data.get('before_after', '')}

Script context (inspire the visual metaphor, do NOT quote dialogue):
{script[:400]}

Examples of good B-roll ideas:
- Hands typing on laptop with soft morning light, slow push-in
- Person reviewing notes at a clean desk, calm productive mood
- Close-up of phone showing progress notification, subtle parallax
- Walking through bright modern space, confident energy, shallow depth of field

Requirements:
- One scene only, cinematic and aspirational.
- Match this topic's emotional arc (problem = tension, promise = relief, etc.).
- End with: 9:16 vertical, smooth cinematic motion.

Return ONLY the B-roll prompt (1–2 sentences)."""
