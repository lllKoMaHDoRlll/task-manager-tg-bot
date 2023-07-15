from pathlib import Path

from aiogram import Dispatcher, Bot
from aiogram.filters import Command, Text
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from backend._utils import get_config
from backend.task_manager.scheduler import TaskScheduler
from backend.task_manager.tm_dialogs.main_menu import TaskManagerMainMenu
from backend.task_manager.tm_handler import TaskManagerHandler
from backend.task_manager.task_card import TaskCard
from backend.task_manager.folder import Folder
from backend.task_manager.labels import (
    TASK_FRAME, COMPLETE_TASK_BUTTON, DELETE_TASK_BUTTON, TASK_SNOOZE_BUTTON, TASK_COMPLETE_NOTIFICATION,
    NOT_IMPLEMENTED_ALERT, TASK_DELETE_NOTIFICATION
)


class MyBot:
    def __init__(self):
        self.tasks_data_path = Path(r"C:\Users\aleks\PycharmProjects\TG-TaskManager\data\tasks")
        self.config_path = Path(r"C:\Users\aleks\PycharmProjects\TG-TaskManager\data\config.json")

        self.config_data = get_config(self.config_path)
        self.bot = Bot(token=self.config_data.token)
        self.task_scheduler = TaskScheduler(self.bot, self.send_notification)

        self.task_manager_handler = TaskManagerHandler(self.tasks_data_path, self.task_scheduler)
        self.task_manager_handler.load()
        self.task_manager_commands = TaskManagerMainMenu(self.task_manager_handler)
        self.storage = MemoryStorage()

        self.dispatcher = Dispatcher(storage=self.storage)

    def run(self, on_startup=None):
        self.dispatcher.run_polling(self.bot, on_startup=on_startup)

    def register_commands(self):
        self.dispatcher.message.register(start_command, Command(commands=['start']))
        self.dispatcher.message.register(ping_command, Command(commands=['ping']))
        self.dispatcher.callback_query.register(self.proceed_ncomplete_task, Text(startswith="ncomplete"))
        self.dispatcher.callback_query.register(self.proceed_nsnooze_task, Text(startswith="nsnooze"))
        self.dispatcher.callback_query.register(self.proceed_ndelete_task, Text(startswith="ndelete"))
        self.task_manager_commands.register(self.dispatcher)

    async def on_startup(self):
        await self.task_scheduler.schedule_folders(self.task_manager_handler.folders)
        await self.task_scheduler.run()

    async def send_notification(self, chat_id: int, task: TaskCard):
        msg_text = TASK_FRAME.format(
            name=task.name,
            priority=task.priority,
            description=task.description,
            due_date=task.due_date,
            repeat=task.repeat
        )
        markup = [
            [
                InlineKeyboardButton(
                    text=COMPLETE_TASK_BUTTON,
                    callback_data="ncompletetask_{0}_{1}".format(task.parent.id, task.id)
                )
            ],
            [
                InlineKeyboardButton(
                    text=TASK_SNOOZE_BUTTON,
                    callback_data="nsnoozetask_{0}_{1}".format(task.parent.id, task.id)
                ),
                InlineKeyboardButton(
                    text=DELETE_TASK_BUTTON,
                    callback_data="ndeletetask_{0}_{1}".format(task.parent.id, task.id)
                )
            ]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=markup)
        await self.bot.send_message(chat_id=chat_id, text=msg_text, reply_markup=keyboard)

    async def proceed_ncomplete_task(self, callback: CallbackQuery):
        action, folder_id, task_id = callback.data.split("_")
        user_id = callback.from_user.id
        folder: Folder = self.task_manager_handler.get_folder_by_folder_id(int(user_id), int(folder_id))
        task: TaskCard = folder.get_task_by_id(int(task_id))
        await self.task_manager_handler.complete_task(task)
        await callback.answer(text=TASK_COMPLETE_NOTIFICATION)
        await callback.message.delete()

    async def proceed_nsnooze_task(self, callback: CallbackQuery):
        await callback.answer(text=NOT_IMPLEMENTED_ALERT)

    async def proceed_ndelete_task(self, callback: CallbackQuery):
        action, folder_id, task_id = callback.data.split("_")
        user_id = callback.from_user.id
        folder: Folder = self.task_manager_handler.get_folder_by_folder_id(int(user_id), int(folder_id))
        task: TaskCard = folder.get_task_by_id(int(task_id))
        task.delete()
        await callback.answer(text=TASK_DELETE_NOTIFICATION)
        await callback.message.delete()


async def start_command(message: Message) -> None:
    await message.answer("Hello! This is your Task Manager Bot.\nYou can list your task with /tasks")


async def ping_command(message: Message) -> None:
    await message.answer("pong")


if __name__ == '__main__':
    bot = MyBot()
    bot.register_commands()
    bot.run(on_startup=bot.on_startup)
