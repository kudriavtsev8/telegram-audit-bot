from __future__ import annotations

import json
from typing import List

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectConfig(BaseModel):
    project_name: str
    chat_ids: List[int] = Field(min_length=1)


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
