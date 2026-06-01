"""
B-roll / cinematic video prompt generation.
Produces AI video prompts optimized for Kling, Runway, and Veo.
"""


def get_broll_system_prompt():
    return (
        "You are a cinematic AI video director specializing in short-form marketing content. "
        "You write detailed, vivid visual prompts for AI video generators like Kling, Runway, and Veo. "
        "Your prompts are specific, sensory, and production-quality. "
        "Each prompt should describe: subject, action, environment, lighting, camera angle, mood, style. "
        "Always include: 'cinematic', 'realistic', 'shallow depth of field' or 'wide establishing shot' as appropriate. "
        "Avoid generic descriptions. Be specific about lighting, textures, and emotion."
    )


def broll_for_problem_promise(data: dict, script: str) -> str:
    return f"""Generate 5 cinematic B-roll video prompts for this Problem → Promise marketing script.

Product: {data['title']}
Audience: {data['audience']}

Script context:
{script[:600]}

Generate exactly 5 prompts. Label them:
SCENE 1 (Hook — The Problem):
SCENE 2 (Agitation — The Struggle):
SCENE 3 (Pivot — Hope Arrives):
SCENE 4 (Promise — The Solution):
SCENE 5 (CTA — Action Moment):

Each prompt should be 2–4 sentences. Reference specific visual details: lighting conditions, camera movements, subject emotions, environment.

Example style: "A tired young woman sitting at a cluttered desk late at night, laptop screen casting a blue glow on her face, surrounded by sticky notes and coffee cups, shallow depth of field, cinematic lighting, 4K realistic, slight slow motion."

Now write the 5 prompts for this specific product and audience."""


def broll_for_three_mistakes(data: dict, script: str) -> str:
    return f"""Generate 5 cinematic B-roll video prompts for this "3 Mistakes" marketing script.

Product: {data['title']}
Audience: {data['audience']}

Script context:
{script[:600]}

Label them:
SCENE 1 (Hook — Pattern Interrupt):
SCENE 2 (Mistake 1 Visual):
SCENE 3 (Mistake 2 Visual):
SCENE 4 (Mistake 3 Visual):
SCENE 5 (Solution Reveal):

Mistakes context: {data['mistakes']}

Each prompt: 2–4 sentences. Specific lighting, camera, emotion, environment. Cinematic and realistic."""


def broll_for_before_after(data: dict, script: str) -> str:
    return f"""Generate 6 cinematic B-roll video prompts for this Before → After transformation script.

Product: {data['title']}
Audience: {data['audience']}
Transformation: {data['before_after']}

Script context:
{script[:600]}

Label them:
SCENE 1 (The Before — Struggle):
SCENE 2 (The Before — Emotional Low):
SCENE 3 (Turning Point):
SCENE 4 (The After — First Win):
SCENE 5 (The After — New Life):
SCENE 6 (CTA Moment):

Each prompt: 2–4 sentences. Contrasting moods between before/after. Cold/dark lighting for before, warm/bright for after."""


def broll_for_myth_truth(data: dict, script: str) -> str:
    return f"""Generate 5 cinematic B-roll video prompts for this Myth vs Truth marketing script.

Product: {data['title']}
Audience: {data['audience']}

Script context:
{script[:600]}

Label them:
SCENE 1 (Hook — The Reveal):
SCENE 2 (Myth Being Believed — Wrong Path):
SCENE 3 (The Truth Emerges):
SCENE 4 (Lightbulb Moment):
SCENE 5 (Empowered Action):

Each prompt: 2–4 sentences. Use visual contrast between confusion and clarity. Cinematic, realistic."""


def broll_for_fast_tip(data: dict, script: str) -> str:
    return f"""Generate 5 cinematic B-roll video prompts for this Fast Tip → Sell marketing script.

Product: {data['title']}
Audience: {data['audience']}
Tips context: {data['tips']}

Script context:
{script[:600]}

Label them:
SCENE 1 (Hook — Attention Grab):
SCENE 2 (Tip in Action — Demonstration):
SCENE 3 (Positive Outcome):
SCENE 4 (Product Tease):
SCENE 5 (CTA Moment):

Each prompt: 2–4 sentences. Upbeat, energetic visuals. Natural daylight or warm interior lighting. Realistic and cinematic."""