from __future__ import annotations

import json
from typing import List

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .types import ChatTarget


class ChatScopeConfig(BaseModel):
    chat_id: int
    topic_ids: List[int] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    project_name: str
    chat_ids: List[int] = Field(default_factory=list)
    chat_scopes: List[ChatScopeConfig] = Field(default_factory=list)

    @property
    def chat_targets(self) -> List[ChatTarget]:
        targets: List[ChatTarget] = []
        if self.chat_scopes:
            for scope in self.chat_scopes:
                targets.append(ChatTarget(chat_id=scope.chat_id, topic_ids=scope.topic_ids))
            return targets

        for chat_id in self.chat_ids:
            targets.append(ChatTarget(chat_id=chat_id, topic_ids=[]))
        return targets

    @model_validator(mode="after")
    def validate_any_chat_source(self) -> "ProjectConfig":
        if not self.chat_ids and not self.chat_scopes:
            raise ValueError("Project requires chat_ids or chat_scopes")
        return self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_api_id: int
    telegram_api_hash: str
    telegram_session_name: str = "audit_session"

    telegram_bot_token: str
    report_target_chat_id: int

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"

    schedule_time: str = "23:00"
    timezone: str = "Europe/Kyiv"
    lookback_hours: int = 24

    projects_json: str = "[]"
    pm_identifiers_json: str = "[]"

    @field_validator("schedule_time")
    @classmethod
    def validate_schedule_time(cls, value: str) -> str:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("SCHEDULE_TIME must be HH:MM")

        hour, minute = parts
        if not (hour.isdigit() and minute.isdigit()):
            raise ValueError("SCHEDULE_TIME must be numeric HH:MM")

        hh = int(hour)
        mm = int(minute)
        if hh < 0 or hh > 23 or mm < 0 or mm > 59:
            raise ValueError("SCHEDULE_TIME out of range")

        return value

    @property
    def projects(self) -> List[ProjectConfig]:
        raw = json.loads(self.projects_json)
        if not isinstance(raw, list):
            raise ValueError("PROJECTS_JSON must be a JSON array")
        return [ProjectConfig.model_validate(item) for item in raw]

    @property
    def pm_identifiers(self) -> List[str]:
        raw = json.loads(self.pm_identifiers_json)
        if not isinstance(raw, list):
            raise ValueError("PM_IDENTIFIERS_JSON must be a JSON array")

        normalized: List[str] = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                normalized.append(item.strip())
        return normalized


def get_settings() -> Settings:
    return Settings()
