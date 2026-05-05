from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .analyzer import DailyAnalyzer
from .config import Settings, get_settings
from .telegram_client import TelegramDataSource, TelegramReporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("telegram_audit_bot")


class AuditApp:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.data_source = TelegramDataSource(settings)
        self.reporter = TelegramReporter(settings)
        self.analyzer = DailyAnalyzer(settings)

        hour, minute = map(int, settings.schedule_time.split(":"))
        self.scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.timezone))
        self.scheduler.add_job(
            self.run_daily_report,
            "cron",
            hour=hour,
            minute=minute,
            id="daily_communication_report",
            replace_existing=True,
        )

    async def start(self) -> None:
        await self.data_source.start()
        await self.reporter.start()
        self.scheduler.start()
        logger.info("Scheduler started, next run at %s", self.settings.schedule_time)

    async def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)
        await self.data_source.stop()
        await self.reporter.stop()

    async def run_daily_report(self) -> None:
        logger.info("Starting daily communication report job")
        now_utc = datetime.now(timezone.utc)
        since_utc = now_utc - timedelta(hours=self.settings.lookback_hours)

        for project in self.settings.projects:
            try:
                messages = await self.data_source.fetch_messages_since(project.chat_targets, since_utc)
                report_text = self.analyzer.build_report(
                    project_name=project.project_name,
                    started_at=since_utc,
                    finished_at=now_utc,
                    messages=messages,
                )
                outbound = (
                    f"Daily communication audit\n"
                    f"Project: {project.project_name}\n"
                    f"Period: last {self.settings.lookback_hours}h\n\n"
                    f"{report_text}"
                )
                await self.reporter.send_report(outbound)
                logger.info("Report sent for project %s", project.project_name)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed report for project %s: %s", project.project_name, exc)

    async def run_forever(self) -> None:
        await self.start()
        stop_event = asyncio.Event()
        await stop_event.wait()


async def run_once(settings: Settings) -> None:
    app = AuditApp(settings)
    await app.data_source.start()
    await app.reporter.start()
    try:
        await app.run_daily_report()
    finally:
        await app.data_source.stop()
        await app.reporter.stop()


def main() -> None:
    settings = get_settings()
    asyncio.run(AuditApp(settings).run_forever())


def main_once() -> None:
    settings = get_settings()
    asyncio.run(run_once(settings))
