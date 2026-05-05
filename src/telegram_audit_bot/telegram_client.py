from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List

from telethon import TelegramClient
from telethon.tl.custom.message import Message

from .config import Settings
from .types import ChatMessage, ChatTarget


class TelegramDataSource:
    def __init__(self, settings: Settings) -> None:
        self._client = TelegramClient(
            settings.telegram_session_name,
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )
        self._bot_token = settings.telegram_bot_token

    async def start(self) -> None:
        # Cloud runtimes are non-interactive; use bot auth to avoid phone/code prompts.
        await self._client.start(bot_token=self._bot_token)

    async def stop(self) -> None:
        await self._client.disconnect()

    async def fetch_messages_since(self, chat_targets: Iterable[ChatTarget], since_utc: datetime) -> List[ChatMessage]:
        if since_utc.tzinfo is None:
            since_utc = since_utc.replace(tzinfo=timezone.utc)

        results: List[ChatMessage] = []
        for target in chat_targets:
            chat_id = target.chat_id
            entity = await self._client.get_entity(chat_id)
            title = getattr(entity, "title", str(chat_id))

            async for msg in self._client.iter_messages(chat_id, reverse=True):
                if not isinstance(msg, Message):
                    continue
                if not msg.date or msg.date < since_utc:
                    continue
                if not msg.message:
                    continue
                if target.topic_ids and not _message_in_topics(msg, target.topic_ids):
                    continue

                sender = await msg.get_sender()
                sender_name = _sender_name(sender)
                results.append(
                    ChatMessage(
                        chat_id=chat_id,
                        chat_title=title,
                        sender_name=sender_name,
                        sent_at=msg.date,
                        text=msg.message,
                    )
                )

        results.sort(key=lambda item: item.sent_at)
        return results


class TelegramReporter:
    def __init__(self, settings: Settings) -> None:
        self._bot = TelegramClient(
            f"{settings.telegram_session_name}_reporter",
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )
        self._bot_token = settings.telegram_bot_token
        self._target_chat_id = settings.report_target_chat_id

    async def start(self) -> None:
        await self._bot.start(bot_token=self._bot_token)

    async def stop(self) -> None:
        await self._bot.disconnect()

    async def send_report(self, text: str) -> None:
        await self._bot.send_message(self._target_chat_id, text)


def _sender_name(sender: object) -> str:
    if sender is None:
        return "Unknown"

    first = getattr(sender, "first_name", "") or ""
    last = getattr(sender, "last_name", "") or ""
    username = getattr(sender, "username", "") or ""

    display = f"{first} {last}".strip()
    if display:
        return display
    if username:
        return f"@{username}"
    return "Unknown"


def _message_in_topics(msg: Message, topic_ids: List[int]) -> bool:
    if msg.id in topic_ids:
        return True

    reply_to = getattr(msg, "reply_to", None)
    if reply_to is None:
        return False

    reply_to_top_id = getattr(reply_to, "reply_to_top_id", None)
    if reply_to_top_id in topic_ids:
        return True

    # Fallback for cases where thread linkage comes as reply_to_msg_id.
    reply_to_msg_id = getattr(reply_to, "reply_to_msg_id", None)
    return reply_to_msg_id in topic_ids
