"""
Script generation prompts — 5 short-form video script templates.
Each returns a system prompt + user prompt pair for OpenAI.
"""

# Spoken length targets for HeyGen (~2 words/sec TTS). Scripts are generated complete —
# nothing is truncated before sending to HeyGen.
SCRIPT_MIN_WORDS = 55
SCRIPT_MAX_WORDS = 75
SCRIPT_LENGTH_LABEL = f"{SCRIPT_MIN_WORDS} and {SCRIPT_MAX_WORDS} words total (about 28–38 seconds when read aloud)"
WORDS_PER_SECOND = 2.0


def cta_ending_rules(data: dict) -> str:
    """Mandatory CTA + link closing rules injected into every script prompt."""
    cta = (data.get("cta") or "").strip()
    link = (data.get("link") or "").strip()
    if link:
        link_rule = (
            f'- Immediately after the CTA phrase, speak the website/link aloud exactly as written: "{link}"'
        )
    else:
        link_rule = "- No website link was provided — end with the CTA phrase only."
    return f"""
CTA ENDING (MANDATORY — must be the final section of every script):
- The last section label must be: CTA:
- Speak this EXACT call-to-action phrase word for word: "{cta}"
{link_rule}
- The CTA phrase{"" if not link else " and link"} must be the very last words spoken.
- Never paraphrase, shorten, or skip the CTA phrase{"" if not link else " or link"}.
- Budget your word count so the full story AND this CTA ending fit naturally — do not run out of room.
"""


OUTPUT_RULES = f"""
CRITICAL OUTPUT RULES (every script must follow all of these):

FORMAT
- Plain text ONLY. No markdown of any kind. Absolutely NO asterisks (*), no bold, no
  italics, no hashtags, no backticks, no underscores for emphasis, no bullet symbols.
- Write section labels as plain words followed by a colon, e.g. "HOOK:" — never "**HOOK:**".
- NO EMOJIS OR PICTOGRAPHS of any kind anywhere in the output. Not in labels, not in the
  body, not in the CTA. The text is read aloud by a human/AI voice — emojis cannot be spoken.
- This is spoken delivery for a short vertical social video. Write clean, readable spoken text.
- Do NOT add a word-count or read-time line — that is added automatically after generation.

LENGTH
- Keep the full spoken script between {SCRIPT_LENGTH_LABEL}.
- Write SHORT, complete scripts — never write too much and assume it will be cut later.
- Be concise: short sentences, one idea per beat. Trim the middle sections first if needed.
- You MUST still include the full mandatory CTA ending (CTA phrase{""} + link) within the word limit.
- Use short sentences with natural pauses. Avoid cramming too many ideas into one breath.

DELIVERY CUES
- After EACH section label, add ONE very short delivery cue in square brackets.
  Examples: [pause]  [lean in]  [upbeat]  [direct to camera]
- Cues are stage directions only — they must NOT be spoken aloud.
- Do not put spoken dialogue inside brackets.
"""


def get_system_prompt():
    return (
        "You are an expert short-form video scriptwriter for digital product creators. "
        "You write punchy, emotionally engaging scripts optimized for Reels, "
        "TikTok, and YouTube Shorts. Your scripts have a strong pattern-interrupt hook, "
        "clear value delivery, and a natural CTA — with zero filler. "
        "Never sound robotic, corporate, or generic. Write like a confident, relatable human creator. "
        f"Every script must be {SCRIPT_MIN_WORDS}–{SCRIPT_MAX_WORDS} words of spoken dialogue "
        "(about 28–38 seconds when read aloud). Write complete scripts that fit naturally — "
        "never exceed the limit and never leave the ending unfinished. "
        "You output PLAIN TEXT ONLY: never use asterisks, markdown, or emojis. "
        + OUTPUT_RULES
    )


