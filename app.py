import streamlit as st
import os
from dotenv import load_dotenv
from services.ai_generator import generate_all_content
from services.file_manager import save_outputs, get_output_folder
from services.pdf_generator import generate_pdf
from services.zip_manager import create_zip

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

st.set_page_config(
    page_title="Content Creator Automation",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
</style>
""", unsafe_allow_html=True)

# Sidebar 
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("### 📋 What This Generates")
    st.markdown("""
- ✅ 5 short-form video scripts  
- ✅ Cinematic B-roll prompts  
- ✅ Talking head guide  
- ✅ Image style guide  
- ✅ Organized output folders  
- ✅ PDF export  
- ✅ ZIP download  
""")
    st.markdown("---")
    st.caption("Built for DigitalProductsCreators.com")

# header
st.markdown('<p class="main-title">🎬 Content Creator Automation</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Generate 5 marketing video scripts + B-roll prompts for your digital product</p>', unsafe_allow_html=True)
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

    st.markdown("### 💡 Content Details")
    col5, col6 = st.columns(2)
    with col5:
        tips = st.text_area("3 Quick Tips / Wins Inside Your Product *",
                             placeholder="Tip 1: ...\nTip 2: ...\nTip 3: ...",
                             height=100)
    with col6:
        mistakes = st.text_area("3 Common Mistakes Your Audience Makes *",
                                 placeholder="Mistake 1: ...\nMistake 2: ...\nMistake 3: ...",
                                 height=100)

    submitted = st.form_submit_button("🚀 Generate All Content", use_container_width=True, type="primary")

# generation logic
if submitted:
    # Validation
    required = {
        "eBook Title": ebook_title,
        "Target Audience": target_audience,
        "Product Description": ebook_description,
        "Pain Points": pain_points,
        "Tips": tips,
        "Mistakes": mistakes,
        "Before/After": before_after,
        "CTA Phrase": cta_phrase,
    }
    missing = [k for k, v in required.items() if not v.strip()]
    if missing:
        st.error(f"Please fill in: {', '.join(missing)}")
        st.stop()

    if not API_KEY:
        st.error("Service not configured. Please contact the administrator.")
        st.stop()

    product_data = {
        "title": ebook_title.strip(),
        "description": ebook_description.strip(),
        "audience": target_audience.strip(),
        "pain_points": pain_points.strip(),
        "tips": tips.strip(),
        "mistakes": mistakes.strip(),
        "before_after": before_after.strip(),
        "cta": cta_phrase.strip(),
        "link": website_link.strip(),
    }

    # Generate content
    with st.spinner("🤖 Generating your scripts and B-roll prompts..."):
        try:
            results = generate_all_content(product_data, api_key=API_KEY, model=MODEL)
            st.session_state["results"] = results
            st.session_state["product_data"] = product_data
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.stop()

    # Save files
    with st.spinner("💾 Saving files to output folder..."):
        output_folder = save_outputs(results, product_data)
        st.session_state["output_folder"] = output_folder

    st.success("✅ Content generated successfully!")

# Results Display 
if "results" in st.session_state:
    results = st.session_state["results"]
    product_data = st.session_state["product_data"]
    output_folder = st.session_state.get("output_folder", "")

    st.markdown("---")
    st.markdown("## 📄 Generated Content")

    scripts = results.get("scripts", {})
    broll = results.get("broll", {})
    extras = results.get("extras", {})

    script_names = [
        ("problem_promise", "1️⃣ Problem → Promise"),
        ("three_mistakes", "2️⃣ 3 Mistakes"),
        ("before_after", "3️⃣ Before → After"),
        ("myth_truth", "4️⃣ Myth vs Truth"),
        ("fast_tip", "5️⃣ Fast Tip → Sell"),
    ]

    tabs = st.tabs(["📝 Scripts", "🎬 B-Roll Prompts", "📋 Extras", "⬇️ Downloads"])

    # ── Scripts Tab ───────────────────────────────────────────────────────────
    with tabs[0]:
        for key, label in script_names:
            if key in scripts:
                with st.expander(label, expanded=False):
                    st.text_area("", scripts[key], height=300, key=f"script_{key}", label_visibility="collapsed")

    # ── B-Roll Tab ────────────────────────────────────────────────────────────
    with tabs[1]:
        for key, label in script_names:
            broll_key = f"broll_{key}"
            if broll_key in broll:
                with st.expander(f"🎥 {label} — B-Roll Prompts", expanded=False):
                    st.text_area("", broll[broll_key], height=250, key=broll_key, label_visibility="collapsed")

    # ── Extras Tab ────────────────────────────────────────────────────────────
    with tabs[2]:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🎤 Talking Head Guide")
            st.text_area("", extras.get("talking_head", ""), height=300,
                         key="talking_head", label_visibility="collapsed")
        with col_b:
            st.markdown("#### 🖼️ Image Style Guide")
            st.text_area("", extras.get("image_guide", ""), height=300,
                         key="image_guide", label_visibility="collapsed")

    # ── Downloads Tab ─────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("### ⬇️ Download Your Content")
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            st.markdown("#### 📄 PDF Export")
            with st.spinner("Generating PDF..."):
                try:
                    pdf_bytes = generate_pdf(results, product_data)
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"{product_data['title'].replace(' ', '_')}_content.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")

        with col_d2:
            st.markdown("#### 📦 ZIP Export")
            if output_folder and os.path.exists(output_folder):
                with st.spinner("Creating ZIP..."):
                    try:
                        zip_bytes = create_zip(output_folder)
                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_bytes,
                            file_name=f"{product_data['title'].replace(' ', '_')}_content.zip",
                            mime="application/zip",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"ZIP creation failed: {e}")

        st.markdown("---")
        st.markdown("#### 📁 Individual Script Downloads")
        for key, label in script_names:
            if key in scripts:
                st.download_button(
                    label=f"⬇️ {label}",
                    data=scripts[key],
                    file_name=f"{key}_script.txt",
                    mime="text/plain",
                    key=f"dl_{key}",
                )