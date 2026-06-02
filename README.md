# 🎬 Content Creator Automation

A Streamlit app that generates **5 short-form marketing video scripts**, **cinematic B-roll prompts**, a **talking head guide**, and an **image style guide** for any digital product — powered by OpenAI.

> **Live App:** [http://116.202.210.102:20157](http://116.202.210.102:20157)

---

## ✨ Features

- 5 ready-to-shoot video scripts (Problem→Promise, 3 Mistakes, Before→After, Myth vs Truth, Fast Tip→Sell)
- Cinematic B-roll prompts for every script
- Talking head delivery guide
- Image / thumbnail style guide
- Organized output folders per product
- PDF and ZIP export

---

## 🧰 Tech Stack

- **Frontend / UI:** Streamlit
- **AI:** OpenAI (`gpt-4o-mini` by default)
- **PDF:** ReportLab
- **Runtime:** Python 3.12
- **Deploy:** Docker + Docker Compose

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
# edit .env and add your OPENAI_API_KEY
```

### 3. Build and run

```bash
docker compose up -d --build
```

App will be available at **http://localhost:20157**.

### 4. Stop

```bash
docker compose down
```

---

## 🐳 Docker Image

The image is built from the included `Dockerfile`:

| Property        | Value                              |
|-----------------|------------------------------------|
| Base image      | `python:3.12-slim`                 |
| Image name      | `content-creator-automation:latest`|
| Container name  | `content-creator`                  |
| Exposed port    | `20157`                            |
| Restart policy  | `unless-stopped`                   |
| Volume          | `./outputs → /app/outputs`         |

Common commands:

```bash
docker compose build              # rebuild image after code changes
docker compose up -d              # start in background
docker compose logs -f            # tail logs
docker compose restart            # restart container
docker compose down               # stop and remove container
docker images content-creator-automation   # inspect image
```

---

## 💻 Run Locally (without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # add your OPENAI_API_KEY

streamlit run app.py --server.port=20157
```

---

## 🔑 Environment Variables

| Variable         | Required | Default        | Description                       |
|------------------|----------|----------------|-----------------------------------|
| `OPENAI_API_KEY` | ✅ Yes   | —              | Your OpenAI API key               |
| `OPENAI_MODEL`   | ❌ No    | `gpt-4o-mini`  | Use `gpt-4o` for higher quality   |

---

## 📁 Project Structure

```
desktop-automation/
├── app.py                  # Streamlit entry point
├── services/               # AI, file, PDF, ZIP logic
├── prompts/                # Script & B-roll prompt templates
├── outputs/                # Generated content (gitignored)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 📝 License

Internal project for **DigitalProductsCreators.com**.
