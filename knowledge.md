# Knowledge — Content Creator Automation

> **Cursor Instructions:**
>
> - Always read this file before making changes.
> - Whenever a feature is added, modified, or removed, update this file.
> - Keep feature descriptions synchronized with the implementation.
> - Document newly created files, folders, APIs, services, and workflows.
> - Update execution flows whenever system behavior changes.
> - Remove outdated information.
> - Treat this file as the project's source of truth.

---

## 1. Project Overview

**Content Creator Automation** is a Streamlit web app that helps digital‑product creators generate a complete short‑form marketing content kit from a single product brief.

Given one product (title, description, audience, pain points, tips, mistakes, transformation, CTA, link), the app uses the OpenAI Chat Completions API to produce:

- 5 short‑form video scripts (Reels / TikTok / YouTube Shorts) using 5 different proven formulas.
- 5 matching sets of cinematic B‑roll / AI‑video prompts (Kling, Runway, Veo).
- A personalised "Talking Head" guide (HeyGen workflow).
- A personalised "Image Style" guide (Higgsfield workflow + palettes).
- Per‑file downloads, a combined PDF export, and a ZIP of the output folder.

Built for `DigitalProductsCreators.com`.

---

## 2. Folder Structure

```
desktop-automation/
├── app.py                  # Streamlit UI + orchestration
├── requirements.txt        # Python dependencies
├── README.md               # (empty placeholder)
├── .env                    # Local secrets (OPENAI_API_KEY)
├── .env.example            # (empty placeholder)
├── assets/                 # Static assets (currently empty)
├── outputs/                # Generated content folders (one per run)
├── prompts/
│   ├── __init__.py
│   ├── script_prompts.py   # 5 script-template prompt builders
│   └── broll_prompts.py    # 5 B-roll prompt builders
├── services/
│   ├── __init__.py
│   ├── ai_generator.py     # OpenAI calls + static guides + orchestrator
│   ├── file_manager.py     # (STUB — empty)
│   ├── pdf_generator.py    # (STUB — empty)
│   └── zip_manager.py      # (STUB — empty)
└── venv/                   # Local virtual environment (not committed)
```

---

## 3. Features

Each feature below lists: **Purpose / Input / Output / Flow / Related files**.

### 3.1 Product Brief Form

- **Purpose:** Collect every piece of product context needed to generate scripts and visuals.
- **Input (UI fields):**
  - `ebook_title`, `target_audience`, `cta_phrase`, `website_link`
  - `ebook_description`
  - `pain_points`, `before_after`
  - `tips`, `mistakes`
- **Output:** A validated `product_data` dict with keys: `title, description, audience, pain_points, tips, mistakes, before_after, cta, link`.
- **Flow:**
  1. Streamlit form rendered in `app.py`.
  2. On submit, required fields are validated; missing fields short‑circuit with `st.error`.
  3. API key presence is also checked (sidebar or `.env`).
  4. Stripped values are packed into `product_data` and passed downstream.
- **Files:** `app.py` (form block + validation, lines ~55–126).

### 3.2 Script Generation (5 formulas)

- **Purpose:** Produce 5 short‑form video scripts (≈45–90 seconds spoken) using distinct narrative formulas.
- **Formulas (key → label):**
  - `problem_promise` → Problem → Promise
  - `three_mistakes` → 3 Mistakes
  - `before_after` → Before → After
  - `myth_truth` → Myth vs Truth
  - `fast_tip` → Fast Tip → Sell
- **Input:** `product_data` dict, OpenAI `api_key`, `model` (default `gpt-4o-mini`).
- **Output:** `scripts: dict[str, str]` keyed by formula name, containing HOOK / BODY / CTA text.
- **Flow:**
  1. `generate_all_content` builds an `OpenAI` client.
  2. Loads system prompt via `get_system_prompt()` from `prompts/script_prompts.py`.
  3. For each formula, calls the matching `*_prompt(data)` builder to assemble a user prompt.
  4. `call_openai(...)` sends the request (`temperature=0.85`, `max_tokens=1200`) with exponential‑backoff retries (default 2).
  5. Result text is stored under `scripts[key]`.
- **Files:**
  - `services/ai_generator.py` — `call_openai`, `generate_all_content`
  - `prompts/script_prompts.py` — system prompt + 5 builders

### 3.3 B‑Roll / AI Video Prompts (5 sets)

- **Purpose:** For each script, generate a matching set of cinematic AI‑video prompts ready to paste into Kling / Runway / Veo.
- **Input:** Same `product_data` plus the just‑generated `scripts[key]` text (truncated to first 600 chars as context).
- **Output:** `broll: dict[str, str]` with keys `broll_problem_promise`, `broll_three_mistakes`, `broll_before_after`, `broll_myth_truth`, `broll_fast_tip` (note: Before→After produces 6 scenes; others produce 5).
- **Flow:**
  1. `get_broll_system_prompt()` provides the cinematic director system message.
  2. Each `broll_for_*` builder takes `(data, script)` and returns the scene‑labelled prompt.
  3. Same `call_openai` helper is reused for the call.
