from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from backend._utils import send_notification
from backend.task_manager.task_card import TaskCard


class TaskScheduler:
    def __init__(self, bot: Bot):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot

    async def run(self):
        self.scheduler.start()

    async def add_task(self, task: TaskCard, chat_id: int):
        due_date = datetime(
            year=task.due_date.year,
            month=task.due_date.month, 
            day=task.due_date.day,
            hour=task.due_date.hour,
            minute=task.due_date.minute
        )
        trigger = DateTrigger(due_date)
        self.scheduler.add_job(send_notification, trigger=trigger, args=(self.bot, chat_id, task, ))
