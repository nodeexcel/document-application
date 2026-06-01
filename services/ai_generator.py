import time
from openai import OpenAI
from prompts.script_prompts import (
    get_system_prompt,
    problem_promise_prompt,
    three_mistakes_prompt,
    before_after_prompt,
    myth_truth_prompt,
    fast_tip_prompt,
)
from prompts.broll_prompts import (
    get_broll_system_prompt,
    broll_for_problem_promise,
    broll_for_three_mistakes,
    broll_for_before_after,
    broll_for_myth_truth,
    broll_for_fast_tip,
)


def call_openai(client: OpenAI, system: str, user: str, model: str, retries: int = 2) -> str:
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
                max_tokens=1200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)  
            else:
                raise RuntimeError(f"OpenAI API call failed after {retries + 1} attempts: {e}") from e


def generate_talking_head_guide(data: dict) -> str:
    """Static talking head HeyGen guide — personalised with product data."""
    return f"""TALKING HEAD GUIDE — {data['title']}
Generated for: {data['audience']}
==============================================

HOW TO USE HEYGEN FOR YOUR TALKING HEAD VIDEOS

STEP 1 — PREPARE YOUR AVATAR
- Upload a close-up headshot (good lighting, neutral background)
- Or use HeyGen's built-in avatars as a starting point
- Choose an avatar that matches your brand aesthetic

STEP 2 — SELECT YOUR SCRIPT
Use any of the 5 generated scripts in the Scripts/ folder.
Paste the script text directly into HeyGen's script box.

STEP 3 — VOICE SETTINGS
- Use your cloned voice (if available) for authenticity
- Or choose a natural-sounding voice (avoid robotic presets)
- Speaking pace: Medium (not too fast for short-form)

STEP 4 — VIDEO SETTINGS FOR REELS/TIKTOK/SHORTS
- Aspect ratio: 9:16 (vertical)
- Resolution: 1080 x 1920
- Duration: Keep under 90 seconds per script

STEP 5 — EXPORT & EDIT
- Export from HeyGen as MP4
- Import into CapCut or Premiere for captions
- Add auto-captions (80% of viewers watch without sound)
- Add background music at 10–15% volume

RECOMMENDED CAPTION STYLE:
- Bold white text, black stroke
- Font: Montserrat Bold or Impact
- Center-aligned, lower third position

PRODUCT DETAILS FOR OVERLAY:
- Product: {data['title']}
- CTA: {data['cta']}
- Link: {data['link']}

TIP: Record a quick intro at the start of each video saying 
"I made this so you don't have to go through what I did..."
This personalises the AI avatar content.
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

─── HIGGSFIELD AI WORKFLOW ──────────────────

Use Higgsfield to animate static images:
1. Upload your flat lay or workspace image
2. Prompt: "Subtle parallax movement, soft bokeh, cinematic"
3. Duration: 3–5 seconds
4. Use as B-roll filler or Instagram Reels background

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


def generate_all_content(data: dict, api_key: str, model: str = "gpt-4o-mini") -> dict:
    """
    Master generation function. Calls OpenAI for all 5 scripts + 5 B-roll sets.
    Returns a structured dict with all generated content.
    """
    client = OpenAI(api_key=api_key)
    sys_script = get_system_prompt()
    sys_broll = get_broll_system_prompt()

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
        scripts[key] = call_openai(client, sys_script, prompt_fn(data), model)

    # ── Generate B-Roll Prompts ───────────────────────────────────────────────
    broll = {}
    broll_configs = [
        ("broll_problem_promise", broll_for_problem_promise, scripts["problem_promise"]),
        ("broll_three_mistakes", broll_for_three_mistakes, scripts["three_mistakes"]),
        ("broll_before_after", broll_for_before_after, scripts["before_after"]),
        ("broll_myth_truth", broll_for_myth_truth, scripts["myth_truth"]),
        ("broll_fast_tip", broll_for_fast_tip, scripts["fast_tip"]),
    ]

    for key, prompt_fn, script_text in broll_configs:
        broll[key] = call_openai(client, sys_broll, prompt_fn(data, script_text), model)

    # ── Generate Extras (Static + Personalised) ───────────────────────────────
    extras = {
        "talking_head": generate_talking_head_guide(data),
        "image_guide": generate_image_guide(data),
    }

    return {"scripts": scripts, "broll": broll, "extras": extras}