def problem_promise_prompt(data: dict) -> str:
    return f"""Write a Problem → Promise short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Pain Points: {data['pain_points']}
Before/After Transformation: {data['before_after']}
Product Tips (use these in PROOF TEASE): {data['tips']}
CTA: {data['cta']}
Link: {data['link']}

Script formula (use these exact section labels):
1. HOOK: Open with the audience's biggest pain point — pattern-interrupt style
2. AGITATE: Briefly twist the knife — make them feel seen (1–2 short sentences)
3. PIVOT: Transition to hope — MUST reference something specific and unique about THIS product
   (a detail from the description, the unique angle, or the specific transformation).
   Do NOT use generic lines like "But what if there was a way..." — make it personal to this eBook.
4. PROMISE + PROOF TEASE: ONE merged punchy line (not two separate sections).
   State what the product delivers AND weave in the actual tips listed above —
   name specific outcomes from those tips, not vague values like "courage and friendship".
5. CTA: Speak the exact CTA phrase and website link (see CTA ENDING rules below)

{cta_ending_rules(data)}
{OUTPUT_RULES}

Make it raw, real, and scroll-stopping. Stay between {SCRIPT_MIN_WORDS} and {SCRIPT_MAX_WORDS} words total including the CTA ending."""


def three_mistakes_prompt(data: dict) -> str:
    return f"""Write a "3 Mistakes" short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Mistakes (use these exact mistakes): {data['mistakes']}
CTA: {data['cta']}
Link: {data['link']}

Script formula (use these exact section labels):
1. HOOK: Pattern-interrupt opener about mistakes this audience makes
2. MISTAKE 1: Name the first mistake + one short sentence why it fails
3. MISTAKE 2: Name the second mistake + one short sentence why it fails
4. MISTAKE 3: Name the third mistake + one short sentence why it fails
5. BRIDGE: Brief empathetic bridge to the solution
6. CTA: Speak the exact CTA phrase and website link (see CTA ENDING rules below)

{cta_ending_rules(data)}
{OUTPUT_RULES}

Use the three mistakes provided — name each in just a few words. Stay between {SCRIPT_MIN_WORDS} and {SCRIPT_MAX_WORDS} words including the CTA ending."""


def before_after_prompt(data: dict) -> str:
    return f"""Write a Before → After transformation short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Transformation: {data['before_after']}
Product Tips: {data['tips']}
CTA: {data['cta']}
Link: {data['link']}

Script formula (use these exact section labels):
1. HOOK: Paint the "before" struggle vividly — one punchy opening line
2. BEFORE: The pain, specific and relatable (1–2 short sentences)
3. TURNING POINT: The moment things changed — reference something specific about this product
4. AFTER: The new reality — relief and wins (1–2 short sentences)
5. BRIDGE: Connect the transformation to the product
6. CTA: Speak the exact CTA phrase and website link (see CTA ENDING rules below)

{cta_ending_rules(data)}
{OUTPUT_RULES}

Storytelling tone. Stay between {SCRIPT_MIN_WORDS} and {SCRIPT_MAX_WORDS} words including the CTA ending."""


def myth_truth_prompt(data: dict) -> str:
    return f"""Write a Myth vs Truth short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Pain Points: {data['pain_points']}
Tips (reference these specific tips when busting myths): {data['tips']}
CTA: {data['cta']}
Link: {data['link']}

Script formula (use these exact section labels):
1. HOOK: Provocative opener — "Nobody told you the truth about..."
2. MYTH 1: State a common belief → bust it with a specific truth tied to this product
3. MYTH 2: State another belief → bust it, weave in a specific tip from the list above
4. REFRAME: The real reason this audience struggles — product-specific, not generic
5. CTA: Speak the exact CTA phrase and website link (see CTA ENDING rules below)

{cta_ending_rules(data)}
{OUTPUT_RULES}

Confident and slightly provocative. Between {SCRIPT_MIN_WORDS} and {SCRIPT_MAX_WORDS} words including the CTA ending."""


def fast_tip_prompt(data: dict) -> str:
    return f"""Write a Fast Tip → Sell short-form video script for this digital product:

Product: {data['title']}
Description: {data['description']}
Audience: {data['audience']}
Tips (deliver one tip, tease the others): {data['tips']}
CTA: {data['cta']}
Link: {data['link']}

Script formula (use these exact section labels):
1. HOOK: "Here's the ONE thing [audience] need to [outcome]" — specific to this product
2. TIP: Deliver one genuinely useful tip from the tips list above (builds trust)
3. EXPAND: One sentence going deeper on that tip
4. TEASE: One punchy line teasing more tips/benefits inside the product — use the actual tips listed
5. CTA: Speak the exact CTA phrase and website link (see CTA ENDING rules below)

{cta_ending_rules(data)}
{OUTPUT_RULES}

Generous value first. Between {SCRIPT_MIN_WORDS} and {SCRIPT_MAX_WORDS} words including the CTA ending."""
