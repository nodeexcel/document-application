import base64
import io
import json
import os
import zipfile

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from services.ai_generator import generate_all_content
from services.file_manager import save_outputs
from services.pdf_generator import generate_pdf
from services.zip_manager import create_zip
from services.avatar_registry import pick_unique_avatar_ids
from services.heygen_client import (
    is_heygen_configured,
    start_talking_head_videos_parallel,
    complete_talking_head_videos_parallel,
)
from services.video_store import (
    get_video_bytes,
    video_is_ready,
    merge_session_videos,
    persist_video,
    save_manifest,
)
from services.output_cleanup import (
    delete_output_folder_silent,
    get_streamlit_session_id,
    register_session_output_folder,
    run_startup_cleanup_once,
    try_cleanup_session_output_folder,
)

load_dotenv()
run_startup_cleanup_once()
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

SCRIPT_NAMES = [
    ("problem_promise", "1️⃣ Problem → Promise"),
    ("three_mistakes", "2️⃣ 3 Mistakes"),
    ("before_after", "3️⃣ Before → After"),
    ("myth_truth", "4️⃣ Myth vs Truth"),
    ("fast_tip", "5️⃣ Fast Tip → Sell"),
]

# Plain (emoji-free) topic names for download button labels.
TOPIC_PLAIN = {
    "problem_promise": "Problem to Promise",
    "three_mistakes": "3 Mistakes",
    "before_after": "Before to After",
    "myth_truth": "Myth vs Truth",
    "fast_tip": "Fast Tip to Sell",
}
VIDEO_NUMBER = {key: idx for idx, (key, _label) in enumerate(SCRIPT_NAMES, start=1)}

# Preview width — phone-style 9:16 frame for Reels/TikTok/Shorts (~280px wide).
VIDEO_PREVIEW_MAX_WIDTH_PX = 280


def _inject_exclusive_video_playback() -> None:
    """Pause other players when one video starts — HTML5 videos are independent by default."""
    components.html(
        """
        <script>
        (function () {
          function findAppWindow(start) {
            var w = start;
            for (var i = 0; i < 8; i++) {
              try {
                var doc = w.document;
                if (doc && (doc.querySelector('[data-testid="stApp"]') || doc.querySelector('[data-testid="stVideo"]'))) {
                  return w;
                }
                if (w.parent && w.parent !== w) {
                  w = w.parent;
                } else {
                  break;
                }
              } catch (e) {
                break;
              }
            }
            return start.parent || start;
          }

          function pauseOthers(active) {
            var root = findAppWindow(window).document;
            root.querySelectorAll('[data-testid="stVideo"] video').forEach(function (other) {
              if (other !== active && !other.paused) {
                other.pause();
              }
            });
          }

          function bind(appWin) {
            if (!appWin || appWin.__exclusiveVideoPlaybackInstalled) return;
            appWin.__exclusiveVideoPlaybackInstalled = true;
            var root = appWin.document;
            root.addEventListener("play", function (event) {
              var video = event.target;
              if (!video || video.tagName !== "VIDEO") return;
              if (!video.closest('[data-testid="stVideo"]')) return;
              pauseOthers(video);
            }, true);
            root.addEventListener("playing", function (event) {
              var video = event.target;
              if (!video || video.tagName !== "VIDEO") return;
              if (!video.closest('[data-testid="stVideo"]')) return;
              pauseOthers(video);
            }, true);
          }

          bind(findAppWindow(window));
        })();
        </script>
        """,
        height=1,
    )


def _copy_to_clipboard_button(text: str, button_key: str) -> None:
    """Render a Copy to Clipboard button via browser clipboard API."""
    html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;">
<button id="{button_key}" style="
    background-color: #7c3aed; color: white; border: none; border-radius: 6px;
    padding: 0.5rem 1rem; font-size: 0.9rem; cursor: pointer; width: 100%;
">Copy to Clipboard</button>
<script>
document.getElementById("{button_key}").addEventListener("click", function() {{
    navigator.clipboard.writeText({json.dumps(text)});
    this.textContent = "Copied!";
    setTimeout(() => {{ this.textContent = "Copy to Clipboard"; }}, 2000);
}});
</script>
</body></html>"""
    src = "data:text/html;base64," + base64.b64encode(html_doc.encode("utf-8")).decode("ascii")
    st.iframe(src, height=45)


def _zip_videos(videos: dict) -> bytes:
    """Bundle all ready video MP4s into a single ZIP archive."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for key, _label in SCRIPT_NAMES:
            video = videos.get(key)
            data = get_video_bytes(video)
            if data:
                zf.writestr(f"{key}_video.mp4", data)
    buffer.seek(0)
    return buffer.read()


