from aiogram.filters.state import State, StatesGroup
from aiogram.filters import Command, CommandStart, StateFilter, Text, and_f, or_f
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize)

from asyncio import sleep

from backend.task_manager.tm_handler import TaskManagerHandler
from backend.task_manager.folder import Folder
from backend.task_manager.task_card import TaskCard


class TaskManagerCommands:
    def __init__(self, task_manager_handler: TaskManagerHandler):
        self.task_manager_handler = task_manager_handler

    def register(self, dispatcher: Dispatcher):
        dispatcher.message.register(
            self.proceed_exit_command,
            Command(commands=['exit']), ~StateFilter(default_state)
        )
        dispatcher.callback_query.register(
            self.proceed_exit_command,
            Text(text=["exit"]), ~StateFilter(default_state)
        )
        dispatcher.message.register(
            self.show_folders_command,
            Command(commands=["folders"]),
            StateFilter(default_state)
        )
        dispatcher.callback_query.register(
            self.add_folder,
            Text(text=['addfolder']), StateFilter(FSMTaskManager.select_folder_action)
        )
        dispatcher.callback_query.register(
            self.show_folder_command,
            StateFilter(FSMTaskManager.select_folder_action), Text(startswith=['folderid'])
        )
        dispatcher.message.register(
            self.show_task_command,
            Command(commands=['task']), StateFilter(FSMTaskManager.request_task)
        )

    async def proceed_exit_command(self, message: Message | CallbackQuery, state: FSMContext):
        left_message = await message.answer("You left dialog.")
        await sleep(1)
        await (await state.get_data())["message"].delete()
        if isinstance(message, Message):
            await left_message.delete()
        await state.clear()

    async def proceed_back_command(self, callback: CallbackQuery, state: FSMContext):
        pass

    async def show_folders_command(self, message: Message, state: FSMContext):
        folders = self.task_manager_handler.get_folders_by_user_id(message.from_user.id)[message.from_user.id]
        msg_text = self.get_text_show_folders(folders)
        keyboard = self.get_keyboard_show_folders(folders)
        await state.set_state(FSMTaskManager.select_folder_action)
        main_message = await message.answer(msg_text, reply_markup=keyboard)
        await state.update_data(message=main_message, prev_state=default_state)

    def get_text_show_folders(self, folders: list[Folder]) -> str:
        if folders:
            msg_text = 'Your folders:\n\n'

            for folder in folders:
                msg_text += f"Id: {folder.id}\n"
        else:
            msg_text = "You have no folders yet."

        return msg_text

    def get_keyboard_show_folders(self, folders: list[Folder]) -> InlineKeyboardMarkup:
        add_task_button = InlineKeyboardButton(text="Add folder", callback_data="addfolder")
        keyboard_markup = [[add_task_button], []]

        if folders:

            row_index = 1
            for folder in folders:
                button = InlineKeyboardButton(text=f"Id: {folder.id}.", callback_data=f"folderid_{folder.id}")
                keyboard_markup[row_index].append(button)
                row_index += 1
                keyboard_markup.append([])

            exit_button = InlineKeyboardButton(text="exit", callback_data="exit")
            keyboard_markup[row_index].append(exit_button)
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        else:
            exit_button = InlineKeyboardButton(text="exit", callback_data="exit")
            keyboard_markup[1].append(exit_button)
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

        return keyboard

    async def add_folder(self, callback: CallbackQuery, state: FSMContext):
        main_message: Message = (await state.get_data())["message"]
        self.task_manager_handler.add_folder(callback.from_user.id)
        await callback.answer(text="Folder was created")
        folders = self.task_manager_handler.get_folders_by_user_id(callback.from_user.id)[callback.from_user.id]
        msg_text = self.get_text_show_folders(folders)
        keyboard = self.get_keyboard_show_folder(folders)
        await main_message.edit_text(msg_text)
        await main_message.edit_reply_markup(reply_markup=keyboard)
        await state.set_state(FSMTaskManager.select_folder_action)

    async def show_folder_command(self, callback: CallbackQuery, state: FSMContext):
        folders = self.task_manager_handler.folders[str(callback.from_user.id)]
        tasks = {}
        selected_folder = None
        for folder in folders:
            if folder.id == int(callback.data.split('_')[1]):
                selected_folder = folder
                tasks = selected_folder.active_tasks
        await state.update_data(selected_folder=selected_folder)

        msg_text = self.get_text_show_folder(tasks, callback)
        keyboard = self.get_keyboard_show_folder(tasks)

        await state.set_state(FSMTaskManager.select_task_action)
        await callback.message.edit_text(msg_text, reply_markup=keyboard)

    def get_text_show_folder(self, tasks: dict[int:TaskCard], callback: CallbackQuery) -> str:
        msg_text = f"Folder: {callback.data.split('_')[1]}\n\n"
        if tasks:

            row_index = 1
            for task in tasks.values():
                msg_text += f"{row_index}: {task.get_attrs()}\n"
                row_index += 1

        else:
            msg_text += "You have no tasks."

        return msg_text

    def get_keyboard_show_folder(self, tasks: dict[int:TaskCard]) -> InlineKeyboardMarkup:
        add_task_button = InlineKeyboardButton(text="Add task", callback_data="addtask")
        edit_folder_button = InlineKeyboardButton(text= "Edit folder", callback_data="editfolder")
        delete_folder_button = InlineKeyboardButton(text= "Delete folder", callback_data="editfolder")
        keyboard_markup = [[add_task_button], [edit_folder_button, delete_folder_button], []]
        row_index = 2
        if tasks:

            for task in tasks.values():
                button = InlineKeyboardButton(text=f"Name: {task.name}", callback_data=f"taskname_{task.name}")
                keyboard_markup[row_index].append(button)
                row_index += 1
                keyboard_markup.append([])

        back_button = InlineKeyboardButton(text="back", callback_data="back")
        exit_button = InlineKeyboardButton(text="exit", callback_data="exit")
        keyboard_markup[row_index].append(back_button)
        keyboard_markup[row_index].append(exit_button)
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        return keyboard


    async def show_task_command(self, message: Message, state: FSMContext):
        await message.answer("show task")
        await state.clear()


class FSMTaskManager(StatesGroup):
    request_folders = State()
    select_folder_action = State()
    select_task_action = State()
    request_tasks = State()
    request_task = State()