- **Files:**
  - `services/ai_generator.py` (B‑roll loop in `generate_all_content`)
  - `prompts/broll_prompts.py`

### 3.4 Static Personalised Extras

- **Purpose:** Provide ready‑to‑use workflow guides personalised with the user's product data — without burning OpenAI tokens.
- **Outputs:** `extras = { "talking_head": str, "image_guide": str }`.
  - **Talking Head Guide:** HeyGen end‑to‑end workflow (avatar, voice, 9:16 export, CapCut captions) with the product title, audience, CTA, and link interpolated.
  - **Image Style Guide:** 15 concrete image concepts, a Higgsfield animation recipe, 3 colour‑palette options, and a text‑overlay template.
- **Flow:** Pure string interpolation in `generate_talking_head_guide(data)` and `generate_image_guide(data)`; no network calls.
- **Files:** `services/ai_generator.py` (functions at lines ~42 and ~91).

### 3.5 Results Display (tabbed UI)

- **Purpose:** Surface all generated artefacts in a scannable, copyable interface.
- **Input:** `st.session_state["results"]` (from generation step).
- **Output:** Four Streamlit tabs:
  - **Scripts** — one expander per formula, each with an editable text area.
  - **B‑Roll Prompts** — same layout, one expander per script's prompt set.
  - **Extras** — two columns: Talking Head Guide and Image Style Guide.
  - **Downloads** — PDF, ZIP, and per‑script `.txt` download buttons.
- **Flow:** After `submitted`, results are cached in `st.session_state`; the display block re‑renders on every interaction without re‑calling OpenAI.
- **Files:** `app.py` (results block, lines ~146–241).

### 3.6 Output Folder Persistence  *(planned — currently a stub)*

- **Purpose:** Save each generation run to a uniquely named folder under `outputs/` so the user has a permanent file copy.
- **Expected API (called by `app.py`):**
  - `save_outputs(results, product_data) -> str` (returns the created folder path)
  - `get_output_folder(...)` (referenced in the commented import in `app.py`)
- **Current status:** `services/file_manager.py` is **empty**. The import is commented out in `app.py`, so the runtime call `save_outputs(...)` will raise `NameError` on submit until the module is implemented.
- **Files:** `services/file_manager.py`, `outputs/`.

### 3.7 PDF Export  *(planned — currently a stub)*

- **Purpose:** Bundle all scripts + B‑roll prompts + extras into a single, branded PDF.
- **Expected API:** `generate_pdf(results, product_data) -> bytes`.
- **Current status:** `services/pdf_generator.py` is **empty**. `reportlab` is already listed in `requirements.txt` for this purpose. The download button in `app.py` is wrapped in `try/except`, so failure surfaces as an `st.error` rather than crashing the tab — but generation itself will not run.
- **Files:** `services/pdf_generator.py`, `app.py` (Downloads tab).

### 3.8 ZIP Export  *(planned — currently a stub)*

- **Purpose:** Produce an in‑memory ZIP of the run's output folder for one‑click download.
- **Expected API:** `create_zip(output_folder: str) -> bytes`.
- **Current status:** `services/zip_manager.py` is **empty**. Same `try/except` safety net in `app.py`.
- **Files:** `services/zip_manager.py`, `app.py` (Downloads tab).

### 3.9 Per‑Script Text Downloads

- **Purpose:** Quick `.txt` download of any individual script without needing the full ZIP/PDF.
- **Flow:** Iterates `script_names` and emits a `st.download_button` per script with `mime="text/plain"`.
- **Files:** `app.py` (bottom of Downloads tab).

---

## 4. Data Flow

```
User (browser)
   │  fills product brief + clicks "Generate"
   ▼
app.py  ── validates, builds product_data ──► services/ai_generator.generate_all_content
                                                  │
                                                  │ for each of 5 script formulas:
                                                  │   prompts/script_prompts.<formula>_prompt(data)
                                                  │   call_openai(client, sys_script, user, model)
                                                  │
                                                  │ for each of 5 B-roll sets:
                                                  │   prompts/broll_prompts.broll_for_<formula>(data, script)
                                                  │   call_openai(client, sys_broll, user, model)
                                                  │
                                                  │ generate_talking_head_guide(data)   # local
                                                  │ generate_image_guide(data)          # local
                                                  ▼
                                       results = {scripts, broll, extras}
                                                  │
app.py  ── save_outputs(results, product_data) ──► services/file_manager (STUB)
                                                  │
                                                  ▼
                                       output_folder path (planned)
                                                  │
app.py  ── render tabs from st.session_state["results"]
        ── generate_pdf(...)  ──► services/pdf_generator (STUB)
        ── create_zip(folder) ──► services/zip_manager   (STUB)
        ── per‑script download_button
```

State that survives reruns lives in `st.session_state` under: `results`, `product_data`, `output_folder`.

---

## 5. APIs, Services, and Integrations

