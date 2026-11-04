# High Value Market Bot

An AI-powered Telegram assistant for **SEO, keyword research, content writing, marketing strategy, social media, backlink planning, and business growth**.

Built with `python-telegram-bot`, `FastAPI`, `aiosqlite`, and an OpenAI-compatible AI API. Deployable on **Railway** from **GitHub**.

---

## ✨ Features

- **SEO Tools** (15): title, meta, content analyzer, URL, headings, on-page checklist, audit, search intent, improvements, strategy, readability, keyword density, schema, outline, competitor comparison.
- **Keyword Research** (15): suggestions, long-tail, clustering, difficulty, intent, related, questions, brainstorm, local, commercial, informational, transactional, content mapping, strategy, report.
- **Website Analysis**: safe public-page audit with SSRF protection.
- **Competitor Analysis**: fetch up to 3 public URLs and generate a competitive report.
- **AI Content Writer** (20): blog posts, intros, conclusions, product descriptions, landing pages, ads, emails, YouTube, affiliate content, rewriting, tone, and more.
- **Marketing Tools** (15), **Social Media Tools** (10), **Backlink Tools** (8), **Business Tools** (6).
- **AI Assistant**: conversational chat with per-user memory.
- **Accounts, usage limits, admin panel, statistics, broadcast, premium control**.

> ⚠️ The bot uses AI to generate recommendations. It does **not** access Google Search Console, Google Analytics, or private website data. **Verified SEO metrics (volume, CPC, KD, backlinks, rankings) require a third-party data provider** (e.g., DataForSEO, Ahrefs, SEMrush). When data isn't available the bot clearly labels outputs as estimates.

---

## 🚀 Railway Deployment

1. Push this project to a **GitHub** repository.
2. In Railway, create a new project → **Deploy from GitHub repo**.
3. Add the following **environment variables**:

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token |
| `ADMIN_ID` | ✅ | Your Telegram user ID |
| `AI_API_KEY` | ✅ | API key for an OpenAI-compatible endpoint |
| `AI_BASE_URL` | ✅ | e.g. `https://api.openai.com/v1` |
| `AI_MODEL` | ✅ | e.g. `gpt-4o-mini` |
| `AI_TIMEOUT` | – | default 60 |
| `DATABASE_PATH` | – | default `data/bot.db` |
| `WEBHOOK_URL` | – | Auto-detected from `RAILWAY_PUBLIC_DOMAIN` |
| `WEBHOOK_PATH` | – | default `/webhook` |
| `PORT` | – | Railway injects this |
| `FREE_DAILY_LIMIT` | – | default 15 |
| `PREMIUM_DAILY_LIMIT` | – | default 300 |
| `FREE_AUDIT_LIMIT` | – | default 2 |
| `PREMIUM_AUDIT_LIMIT` | – | default 50 |

4. Deploy. Railway's Nixpacks builder installs dependencies and runs `python main.py`.
5. Uvicorn starts on Railway's `$PORT`. The bot sets the webhook automatically from `RAILWAY_PUBLIC_DOMAIN`.

**Important for webhook mode:** webhook and polling are mutually exclusive. If `WEBHOOK_URL` or `RAILWAY_PUBLIC_DOMAIN` is set, webhook mode is used. Otherwise the bot uses long-polling.

---

## 💻 Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your values

export $(grep -v '^#' .env | xargs)   # or use python-dotenv in a wrapper
python main.py
