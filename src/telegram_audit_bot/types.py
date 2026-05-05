from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ChatMessage:
    chat_id: int
    chat_title: str
    sender_name: str
    sent_at: datetime
    text: str


@dataclass(slots=True)
class ChatTarget:
    chat_id: int
    topic_ids: list[int]
