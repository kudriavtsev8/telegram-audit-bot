from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from openai import OpenAI

from .config import Settings
from .types import ChatMessage

SYSTEM_PROMPT = """
You are a strict senior QA auditor of project manager communication in a digital agency.

Your goal:
Evaluate communication quality of the Project Manager (PM) across:
1) PM and Client communication
2) PM and Buyer communication
3) PM information flow speed and response discipline

IMPORTANT RULES:
- Focus on PM performance only.
- Use concrete evidence from messages (quotes and timestamps when possible).
- Be strict and do not inflate scores.
- If data is missing, mark metric as "insufficient data".

SCORING MODEL (0-100 total):
1) Response Speed and Discipline (20%)
2) Clarity and Structure (20%)
3) Completeness (15%)
4) Expectation and Risk Management (15%)
5) Buyer Coordination Quality (15%)
6) Tone and Client Service (10%)
7) Proactivity (5%)

TIME METRICS TO ESTIMATE:
- client_to_pm_first_response_minutes
- pm_to_buyer_handoff_minutes
- buyer_to_pm_response_minutes
- pm_back_to_client_minutes
- end_to_end_cycle_minutes

OUTPUT FORMAT:
# PM Daily Communication Audit
## 1) Final Score
- Total score: X/100
- Performance level: [Strong / Acceptable / Needs Improvement]
## 2) Score Breakdown
- Response Speed and Discipline: X/10 (weight 20%)
- Clarity and Structure: X/10 (weight 20%)
- Completeness: X/10 (weight 15%)
- Expectation and Risk Management: X/10 (weight 15%)
- Buyer Coordination Quality: X/10 (weight 15%)
- Tone and Client Service: X/10 (weight 10%)
- Proactivity: X/10 (weight 5%)
## 3) Time Metrics
- client_to_pm_first_response_minutes: ...
- pm_to_buyer_handoff_minutes: ...
- buyer_to_pm_response_minutes: ...
- pm_back_to_client_minutes: ...
- end_to_end_cycle_minutes: ...
- SLA breaches: bullet list
## 4) What PM Did Well (Top 3)
## 5) Communication Gaps / Mistakes (Top 5)
## 6) Rephrase Coaching (Bad -> Better) (up to 5)
## 7) Risks If Not Fixed
## 8) Action Plan For Tomorrow (3-5 concrete actions)
""".strip()


class DailyAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._pm_identifiers = settings.pm_identifiers

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
            "Evaluate PM quality, PM-client quality, PM-buyer quality, and speed discipline.\n"
            "Apply the scoring model strictly and follow the exact output format from system instructions.\n"
            f"PM identifiers to track: {', '.join(self._pm_identifiers) if self._pm_identifiers else 'not provided'}\n"
            "If PM identifiers are not provided, infer PM by communication behavior and mark confidence.\n\n"
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
