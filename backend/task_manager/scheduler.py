from aiogram import Bot
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from backend.task_manager.task_card import TaskCard
from backend._utils import send_notification


class TaskScheduler:
    def __init__(self, bot: Bot):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot

    async def sayhi(self):
        print("hello")

    async def run(self):
        self.scheduler.add_job(self.sayhi, trigger=IntervalTrigger(seconds=5))
        self.scheduler.start()


    async def add_task(self, task: TaskCard, chat_id: int):
        due_date = datetime(year=task.due_date.year, month=task.due_date.month, day=task.due_date.day, hour=13, minute=55)
        trigger = DateTrigger(due_date)
        self.scheduler.add_job(send_notification, trigger=trigger, args=(self.bot, chat_id, task, ))
        

