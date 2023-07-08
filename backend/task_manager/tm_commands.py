from aiogram.filters.state import State, StatesGroup
from aiogram.filters import Command, CommandStart, StateFilter, Text, and_f, or_f
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize)

from backend.task_manager.tm_handler import TaskManagerHandler


class TaskManagerCommands:
    def __init__(self, task_manager_handler: TaskManagerHandler):
        self.task_manager_handler = task_manager_handler

    def register(self, dispatcher: Dispatcher):
        dispatcher.message.register(self.proceed_cancel_command, Command(commands=['cancel']), ~StateFilter(default_state))
        dispatcher.callback_query.register(self.proceed_cancel_command, Text(text=["cancel"]), ~StateFilter(default_state))
        dispatcher.message.register(self.show_folders_command, Command(commands=["folders"]), StateFilter(default_state))
        dispatcher.callback_query.register(self.show_folder_command, StateFilter(FSMTaskManager.select_folder), Text(startswith=['folderid']))
        dispatcher.message.register(self.show_task_command, Command(commands=['task']), StateFilter(FSMTaskManager.request_task))

    async def proceed_cancel_command(self, message: Message, state: FSMContext):
        await message.answer("You left dialog.")
        await state.clear()

    async def show_folders_command(self, message: Message, state: FSMContext):
        await state.update_data(message_id=message.message_id)
        folders = self.task_manager_handler.get_folders_by_user_id(message.from_user.id)[message.from_user.id]
        keyboard_markup = [[]]
        if folders:
            msg_text = 'Your folders:\n\n'

            row_index = 0
            for folder in folders:
                msg_text += f"Id: {folder.id}\n"
                button = InlineKeyboardButton(text=f"Id: {folder.id}", callback_data=f"folderid_{folder.id}")
                keyboard_markup[row_index].append(button)
                row_index += 1
                keyboard_markup.append([])

            button = InlineKeyboardButton(text="cancel", callback_data="cancel")
            keyboard_markup[row_index].append(button)
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
            await state.set_state(FSMTaskManager.select_folder)
            await message.answer(msg_text, reply_markup=keyboard)
        else:
            await state.set_state(FSMTaskManager.request_tasks)
            await message.answer("You have no folders yet.")

    async def show_folder_command(self, callback: CallbackQuery, state: FSMContext):
        msg_text = f"Folder: {callback.data.split('_')[1]}"
        await state.update_data(folder_id=int(callback.data.split('_')[1]))
        folders = self.task_manager_handler.folders[str(callback.from_user.id)]
        for folder in folders:
            if folder.id == int(callback.data.split('_')[1]):
                selected_folder = folder
                tasks = selected_folder.active_tasks
        keyboard_markup = [[]]
        if tasks:
            msg_text = f'Your tasks in folder {(await state.get_data())["folder_id"]}:\n\n'

            row_index = 0
            for task in tasks:
                msg_text += f"{row_index}: {task.get_attrs()}\n"
                button = InlineKeyboardButton(text=f"Name: {task.name}", callback_data=f"taskname_{task.name}")
                keyboard_markup[row_index].append(button)
                row_index += 1
                keyboard_markup.append([])

            button = InlineKeyboardButton(text="cancel", callback_data="cancel")
            keyboard_markup[row_index].append(button)
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
            await state.set_state(FSMTaskManager.select_task)
            await callback.message.edit_text(msg_text, reply_markup=keyboard)
        else:
            await state.set_state(FSMTaskManager.request_task)
            await callback.message.answer("You have no tasks in folder yet.")

    async def show_task_command(self, message: Message, state: FSMContext):
        await message.answer("show task")
        await state.clear()


class FSMTaskManager(StatesGroup):
    request_folders = State()
    select_folder = State()
    select_task = State()
    request_tasks = State()
    request_task = State()
