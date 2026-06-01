"""
Script generation prompts — 5 short-form video script templates.
Each returns a system prompt + user prompt pair for OpenAI.
"""


def get_system_prompt():
    return (
        "You are an expert short-form video scriptwriter for digital product creators. "
        "You write punchy, emotionally engaging scripts optimized for Reels, TikTok, and YouTube Shorts. "
        "Your scripts have strong pattern-interrupt hooks, clear value delivery, and natural-sounding CTAs. "
        "Never sound robotic, corporate, or generic. Write like a confident, relatable human creator. "
        "Each script should be approximately 45–90 seconds when spoken aloud (about 120–230 words). "
        "Format each script with: HOOK, BODY (2–3 beats), CTA."
    )


def problem_promise_prompt(data: dict) -> str:
    return f"""Write a Problem → Promise short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Pain Points: {data['pain_points']}
CTA: {data['cta']}
Link: {data['link']}

Script formula:
1. HOOK: Open with the audience's biggest pain point in a pattern-interrupt way
2. AGITATE: Briefly twist the knife — make them feel seen
3. PIVOT: "But what if there was a way to..."
4. PROMISE: Clearly state what the product delivers
5. PROOF TEASE: One specific result or transformation
6. CTA: Strong, direct call to action

Make it feel raw, real, and scroll-stopping. No fluff."""


def three_mistakes_prompt(data: dict) -> str:
    return f"""Write a "3 Mistakes" short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Mistakes: {data['mistakes']}
CTA: {data['cta']}
Link: {data['link']}

Script formula:
1. HOOK: "Stop doing [X] if you want [Y]" or "3 mistakes [audience] make with [topic]"
2. MISTAKE 1: Name it + 1 sentence why it fails
3. MISTAKE 2: Name it + 1 sentence why it fails
4. MISTAKE 3: Name it + 1 sentence why it fails
5. BRIDGE: "If any of these sound familiar..."
6. CTA: Reference the product as the solution

Make it authoritative but empathetic. Not preachy."""


def before_after_prompt(data: dict) -> str:
    return f"""Write a Before → After transformation short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Transformation: {data['before_after']}
CTA: {data['cta']}
Link: {data['link']}

Script formula:
1. HOOK: Paint the "before" picture vividly — the struggle, the frustration
2. BEFORE: Make the pain specific and relatable (2–3 sentences)
3. TURNING POINT: "Then everything changed when..."
4. AFTER: Paint the new reality — the relief, the wins
5. BRIDGE TO PRODUCT: "Here's exactly how..."
6. CTA: Direct and warm

Storytelling tone. Emotional but not overdramatic."""


def myth_truth_prompt(data: dict) -> str:
    return f"""Write a Myth vs Truth short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Pain Points: {data['pain_points']}
Tips: {data['tips']}
CTA: {data['cta']}
Link: {data['link']}

Script formula:
1. HOOK: "Nobody told you the truth about [topic]..."
2. MYTH 1: State the common belief → bust it with a truth
3. MYTH 2: State the common belief → bust it with a truth
4. MYTH 3 (optional): State the common belief → bust it
5. REFRAME: "The real reason [audience] struggle is..."
6. CTA: Position product as the truth-teller's tool

Make it feel like revealing a secret. Confident and slightly provocative."""


def fast_tip_prompt(data: dict) -> str:
    return f"""Write a Fast Tip → Sell short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Tips: {data['tips']}
CTA: {data['cta']}
Link: {data['link']}

Script formula:
1. HOOK: "Here's the ONE thing [audience] need to [outcome]"
2. TIP DELIVERY: Give a genuinely useful, specific tip (this builds trust)
3. EXPAND: 1–2 sentences going deeper on the tip
4. SOFT PIVOT: "If this helped, you'll love what's inside..."
5. TEASE: 1–2 more benefits/tips from the product
6. CTA: Clear and low-pressure

Generous value first. The sell feels like a natural extension."""