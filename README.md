# Telegram Communication Audit Bot

MVP for an agency workflow:
- reads messages from selected Telegram chats,
- analyzes communication quality with LLM,
- sends one daily report at configured time (default `23:00`).

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Fill `.env`:
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` from my.telegram.org
- `TELEGRAM_BOT_TOKEN` from BotFather
- `REPORT_TARGET_CHAT_ID` where daily report is sent
- `OPENAI_API_KEY`
- `PROJECTS_JSON` with chats to analyze

Example `PROJECTS_JSON`:

```json
[
  {
    "project_name": "Client A",
    "chat_ids": [-1001111111111, -1002222222222]
  }
]
```

## 2) First login for Telethon

First run will ask for your Telegram phone and login code to create session file.

```bash
python -m telegram_audit_bot
```

## 3) Run modes

### Continuous mode (daily scheduler)

```bash
python -m telegram_audit_bot
```

### One-time mode (test now)

```bash
python run_once.py
```

## 4) Deploy

Use any VM/VPS and run the continuous mode under `systemd`/`supervisor`/Docker.

## 5) GitHub

Initialize git and push:

```bash
git init
git add .
git commit -m "Initial MVP: telegram communication audit bot"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## Notes

- Ensure participants are informed that communication is being analyzed.
- Keep data access restricted to agency managers.
- Tune prompt/rules in `src/telegram_audit_bot/analyzer.py` for your standards.
