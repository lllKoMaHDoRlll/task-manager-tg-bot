from pathlib import Path

from aiogram import Dispatcher, Bot
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from backend._utils import get_config
from backend.task_manager.scheduler import TaskScheduler
from backend.task_manager.tm_commands import TaskManagerCommands
from backend.task_manager.tm_handler import TaskManagerHandler


class MyBot:
    def __init__(self):
        self.tasks_data_path = Path(r"C:\Users\aleks\PycharmProjects\TG-TaskManager\data\tasks")
        self.config_path = Path(r"C:\Users\aleks\PycharmProjects\TG-TaskManager\data\config.json")

        self.config_data = get_config(self.config_path)
        self.bot = Bot(token=self.config_data.token)
        self.task_scheduler = TaskScheduler(self.bot)

        self.task_manager_handler = TaskManagerHandler(self.tasks_data_path, self.task_scheduler)
        self.task_manager_handler.load()
        self.task_manager_commands = TaskManagerCommands(self.task_manager_handler)
        self.storage = MemoryStorage()

        self.dispatcher = Dispatcher(storage=self.storage)

    def run(self, on_startup=None):
        self.dispatcher.run_polling(self.bot, on_startup=on_startup)

    def register_commands(self):
        self.dispatcher.message.register(start_command, Command(commands=['start']))
        self.dispatcher.message.register(ping_command, Command(commands=['ping']))
        self.task_manager_commands.register(self.dispatcher)

    async def on_startup(self):
        await self.task_manager_handler.schedule_folders()
        await self.task_scheduler.run()


async def start_command(message: Message) -> None:
    await message.answer("Hello! This is your Task Manager Bot.\nYou can list your task with /tasks")


async def ping_command(message: Message) -> None:
    await message.answer("pong")


if __name__ == '__main__':
    bot = MyBot()
    bot.register_commands()
    bot.run(on_startup=bot.on_startup)
