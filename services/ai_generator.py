import re
import time
from openai import OpenAI
from prompts.script_prompts import (
    get_system_prompt,
    problem_promise_prompt,
    three_mistakes_prompt,
    before_after_prompt,
    myth_truth_prompt,
    fast_tip_prompt,
    SCRIPT_MIN_WORDS,
    SCRIPT_MAX_WORDS,
    WORDS_PER_SECOND,
)
from services.file_manager import build_chatgpt_template
from prompts.heygen_motion_prompts import (
    get_heygen_motion_system_prompt,
    heygen_motion_prompt_user,
)


def call_openai(
    client: OpenAI,
    system: str,
    user: str,
    model: str,
    max_tokens: int = 400,
    retries: int = 2,
) -> str:
    """Make a single OpenAI API call with retry logic."""
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.85,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)  
            else:
                raise RuntimeError(f"OpenAI API call failed after {retries + 1} attempts: {e}") from e


def _parse_tips_mistakes(raw: str) -> tuple:
    """Parse the LLM TIPS/MISTAKES response into two newline-joined strings."""
    tips_lines, mistakes_lines = [], []
    section = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        upper = stripped.upper()
        if upper.startswith("TIPS"):
            section = "tips"
            continue
        if upper.startswith("MISTAKES"):
            section = "mistakes"
            continue
        if section == "tips":
            tips_lines.append(stripped)
        elif section == "mistakes":
            mistakes_lines.append(stripped)
    return "\n".join(tips_lines), "\n".join(mistakes_lines)


def generate_tips_and_mistakes(client: OpenAI, data: dict, model: str) -> tuple:
    """
    Auto-generate 3 quick tips/wins and 3 common audience mistakes from the
    existing product inputs, before the scripts are generated.
    Returns (tips, mistakes) as newline-separated strings.
    """
    system = (
        "You are a digital product marketing strategist. From the product details "
        "provided, infer the most valuable quick tips/wins likely found inside the "
        "product, and the most common mistakes the target audience makes. "
        "Be specific and concrete — grounded in the product description, audience, "
        "pain points, and transformation. Never write generic filler."
    )
    user = f"""Based on this digital product, generate:
- 3 quick tips / wins that are likely inside the product
- 3 common mistakes the target audience makes

Product Title: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Pain Points: {data['pain_points']}
Before/After Transformation: {data['before_after']}

Return ONLY in this exact format, with no extra commentary:
TIPS:
1. <tip>
2. <tip>
3. <tip>
MISTAKES:
1. <mistake>
2. <mistake>
3. <mistake>
"""
    raw = call_openai(client, system, user, model)
    return _parse_tips_mistakes(raw)


def _count_spoken_words(text: str) -> int:
    """Approximate spoken word count (labels and bracket cues excluded)."""
    words = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("Word count:", "Note:")):
            continue
        spoken = re.sub(r"^[A-Z][A-Z0-9\s→/&+\-]*:\s*", "", stripped)
        spoken = re.sub(r"\[[^\]]*\]", "", spoken)
        words += len(spoken.split())
    return words