- **OpenAI Chat Completions** — `openai>=1.30.0`.
  - Models exposed in the sidebar: `gpt-4o-mini` (default), `gpt-4o`.
  - Call params: `temperature=0.85`, `max_tokens=1200`.
  - Retry policy: up to 2 retries with `2 ** attempt` second backoff (`call_openai` in `services/ai_generator.py`).
- **Streamlit** — `streamlit>=1.35.0` for the full UI (form, tabs, expanders, download buttons, custom CSS theming).
- **ReportLab** — `reportlab>=4.2.0`, declared for the planned PDF export (not yet wired up).
- **python‑dotenv** — `python-dotenv>=1.0.0`, available for loading `.env` (currently `app.py` reads `OPENAI_API_KEY` directly via `os.getenv`; `load_dotenv()` is not called explicitly).
- **External tools referenced in generated content (not direct integrations):** HeyGen (talking head), Kling / Runway / Veo (AI video), Higgsfield (image‑to‑video), CapCut / Premiere (editing).

---

## 6. Important Business Logic

- **All 5 script formulas are non‑negotiable** — they encode proven short‑form structures (Problem→Promise, 3 Mistakes, Before→After, Myth vs Truth, Fast Tip→Sell). Changing the keys breaks the UI tabs and the B‑roll mapping.
- **B‑roll prompts depend on the corresponding script text** (passed in as `script[:600]`) so visuals stay coherent with copy. Run order matters: scripts first, then B‑roll.
- **Validation is strict:** all fields except `Website / Link` are required. Submission is blocked client‑side until they are filled.
- **API key resolution order:** sidebar text input → `OPENAI_API_KEY` env var. The sidebar input is pre‑filled from the env var.
- **Token / cost shape:** 10 OpenAI calls per "Generate" click (5 scripts + 5 B‑roll). Extras are free (local string templates).
- **Filenames** in downloads use `product_data['title'].replace(' ', '_')` — no further sanitisation, so unusual characters in titles can produce odd filenames.
- **`st.session_state` is the cache.** Re‑renders (e.g. clicking a download button) do not re‑call OpenAI as long as `results` is in session state.

---

## 7. Environment Variables & Configuration

- **`.env`** (local, **do not commit real keys**):
  - `OPENAI_API_KEY` — OpenAI secret key. Used by the sidebar default and by `OpenAI(api_key=...)`.
- **`.env.example`** — currently empty; should mirror the variable names above without values.
- **Sidebar runtime settings (in‑memory only):**
  - `OpenAI API Key` text input (password masked).
  - `Model` selector — `gpt-4o-mini` | `gpt-4o`.
- **Streamlit page config:** title `Content Creator Automation`, icon `🎬`, wide layout, sidebar expanded. Custom dark theme injected via `st.markdown` CSS.

---

## 8. Known Limitations & Assumptions

- **Stub modules.** `services/file_manager.py`, `services/pdf_generator.py`, and `services/zip_manager.py` are empty. Their imports in `app.py` are **commented out**, but the functions (`save_outputs`, `generate_pdf`, `create_zip`) are still **called** unconditionally inside `if submitted:` and the Downloads tab. As shipped, clicking **Generate** will raise `NameError: name 'save_outputs' is not defined`. Implement these modules (and uncomment the imports) before the app is usable end‑to‑end.
- **No `load_dotenv()` call.** `.env` is only honoured if the shell that launches Streamlit already exported the variables, or if `python-dotenv` is invoked elsewhere. Consider adding `from dotenv import load_dotenv; load_dotenv()` at the top of `app.py`.
- **A real `OPENAI_API_KEY` is currently checked into `.env`.** Rotate it and move secrets out of version control.
- **`README.md` and `.env.example` are empty** placeholders.
- **No automated tests** and no `pytest`/lint configuration.
- **No rate‑limit handling beyond simple retries.** Persistent 429s will surface as an `st.error`.
- **No persistence of past runs in the UI** — `outputs/` is the only history once `file_manager` is implemented.
- **Filename sanitisation is minimal** (spaces → underscores only); OS‑illegal characters in product titles can break file writes.
- **Generation is fully synchronous** (10 sequential OpenAI calls), so the spinner can block the UI for tens of seconds.
- **`assets/` and `outputs/` are empty** by default and exist only as conventions.
- **The script formula keys are hard‑coded in three places** (`script_configs` in `ai_generator.py`, `broll_configs` in `ai_generator.py`, and `script_names` in `app.py`). Adding or renaming a formula requires changes in all three.

---

## 9. Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...          # or put it in .env
streamlit run app.py
```

Open the URL Streamlit prints (default `http://localhost:8501`).

---

## 10. Change Log Conventions

When updating this file:

1. Bump or add the relevant subsection under **Features** when behaviour changes.
2. Update **Data Flow** if the orchestration order or session‑state shape changes.
3. Move items from **Known Limitations** to **Features** once implemented.
4. Keep file paths in code references current with the actual repository layout.
