# 🎬 Content Creator Automation

A Streamlit app that generates **5 short-form marketing video scripts** (~25–30s), **HeyGen talking-head videos** (Avatar V with Avatar IV fallback, full script + lip-sync + custom motion), **HeyGen motion prompts**, **Kling B-roll prompts**, guides, and **PDF/ZIP export** for any digital product — powered by OpenAI + HeyGen.

> **Live App:** [http://116.202.210.102:20157](http://116.202.210.102:20157)

---

## ✨ Features

- **5 video scripts** (65–80 words, ~25–30s): Problem→Promise, 3 Mistakes, Before→After, Myth vs Truth, Fast Tip→Sell
- **5 HeyGen talking-head videos** — full script, AI voice, lip-sync, Avatar V (Avatar IV fallback) + custom motion
- **5 HeyGen motion prompts** — auto-applied per video (lean in, gestures, look at camera)
- **5 Kling B-roll prompts** — cinematic supplementary clips (paste into Kling manually)
- Avatar video guide + image style guide
- Organized output folders per product
- PDF and ZIP export

---

## 🧰 Tech Stack

| Layer | Tool |
|-------|------|
| UI | Streamlit |
| Scripts & prompts | OpenAI (`gpt-4o-mini` default) |
| Talking-head video | HeyGen API v3 (Avatar V → Avatar IV fallback) |
| B-roll (manual) | Kling prompts only — no Kling API integration |
| PDF | ReportLab |
| Runtime | Python 3.12 |
| Deploy | Docker + Docker Compose |

---

## 🚀 Quick Start (Docker — recommended)

### 1. Clone

```bash
git clone https://github.com/nodeexcel/document-application.git
cd document-application
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

- `OPENAI_API_KEY`
- `HEYGEN_API_KEY`
- `HEYGEN_VOICE_ID`
- `config/avatars.json` (photo-avatar look IDs — see below)

### 3. Build and run

```bash
docker compose up -d --build
```

If `docker compose up` fails with `compose compose`, use:

```bash
/usr/libexec/docker/cli-plugins/docker-compose up -d --build
```

App: **http://localhost:20157**

### 4. Stop

```bash
docker compose down
```

---

## 🐳 Docker

| Property | Value |
|----------|-------|
| Base image | `python:3.12-slim` |
| Image | `content-creator-automation:latest` |
| Container | `content-creator` |
| Port | `20157` |
| Restart | `unless-stopped` |
| Volume | `./outputs → /app/outputs` |

```bash
docker compose build
docker compose up -d
docker compose logs -f
docker compose restart
```

---

## 💻 Run Locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add keys
streamlit run app.py --server.port=20157
```

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | Script/prompt model |
| `HEYGEN_API_KEY` | ✅\* | — | HeyGen API key |
| `HEYGEN_VOICE_ID` | ✅\* | — | TTS voice for talking-head |
| `config/avatars.json` | ✅\* | — | Avatar registry (see below) |
| `HEYGEN_ENGINE` | ❌ | `avatar_v` | Primary engine (`avatar_v` or `avatar_iv`) |
| `HEYGEN_ENGINE_FALLBACK` | ❌ | `avatar_iv` | Fallback if Avatar V rejects a look |
| `HEYGEN_RESOLUTION` | ❌ | `720p` | `720p` or `1080p` |
| `HEYGEN_ASPECT_RATIO` | ❌ | `9:16` | Vertical for Reels/Shorts |
| `HEYGEN_EXPRESSIVENESS` | ❌ | `high` | Avatar IV only: `high`, `medium`, or `low` |
| `HEYGEN_MAX_SPOKEN_WORDS` | ❌ | `80` | Hard cap before sending to HeyGen |
| `HEYGEN_POLL_INTERVAL_SEC` | ❌ | `15` | Status poll interval |

\* Required for video generation. Without HeyGen vars, scripts and prompts still generate but videos show "not configured".

### HeyGen avatar setup

1. Copy `config/avatars.example.json` to `config/avatars.json` (or edit the existing file).
2. Upload portrait images in [HeyGen](https://app.heygen.com/) as **Photo Avatars** and paste each **look ID** into `avatars.json`.
3. Optionally fill `label`, `outfit`, and `pose` for your own reference; set `"enabled": false` to skip a look.
4. Sync API names (optional): `python scripts/sync_heygen_avatars.py`
5. Videos map to enabled avatars by list order (cycles if fewer than 5):
   - 1 → Problem→Promise
   - 2 → 3 Mistakes
   - 3 → Before→After
   - 4 → Myth vs Truth
   - 5 → Fast Tip→Sell

Videos use **Avatar V** by default; if a look is not eligible, the app retries once with **Avatar IV**.

---

## 📁 Project Structure

```
desktop-automation/
├── app.py                      # Streamlit UI
├── services/
│   ├── ai_generator.py         # OpenAI: scripts, motion, B-roll prompts
│   ├── heygen_client.py        # HeyGen v3 video API
│   ├── file_manager.py         # Output folders
│   ├── pdf_generator.py
│   └── zip_manager.py
├── prompts/
│   ├── script_prompts.py
│   ├── heygen_motion_prompts.py
│   └── broll_prompts.py        # Kling B-roll (manual)
├── outputs/                    # Generated content (gitignored)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 🎥 Video pipeline

1. User fills product form → OpenAI generates 5 scripts + motion + B-roll prompts.
2. **HeyGen** (per topic): cleaned script + `motion_prompt` + `avatar_id` + `voice_id` → MP4.
3. **Kling B-roll**: copy from B-Roll tab → paste into Kling manually (optional).
4. Download individual videos, ZIP, PDF from Downloads tab.

---

## 📝 License

Internal project for **DigitalProductsCreators.com**.
