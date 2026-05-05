from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from openai import OpenAI

from .config import Settings
from .types import ChatMessage

SYSTEM_PROMPT = """
You are a senior communication auditor for a digital agency.
Analyze dialogs between client, project manager, buyer, and internal team.
Focus on communication quality and practical improvements.

Rules:
- Be concrete and cite short message examples.
- Separate strengths and risks.
- Give actionable recommendations for tomorrow.
- Keep output compact and useful for managers.
""".strip()


class DailyAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def build_report(
        self,
        project_name: str,
        started_at: datetime,
        finished_at: datetime,
        messages: Iterable[ChatMessage],
    ) -> str:
        rows: List[str] = []
        for msg in messages:
            ts = msg.sent_at.strftime("%Y-%m-%d %H:%M")
            rows.append(f"[{ts}] [{msg.chat_title}] {msg.sender_name}: {msg.text}")

        if not rows:
            return (
                f"# Daily communication report: {project_name}\n\n"
                "No messages found in the selected period."
            )

        user_prompt = (
            f"Project: {project_name}\n"
            f"Period: {started_at.isoformat()} -> {finished_at.isoformat()}\n\n"
            "Create report in this structure:\n"
            "1) Overall communication score 1-10\n"
            "2) What went well (3 bullets)\n"
            "3) What went wrong (3 bullets)\n"
            "4) Risks if not fixed (up to 3 bullets)\n"
            "5) Action plan for tomorrow (3 specific actions)\n"
            "6) Rephrase examples (bad -> better) up to 3 pairs\n\n"
            "Messages:\n"
            + "\n".join(rows)
        )

        response = self._client.responses.create(
            model=self._model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.output_text.strip()