def _video_grid_slots(items, cols_per_row: int = 2) -> dict:
    """Create a responsive grid of empty placeholders, one per video."""
    slots = {}
    for i in range(0, len(items), cols_per_row):
        row = items[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, (key, _label) in enumerate(row):
            slots[key] = cols[idx].empty()
    return slots


def _videos_still_generating() -> bool:
    return bool(st.session_state.get("videos_generating"))


def _all_videos_done(videos: dict, script_keys: list[str]) -> bool:
    for key in script_keys:
        entry = videos.get(key)
        if not entry:
            return False
        if entry.get("error"):
            continue
        if not video_is_ready(entry):
            return False
    return True


def _video_slot_state(video: dict | None) -> str:
    if not video:
        return "waiting"
    if video.get("error"):
        return "error"
    if video.get("video_id") and not video_is_ready(video):
        return "generating"
    if video_is_ready(video):
        return "ready"
    return "waiting"


def _ensure_video_generation_resumed(script_keys: list[str]) -> None:
    """If a batch was interrupted, keep generating until every slot is done or failed."""
    if not script_keys or not is_heygen_configured():
        return
    videos = st.session_state.get("videos") or {}
    if not _all_videos_done(videos, script_keys):
        st.session_state["videos_generating"] = True


def _paint_video_slot(
    slot,
    key: str,
    label: str,
    state: str,
    video: dict | None = None,
) -> None:
    """Replace a video card slot with a single state (waiting/generating/ready/error)."""
    with slot.container():
        with st.container(border=True):
            st.markdown(f'<div class="video-card-label">{label}</div>', unsafe_allow_html=True)
            if state == "waiting":
                st.info("⏳ Waiting…")
            elif state == "generating":
                st.info("🎬 Generating your video, please wait…")
            elif state == "error":
                st.warning(f"Video generation failed: {video.get('error', 'Unknown error') if video else 'Unknown error'}")
            elif state == "ready" and video:
                data = get_video_bytes(video)
                if data:
                    st.video(data)
                    st.download_button(
                        "⬇️ Download Video",
                        data=data,
                        file_name=f"{key}_video.mp4",
                        mime="video/mp4",
                        key=f"dl_video_{key}",
                        use_container_width=True,
                    )
                else:
                    st.warning("Video file not found — try refreshing the page.")


def render_videos_tab(
    scripts: dict,
    motion_prompts: dict,
    product_data: dict | None = None,
) -> None:
    if not is_heygen_configured():
        st.info("Video generation not configured yet")
        return

    items = [(k, l) for k, l in SCRIPT_NAMES if k in scripts]
    if not items:
        st.info("No content available to generate videos from.")
        return

    _inject_exclusive_video_playback()
    script_keys = [key for key, _label in items]
    output_folder = st.session_state.get("output_folder", "")
    videos: dict = merge_session_videos(output_folder, st.session_state.get("videos"))
    st.session_state["videos"] = videos
    slots = _video_grid_slots(items)

    if not _videos_still_generating():
        for key, label in items:
            video = videos.get(key)
            _paint_video_slot(slots[key], key, label, _video_slot_state(video), video)
        return

    avatar_ids = st.session_state.get("avatar_ids")
    if not avatar_ids or len(avatar_ids) < len(items):
        avatar_ids = pick_unique_avatar_ids(len(items))
        st.session_state["avatar_ids"] = avatar_ids

    # Paint current state for all slots
    for key, label in items:
        video = videos.get(key)
        _paint_video_slot(slots[key], key, label, _video_slot_state(video), video)

    # ── Phase 1: submit all pending jobs concurrently ─────────────────────────
    submit_jobs: list[tuple[str, str, str | None, str | None]] = []
    for index, (key, _label) in enumerate(items):
        existing = videos.get(key)
        if video_is_ready(existing) or (existing and existing.get("error")):
            continue
        if existing and existing.get("video_id"):
            continue
        submit_jobs.append((
            key,
            scripts[key],
            avatar_ids[index],
            motion_prompts.get(key, ""),
        ))

    if submit_jobs:
        labels = dict(items)
        for key, _, _, _ in submit_jobs:
            _paint_video_slot(slots[key], key, labels[key], "generating")

        submitted = start_talking_head_videos_parallel(submit_jobs)
        for key, pending in submitted.items():
            videos[key] = pending
        st.session_state["videos"] = dict(videos)
        if output_folder:
            save_manifest(output_folder, videos)

    # ── Phase 2: poll & download all in-flight jobs concurrently ──────────────
    pending_keys = {
        key: videos[key]
        for key, _ in items
        if videos.get(key, {}).get("video_id") and not video_is_ready(videos.get(key))
        and not videos.get(key, {}).get("error")
    }

    if pending_keys:
        for key in pending_keys:
            label = next(lbl for k, lbl in items if k == key)
            _paint_video_slot(slots[key], key, label, "generating", videos.get(key))

        completed = complete_talking_head_videos_parallel(pending_keys)
        for key, video in completed.items():
            if output_folder and video_is_ready(video):
                video = persist_video(output_folder, key, video, videos)
            videos[key] = video
            label = next(lbl for k, lbl in items if k == key)
            state = "ready" if video_is_ready(video) else "error"
            _paint_video_slot(slots[key], key, label, state, video)

        st.session_state["videos"] = dict(videos)

    if _all_videos_done(videos, script_keys):
        st.session_state["videos_generating"] = False
        st.rerun()


def render_download_video_slot(slot, key: str, video: dict | None) -> None:
    """Render a single video's download row in the Downloads tab."""
    idx = VIDEO_NUMBER.get(key, 0)
    topic = TOPIC_PLAIN.get(key, key)
    data = get_video_bytes(video)
    with slot.container():
        if data:
            st.download_button(
                f"⬇️ Download Video {idx} — {topic}",
                data=data,
                file_name=f"{key}_video.mp4",
                mime="video/mp4",
                key=f"dl_dl_video_{key}_ready",
                use_container_width=True,
            )
        elif video and video.get("error"):
            st.button(
                f"⚠️ Video {idx} — {topic} (generation failed)",
                disabled=True,
                key=f"dl_dl_failed_{key}",
                use_container_width=True,
            )
        elif video and video.get("video_id"):
            st.button(
                f"⏳ Video {idx} — {topic} (generating…)",
                disabled=True,
                key=f"dl_dl_pending_{key}",
                use_container_width=True,
            )
        else:
            st.button(
                f"⏳ Video {idx} — {topic} (waiting…)",
                disabled=True,
                key=f"dl_dl_waiting_{key}",
                use_container_width=True,
            )



def render_all_videos_button(slot, videos: dict, product_data: dict, *, live_update: bool = False) -> None:
    """Render the 'Download All Videos (ZIP)' control."""
    safe_title = product_data["title"].replace(" ", "_")
    ready_count = sum(1 for v in videos.values() if video_is_ready(v))
    zip_key = f"dl_all_videos_zip_{ready_count}" if live_update else "dl_all_videos_zip"
    with slot.container():
        if ready_count:
            st.download_button(
                "⬇️ Download All Videos (ZIP)",
                data=_zip_videos(videos),
                file_name=f"{safe_title}_videos.zip",
                mime="application/zip",
                key=zip_key,
                use_container_width=True,
            )
        else:
            st.button(
                "⏳ Download All Videos (ZIP) — no videos ready yet",
                disabled=True,
                key="dl_all_videos_pending",
                use_container_width=True,
            )


@st.fragment
def _downloads_videos_section(product_data: dict) -> None:
    """Video download rows — fragment isolates reruns when a download button is clicked."""
    output_folder = st.session_state.get("output_folder", "")
    videos = merge_session_videos(output_folder, st.session_state.get("videos"))
    all_videos_slot = st.empty()
    render_all_videos_button(all_videos_slot, videos, product_data)
    for key, _label in SCRIPT_NAMES:
        slot = st.empty()
        render_download_video_slot(slot, key, videos.get(key))


def render_downloads_tab(results: dict, product_data: dict, output_folder: str) -> None:
    """Render the Downloads tab."""
    st.markdown("### ⬇️ Download Your Content")

    safe_title = product_data["title"].replace(" ", "_")

    # ── Videos (fragment — download clicks won't reload the Videos tab players) ─
    st.markdown("#### 🎥 Videos")
    if not is_heygen_configured():
        st.info("Video generation not configured yet")
    else:
        _downloads_videos_section(product_data)

    st.markdown("---")

    # ── Supporting content (no scripts) ───────────────────────────────────────
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("#### 📄 PDF Export")
        st.caption("Guides and export bundle (no scripts).")
        with st.spinner("Generating PDF..."):
            try:
                pdf_bytes = generate_pdf(results, product_data)
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"{safe_title}_content.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    with col_d2:
        st.markdown("#### 📦 ZIP Export")
        st.caption("Guides and export bundle (no scripts).")
        if output_folder and os.path.exists(output_folder):
            with st.spinner("Creating ZIP..."):
                try:
                    zip_bytes = create_zip(output_folder)
                    st.download_button(
                        label="⬇️ Download ZIP",
                        data=zip_bytes,
                        file_name=f"{safe_title}_content.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"ZIP creation failed: {e}")


st.set_page_config(
    page_title="Content Creator Automation",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

_session_id = get_streamlit_session_id()
if "results" not in st.session_state:
    try_cleanup_session_output_folder(_session_id)

if not st.session_state.get("_exclusive_playback_injected"):
    st.session_state["_exclusive_playback_injected"] = True

st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; }
    .main-title { font-size: 2.4rem; font-weight: 800; color: #ffffff; margin-bottom: 0; }
    .sub-title { font-size: 1rem; color: #aaaaaa; margin-top: 0; }
    .section-label { font-size: 0.85rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.08em; }
    .stTabs [data-baseweb="tab"] { color: #aaa; }
    .stTabs [aria-selected="true"] { color: #fff; border-bottom: 2px solid #7c3aed; }
    .output-box { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem; }
    div[data-testid="stExpander"] { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; }
    /* Video cards: phone-style 9:16 preview (~280px), centered like Reels/TikTok */
    .video-card-label { font-size: 0.95rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem; }
    div[data-testid="stVideo"] {
        display: flex;
        justify-content: center;
        margin: 0 auto;
        max-width: 280px;
    }
    div[data-testid="stVideo"] video {
        width: 280px;
        height: 498px;
        max-width: 280px;
        aspect-ratio: 9 / 16;
        object-fit: cover;
        object-position: center top;
        border-radius: 12px;
        background: #000000;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVideo"]) {
        max-width: 300px;
        margin-left: auto;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("### 📋 What This Generates")
    st.markdown("""
- ✅ 5 HeyGen talking-head videos  
- ✅ Avatar video guide  
- ✅ Image style guide  
- ✅ PDF & ZIP export  
""")
    st.markdown("---")
    st.caption("Built for DigitalProductsCreators.com")

# header
st.markdown('<p class="main-title">🎬 Content Creator Automation</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Generate 5 HeyGen talking-head videos and export guides</p>', unsafe_allow_html=True)
st.markdown("---")

# Input Form
with st.form("product_form"):
    st.markdown("### 📦 Your Digital Product")

    col1, col2 = st.columns(2)
    with col1:
        ebook_title = st.text_input("eBook / Product Title *", placeholder="e.g. The 5-Day Clarity Method")
        target_audience = st.text_input("Target Audience *", placeholder="e.g. Busy moms who want to start an online business")
    with col2:
        cta_phrase = st.text_input("Call to Action Phrase *", placeholder="e.g. Grab your free copy now")
        website_link = st.text_input("Website / Link", placeholder="e.g. https://yourdomain.com")

    ebook_description = st.text_area("Product Description *",
                                      placeholder="Describe what your eBook/product is about and what problem it solves...",
                                      height=100)

    st.markdown("### 🎯 Audience & Transformation")
    col3, col4 = st.columns(2)
    with col3:
        pain_points = st.text_area("Audience Pain Points *",
                                    placeholder="What struggles does your audience have? (one per line)",
                                    height=100)
    with col4:
        before_after = st.text_area("Before → After Transformation *",
                                     placeholder="Before: [struggling with X]\nAfter: [now achieving Y]",
                                     height=100)

    submitted = st.form_submit_button("🚀 Generate All Content", use_container_width=True, type="primary")

# Validation/status messages render through this placeholder so a stale warning
# is reclaimed and cleared instantly on the next click (before any long work).
validation_msg = st.empty()

# generation logic — two-phase so a re-run clears stale videos/errors before long work
if submitted:
    validation_msg.empty()
    required = {
        "eBook Title": ebook_title,
        "Target Audience": target_audience,
        "Product Description": ebook_description,
        "Pain Points": pain_points,
        "Before/After": before_after,
        "CTA Phrase": cta_phrase,
    }
    missing = [k for k, v in required.items() if not v.strip()]
    if missing:
        validation_msg.error(f"Please fill in: {', '.join(missing)}")
        st.stop()

    if not API_KEY:
        validation_msg.error("Service not configured. Please contact the administrator.")
        st.stop()

    product_data = {
        "title": ebook_title.strip(),
        "description": ebook_description.strip(),
        "audience": target_audience.strip(),
        "pain_points": pain_points.strip(),
        "before_after": before_after.strip(),
        "cta": cta_phrase.strip(),
        "link": website_link.strip(),
    }

    # Wipe previous output and show a clean generating screen on the next run.
    st.session_state.pop("videos", None)
    st.session_state.pop("results", None)
    st.session_state.pop("videos_generating", None)
    st.session_state.pop("just_generated", None)
    st.session_state["product_data"] = product_data
    st.session_state["generating"] = True
    st.session_state["regenerate"] = True
    st.rerun()

if st.session_state.get("generating"):
    if st.session_state.pop("regenerate", False):
        product_data = st.session_state["product_data"]
        with st.status("⏳ Generating content…", expanded=True) as status:
            st.write("🤖 Writing scripts with AI…")
            try:
                results = generate_all_content(product_data, api_key=API_KEY, model=MODEL)
                st.session_state["results"] = results
            except Exception as e:
                st.session_state.pop("generating", None)
                status.update(label="Generation failed", state="error")
                st.error(f"Generation failed: {e}")
                st.stop()

            st.write("💾 Saving guides and prompts…")
            prev_folder = st.session_state.get("output_folder")
            output_folder = save_outputs(results, product_data)
            st.session_state["output_folder"] = output_folder
            register_session_output_folder(_session_id, output_folder)
            if prev_folder and prev_folder != output_folder:
                delete_output_folder_silent(prev_folder)

            status.update(label="✅ Scripts ready — starting video generation…", state="complete")

        st.session_state.pop("videos", None)
        st.session_state.pop("generating", None)
        st.session_state["videos_generating"] = True
        st.session_state["just_generated"] = True
        st.rerun()
    else:
        with st.status("⏳ Generating content…", expanded=True):
            st.write("Please wait…")
        st.stop()

# Results Display
if "results" in st.session_state and not st.session_state.get("generating"):
    results = st.session_state["results"]
    product_data = st.session_state["product_data"]
    output_folder = st.session_state.get("output_folder", "")
    just_generated = st.session_state.pop("just_generated", False)

    output_folder = st.session_state.get("output_folder", "")
    st.session_state["videos"] = merge_session_videos(
        output_folder, st.session_state.get("videos")
    )

    scripts = results.get("scripts", {})
    motion_prompts = results.get("motion_prompts", {})
    extras = results.get("extras", {})

    st.markdown("---")
    st.markdown("## 🎥 Your Videos")
    if just_generated:
        st.success("✅ Scripts ready — generating your videos below (all 5 in parallel)…")

    if _videos_still_generating():
        st.info("⏳ Videos are generating in parallel — each one becomes available as soon as it's ready.")

    script_keys = [key for key, _ in SCRIPT_NAMES if key in scripts]
    _ensure_video_generation_resumed(script_keys)

    tabs = st.tabs(["🎥 Videos", "📋 Extras", "⬇️ Downloads"])

    # NOTE: Extras and Downloads tabs are populated FIRST so they render immediately
    # while the blocking HeyGen video loop runs. Videos tab is LAST.

    # ── Extras Tab ──────────────────────────────────────────────────────────
    with tabs[1]:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🎤 Avatar Video Guide")
            st.text_area("Content", extras.get("avatar_guide", ""), height=300,
                         key="avatar_guide", label_visibility="collapsed")
        with col_b:
            st.markdown("#### 🖼️ Image Style Guide")
            st.text_area("Content", extras.get("image_guide", ""), height=300,
                         key="image_guide", label_visibility="collapsed")

        st.markdown("---")
        st.markdown("#### 💬 ChatGPT Prompt Template")
        st.caption(
            "Copy this prompt into ChatGPT anytime to generate more scripts for your product "
            "without using this app."
        )
        chatgpt_template = extras.get("chatgpt_template", "")
        st.text_area(
            "Content",
            chatgpt_template,
            height=320,
            key="chatgpt_template",
            label_visibility="collapsed",
        )
        _copy_to_clipboard_button(chatgpt_template, "copy_chatgpt_template")

    # ── Downloads Tab ───────────────────────────────────────────────────────
    with tabs[2]:
        render_downloads_tab(results, product_data, output_folder)

    # ── Videos Tab (resumable generation — survives page reruns) ─────────────
    with tabs[0]:
        render_videos_tab(scripts, motion_prompts, product_data)
