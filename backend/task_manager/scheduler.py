from datetime import datetime
from typing import Callable

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError

from backend.task_manager.task_card import TaskCard
from backend.task_manager.folder import Folder


class TaskScheduler:
    def __init__(self, bot: Bot, send_notification: Callable):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.send_notification = send_notification

    async def run(self) -> None:
        self.scheduler.start()

    async def schedule_folders(self, folders: dict[int, list[Folder]]) -> None:
        for user_id in folders:
            for folder in folders[user_id]:
                await self.schedule_folder(folder.active_tasks, user_id)

    async def schedule_folder(self, tasks: dict[int, TaskCard], chat_id: int) -> None:
        for task in tasks.values():
            await self.schedule_task(task, chat_id)

    async def schedule_task(self, task: TaskCard, chat_id: int) -> None:
        if task.due_date > datetime.now():
            trigger = DateTrigger(task.due_date)
            job = self.scheduler.add_job(self.send_notification, trigger=trigger, args=(chat_id, task, ))
            task.schedule_job_id = job.id

    async def remove_schedule_task(self, task: TaskCard) -> None:
        if task.schedule_job_id:
            try:
                self.scheduler.remove_job(str(task.schedule_job_id))
            except JobLookupError:
                pass
