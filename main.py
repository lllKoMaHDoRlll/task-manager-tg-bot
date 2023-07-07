from aiogram import Dispatcher, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.session.aiohttp import AiohttpSession

from pathlib import Path

from backend.task_manager.tm_handler import TaskManagerHandler
from backend._utils import get_config

TASKS_DATA_PATH = Path(r"C:\Users\aleks\PycharmProjects\TG-TaskManager\data\tasks")
CONFIG_PATH = Path(r"C:\Users\aleks\PycharmProjects\TG-TaskManager\data\config.json")

TM_HANDLER = TaskManagerHandler(TASKS_DATA_PATH)

DP = Dispatcher()

CONFIG = get_config(CONFIG_PATH)


@DP.message(Command(commands=['start']))
async def start_command(message: Message) -> None:
    await message.answer("Hello! This is your Task Manager Bot.\nYou can list your task with /tasks")


@DP.message(Command(commands=['ping']))
async def ping_command(message: Message) -> None:
    await message.answer("pong")


if __name__ == '__main__':

    bot = Bot(token=CONFIG.token)

    DP.run_polling(bot)
