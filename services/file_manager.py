"""
File Manager Service — creates output folder structure and saves all generated content.
"""

import os
import re
from datetime import datetime


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
    """Create the 4-subfolder structure and return paths."""
    folders = {
        "scripts": os.path.join(base_path, "Scripts"),
        "broll": os.path.join(base_path, "Broll_Prompts"),
        "talking_head": os.path.join(base_path, "Talking_Head"),
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

    scripts = results.get("scripts", {})
    broll = results.get("broll", {})
    extras = results.get("extras", {})

    # ── Scripts ───────────────────────────────────────────────────────────────
    script_filenames = {
        "problem_promise": "01_Problem_Promise_Script.txt",
        "three_mistakes": "02_Three_Mistakes_Script.txt",
        "before_after": "03_Before_After_Script.txt",
        "myth_truth": "04_Myth_vs_Truth_Script.txt",
        "fast_tip": "05_Fast_Tip_Sell_Script.txt",
    }

    for key, filename in script_filenames.items():
        if key in scripts:
            write_file(folders["scripts"], filename, scripts[key])

    # ── B-Roll Prompts ────────────────────────────────────────────────────────
    broll_filenames = {
        "broll_problem_promise": "01_Broll_Problem_Promise.txt",
        "broll_three_mistakes": "02_Broll_Three_Mistakes.txt",
        "broll_before_after": "03_Broll_Before_After.txt",
        "broll_myth_truth": "04_Broll_Myth_Truth.txt",
        "broll_fast_tip": "05_Broll_Fast_Tip.txt",
    }

    for key, filename in broll_filenames.items():
        if key in broll:
            write_file(folders["broll"], filename, broll[key])

    # ── Talking Head Guide ────────────────────────────────────────────────────
    if "talking_head" in extras:
        write_file(folders["talking_head"], "HeyGen_Talking_Head_Guide.txt", extras["talking_head"])

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
    return f"""REUSABLE CHATGPT PROMPT TEMPLATE
For: {data['title']}
==============================================

Copy and paste this into ChatGPT anytime you need more scripts.

─── PROMPT ────────────────────────────────────

You are a short-form video scriptwriter for digital product creators.

Write a [SCRIPT TYPE] video script for my digital product.

Product: {data['title']}
Description: {data['description']}
Target audience: {data['audience']}
Their pain points: {data['pain_points']}
3 tips inside my product: {data['tips']}
3 mistakes my audience makes: {data['mistakes']}
Transformation: {data['before_after']}
Call to action: {data['cta']}
Link: {data['link']}

Script types you can use:
- Problem → Promise
- 3 Mistakes  
- Before → After
- Myth vs Truth
- Fast Tip → Sell
- Day in the Life
- Story Time
- Hot Take

Make it 45–90 seconds when spoken. Strong hook, clear value, direct CTA.
Sound human, relatable, and confident. No corporate language.

─── END PROMPT ────────────────────────────────
"""


def build_folder_readme(data: dict) -> str:
    return f"""CONTENT FOLDER — {data['title']}
Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
==============================================

FOLDER CONTENTS:

📁 Scripts/
   - 5 complete video scripts (Problem→Promise, 3 Mistakes, Before→After, Myth vs Truth, Fast Tip→Sell)
   - Ready to paste into HeyGen or record yourself

📁 Broll_Prompts/
   - 5 sets of cinematic B-roll prompts (5–6 scenes each)
   - Optimized for Kling 2.6, Runway, and Veo

📁 Talking_Head/
   - Step-by-step HeyGen guide
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