"""
File Manager Service — creates output folder structure and saves all generated content.
"""

import os
import re
from datetime import datetime

from prompts.script_prompts import SCRIPT_MIN_WORDS, SCRIPT_MAX_WORDS


def safe_filename(name: str) -> str:
    """Convert a string to a safe folder/file name."""
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:50]


def get_output_folder(title: str) -> str:
    """Return the path for this project's output folder."""
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    project_name = f"{safe_filename(title)}_{timestamp}"
    return os.path.join(base, project_name)


def create_folder_structure(base_path: str) -> dict:
    """Create the subfolder structure and return paths."""
    folders = {
        "motion_prompts": os.path.join(base_path, "HeyGen_Motion_Prompts"),
        "avatar_video": os.path.join(base_path, "Avatar_Video"),
        "images": os.path.join(base_path, "Images"),
    }
    for path in folders.values():
        os.makedirs(path, exist_ok=True)
    return folders


def write_file(folder: str, filename: str, content: str):
    """Write a text file to the specified folder."""
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def save_outputs(results: dict, product_data: dict) -> str:
    """
    Save all generated content into an organized folder structure.
    Returns the path to the created project folder.
    """
    output_folder = get_output_folder(product_data["title"])
    folders = create_folder_structure(output_folder)

    motion_prompts = results.get("motion_prompts", {})
    extras = results.get("extras", {})

    # Scripts are intentionally NOT written to disk — they feed HeyGen video generation.

    topic_filenames = {
        "problem_promise": "01_Problem_Promise.txt",
        "three_mistakes": "02_Three_Mistakes.txt",
        "before_after": "03_Before_After.txt",
        "myth_truth": "04_Myth_Truth.txt",
        "fast_tip": "05_Fast_Tip.txt",
    }

    for key, filename in topic_filenames.items():
        if key in motion_prompts:
            write_file(folders["motion_prompts"], filename, motion_prompts[key])

    # ── Avatar Video Guide ────────────────────────────────────────────────────
    if "avatar_guide" in extras:
        write_file(folders["avatar_video"], "Avatar_Video_Guide.txt", extras["avatar_guide"])

    # ── Image Style Guide ─────────────────────────────────────────────────────
    if "image_guide" in extras:
        write_file(folders["images"], "Image_Style_Guide.txt", extras["image_guide"])

    # ── Master ChatGPT Prompt Template ───────────────────────────────────────
    chatgpt_template = build_chatgpt_template(product_data)
    write_file(output_folder, "ChatGPT_Reuse_Prompt.txt", chatgpt_template)

    # ── README ────────────────────────────────────────────────────────────────
    readme = build_folder_readme(product_data)
    write_file(output_folder, "README.txt", readme)

    return output_folder


def build_chatgpt_template(data: dict) -> str:
    """Ready-to-copy ChatGPT prompt for generating more scripts outside this app."""
    return f"""You are an expert short-form video scriptwriter for digital product creators.

Generate ALL 5 of the following video scripts for my digital product. Use the exact same format for each script.

PRODUCT DETAILS (fill in or edit as needed):
- Product title: {data['title']}
- Product description: {data['description']}
- Target audience: {data['audience']}
- Audience pain points: {data['pain_points']}
- Before → After transformation: {data['before_after']}
- 3 tips / wins inside my product: {data['tips']}
- 3 mistakes my audience makes: {data['mistakes']}
- Call to action phrase: {data['cta']}
- Website / link: {data['link'] or '[YOUR LINK HERE]'}

GENERATE THESE 5 SCRIPT TYPES (one script per type):
1. Problem → Promise
2. 3 Mistakes
3. Before → After
4. Myth vs Truth
5. Fast Tip → Sell

FORMAT RULES (apply to every script):
- Plain text ONLY. No markdown, no asterisks, no bold, no italics, no emojis.
- {SCRIPT_MIN_WORDS}–{SCRIPT_MAX_WORDS} words of spoken dialogue per script (complete scripts, no truncation).
- Every script must end by speaking the exact CTA phrase and website link word for word.
- Use these section labels with a delivery cue in square brackets after each label.
  Example: HOOK: [pause 1 sec] Your opening line here...
- Delivery cues are stage directions only — not spoken aloud.
- At the top of each script add: "Note: Text in [brackets] are delivery cues — do not read these aloud."
- Problem → Promise must use a product-specific PIVOT (not generic "what if there was a way").
- Problem → Promise must merge PROMISE + PROOF TEASE into one punchy line using the actual tips above.
- 3 Mistakes must use the three mistakes listed above.
- Myth vs Truth and Fast Tip → Sell must reference the actual tips listed above.

Write each script to sound human, relatable, and confident. No corporate language."""


def build_folder_readme(data: dict) -> str:
    return f"""CONTENT FOLDER — {data['title']}
Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
==============================================

FOLDER CONTENTS:

📁 HeyGen_Motion_Prompts/
   - 5 custom motion prompts (auto-applied per video)

📁 Avatar_Video/
   - HeyGen talking-head workflow guide
   - Settings for Reels/TikTok/Shorts format

📁 Images/
   - 15 image concept ideas
   - Higgsfield animation workflow
   - Color palette suggestions

📄 ChatGPT_Reuse_Prompt.txt
   - Reusable template to generate more scripts anytime

PRODUCT DETAILS:
- Title: {data['title']}
- Audience: {data['audience']}
- CTA: {data['cta']}
- Link: {data['link']}
"""