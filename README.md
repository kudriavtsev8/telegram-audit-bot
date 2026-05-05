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
- `PM_IDENTIFIERS_JSON` to explicitly mark PM user(s) for scoring

Example `PROJECTS_JSON`:

```json
[
  {
    "project_name": "Client A",
    "chat_ids": [-1001111111111, -1002222222222]
  }
]
```

Topic-based example (shared command chat with separate project topics):

```json
[
  {
    "project_name": "KUZOV HUB",
    "chat_scopes": [
      { "chat_id": -1002960691411, "topic_ids": [2661] }
    ]
  },
  {
    "project_name": "GOOD Service",
    "chat_scopes": [
      { "chat_id": -1002960691411, "topic_ids": [2703] }
    ]
  }
]
```

## 2) Run modes

### Continuous mode (daily scheduler)

```bash
python -m telegram_audit_bot
```

### One-time mode (test now)

```bash
python run_once.py
```

## 3) Deploy

Use any VM/VPS and run the continuous mode under `systemd`/`supervisor`/Docker.

## 4) GitHub

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
- For best PM scoring quality, fill `PM_IDENTIFIERS_JSON` (username/full name).