def _strip_script_metadata(raw: str) -> str:
    lines = []
    for line in raw.strip().splitlines():
        stripped = line.strip()
        if stripped.startswith("Word count:") or stripped.startswith("Note:"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _cta_present(body: str, phrase: str) -> bool:
    if not phrase:
        return True
    return phrase.lower() in body.lower()


def _link_present(body: str, link: str) -> bool:
    if not link:
        return True
    normalized = link.lower().replace("https://", "").replace("http://", "").replace("www.", "")
    body_lower = body.lower()
    return link.lower() in body_lower or normalized in body_lower


def ensure_cta_and_link(body: str, data: dict) -> str:
    """Append CTA phrase and link if the model omitted them — never removes content."""
    cta = (data.get("cta") or "").strip()
    link = (data.get("link") or "").strip()
    body = body.strip()

    if cta and not _cta_present(body, cta):
        body = f"{body}\nCTA: [direct] {cta}"

    if link and not _link_present(body, link):
        lines = body.splitlines()
        for idx in range(len(lines) - 1, -1, -1):
            if lines[idx].strip().upper().startswith("CTA:"):
                lines[idx] = f"{lines[idx].rstrip()} {link}"
                return "\n".join(lines)
        closing = f"CTA: [direct] {cta}. {link}" if cta else f"CTA: [direct] {link}"
        body = f"{body}\n{closing}"

    return body


def finalize_script(raw: str, data: dict | None = None) -> str:
    """Strip metadata, ensure CTA/link ending, prepend word-count note."""
    body = _strip_script_metadata(raw)
    if data:
        body = ensure_cta_and_link(body, data)

    word_count = _count_spoken_words(body)
    read_secs = max(1, round(word_count / WORDS_PER_SECOND))
    meta = f"Word count: {word_count} words | Estimated read time: ~{read_secs} seconds"
    note = "Note: Text in [brackets] are delivery cues — do not read these aloud."
    return f"{meta}\n{note}\n\n{body}"


def generate_script(
    client: OpenAI,
    sys_script: str,
    prompt_fn,
    data: dict,
    model: str,
) -> str:
    """Generate one script; retry once with a shorter rewrite if over the word limit."""
    user_prompt = prompt_fn(data)
    raw = call_openai(client, sys_script, user_prompt, model, max_tokens=550)
    body = ensure_cta_and_link(_strip_script_metadata(raw), data)

    if _count_spoken_words(body) > SCRIPT_MAX_WORDS:
        shorter_prompt = (
            f"{user_prompt}\n\n"
            f"REWRITE SHORTER: Your previous draft was too long ({_count_spoken_words(body)} words). "
            f"Rewrite the entire script in {SCRIPT_MIN_WORDS}–{SCRIPT_MAX_WORDS} words. "
            f"Keep the full mandatory CTA ending (exact CTA phrase and link). "
            f"Trim the middle sections — never cut off the ending."
        )
        raw = call_openai(client, sys_script, shorter_prompt, model, max_tokens=550)
        body = ensure_cta_and_link(_strip_script_metadata(raw), data)

    return finalize_script(body, data=None)


def generate_talking_head_guide(data: dict) -> str:
    """Static HeyGen avatar guide — personalised with product data."""
    return f"""TALKING HEAD GUIDE — {data['title']}
Generated for: {data['audience']}
==============================================

HOW YOUR AVATAR VIDEOS ARE MADE (HEYGEN AVATAR IV)

WHAT HAPPENS AUTOMATICALLY
- A unique HeyGen photo avatar is selected for each video (no repeats per product).
- The full script is sent to HeyGen for AI voice + lip-sync — complete, never truncated.
- Every video ends by speaking your exact CTA phrase and website link.
- Safe motion is applied per avatar: gestures for normal looks, frozen hands only for holds_prop avatars.
- Expressiveness is set to HIGH for natural movement (Avatar IV fallback).
- Output: 9:16 vertical, 720p talking-head MP4.

STEP 1 — REVIEW YOUR VIDEOS
- Download each MP4 from the Videos or Downloads tab.
- Check lip-sync and gestures; regenerate in HeyGen dashboard if needed.

STEP 2 — EDIT FOR REELS/TIKTOK/SHORTS
- Aspect ratio: 9:16 (vertical)
- Add auto-captions (most viewers watch without sound).
- Add background music at 10–15% volume.

RECOMMENDED CAPTION STYLE:
- Bold white text, black stroke
- Font: Montserrat Bold or Impact
- Center-aligned, lower third position

PRODUCT DETAILS FOR OVERLAY:
- Product: {data['title']}
- CTA: {data['cta']}
- Link: {data['link']}

TIP: Keep energy high and message clear — each clip is a complete 20–30 second story.
"""


def generate_image_guide(data: dict) -> str:
    """Static image style guide — personalised with product data."""
    return f"""IMAGE STYLE GUIDE — {data['title']}
==============================================

BRAND STYLE IDEAS FOR YOUR DIGITAL PRODUCT

TARGET AESTHETIC: Modern, clean, trustworthy, aspirational
Audience: {data['audience']}

─── 15 IMAGE CONCEPTS ───────────────────────

1. Flat lay of a laptop, coffee, and notebook — productive morning vibes
2. Close-up hands typing — focus and action
3. Woman smiling at laptop screen — relief/victory moment
4. Clean desk setup with natural window light — aspirational workspace
5. Phone in hand scrolling — relatable everyday moment
6. Open notebook with handwritten goals — intentionality
7. Stack of books + coffee mug — knowledge aesthetic
8. Person walking confidently in urban setting — transformation energy
9. Overhead shot of planning pages — organized and strategic
10. Sunrise through a window — new beginnings, hope
11. Two hands exchanging/pointing at a screen — teaching moment
12. Minimalist home office with plants — calm productivity
13. Person celebrating small win at desk — emotional payoff
14. Close-up of a phone showing a Stripe/sales notification — social proof
15. Candid laugh while working — joy in the process

─── ANIMATING STATIC IMAGES ─────────────────

To animate a flat lay or workspace image:
1. Upload your flat lay or workspace image to an image-to-video tool
2. Prompt: "Subtle parallax movement, soft natural light"
3. Duration: 3–5 seconds
4. Use as a background overlay behind your avatar video

─── COLOR PALETTE SUGGESTIONS ──────────────

Option A (Clean & Professional):
- Background: #FFFFFF or #F8F6F2
- Accent: Deep Navy #1B2A4A
- Pop: Warm Gold #D4A853

Option B (Modern & Bold):
- Background: #0F0F0F
- Accent: Electric Purple #7C3AED
- Pop: Bright White #FFFFFF

Option C (Warm & Approachable):
- Background: #FDF6EC
- Accent: Terracotta #C4622D
- Pop: Forest Green #2D6A4F

─── TEXT OVERLAY TEMPLATE ───────────────────

Headline: {data['title']}
Sub: Perfect for {data['audience']}
CTA: {data['cta']}
Link: {data['link']}
"""


# Topic key -> human label for motion prompts.
TOPIC_LABELS = [
    ("problem_promise", "Problem to Promise"),
    ("three_mistakes", "3 Mistakes"),
    ("before_after", "Before to After"),
    ("myth_truth", "Myth vs Truth"),
    ("fast_tip", "Fast Tip to Sell"),
]


def generate_all_content(data: dict, api_key: str, model: str = "gpt-4o-mini") -> dict:
    """
    Master generation function. Calls OpenAI for 5 scripts and 5 HeyGen motion prompts
    (one unique set per topic). Returns a structured dict with all generated content.
    """
    client = OpenAI(api_key=api_key)
    sys_script = get_system_prompt()
    sys_motion = get_heygen_motion_system_prompt()

    # ── Auto-generate Tips & Mistakes  ───────
    tips, mistakes = generate_tips_and_mistakes(client, data, model)
    data["tips"] = tips
    data["mistakes"] = mistakes

    # ── Generate 5 Scripts ────────────────────────────────────────────────────
    scripts = {}
    script_configs = [
        ("problem_promise", problem_promise_prompt),
        ("three_mistakes", three_mistakes_prompt),
        ("before_after", before_after_prompt),
        ("myth_truth", myth_truth_prompt),
        ("fast_tip", fast_tip_prompt),
    ]

    for key, prompt_fn in script_configs:
        scripts[key] = generate_script(client, sys_script, prompt_fn, data, model)

    # ── HeyGen motion prompts (sent to API with each video) ───────────────────
    motion_prompts = {}
    for key, label in TOPIC_LABELS:
        user_prompt = heygen_motion_prompt_user(label, data, scripts[key])
        raw = call_openai(client, sys_motion, user_prompt, model, max_tokens=180)
        motion_prompts[key] = raw.strip().strip('"')

    # ── Generate Extras (Static + Personalised) ───────────────────────────────
    extras = {
        "avatar_guide": generate_talking_head_guide(data),
        "image_guide": generate_image_guide(data),
        "chatgpt_template": build_chatgpt_template(data),
    }

    return {
        "scripts": scripts,
        "motion_prompts": motion_prompts,
        "extras": extras,
    }