from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from backend._utils import send_notification
from backend.task_manager.task_card import TaskCard
from backend.task_manager.folder import Folder


class TaskScheduler:
    def __init__(self, bot: Bot):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot

    async def run(self):
        self.scheduler.start()

    async def schedule_folders(self, folders: dict[int:Folder]) -> None:
        for user_id in folders:
            for folder in folders[user_id]:
                await self.schedule_folder(folder.active_tasks, user_id)

    async def schedule_folder(self, tasks: dict[int:TaskCard], chat_id: int) -> None:
        for task in tasks.values():
            await self.schedule_task(task, chat_id)

    async def schedule_task(self, task: TaskCard, chat_id: int) -> None:
        if task.due_date < datetime.now():
            return None
        trigger = DateTrigger(task.due_date)
        job = self.scheduler.add_job(send_notification, trigger=trigger, args=(self.bot, chat_id, task, ))
        task.schedule_job_id = job.id

    async def remove_schedule_task(self, task: TaskCard) -> None:
        if task.schedule_job_id:
            self.scheduler.remove_job(str(task.schedule_job_id))
