from asyncio import sleep

from aiogram import Dispatcher
from aiogram.filters import Command, StateFilter, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiogram3_calendar.simple_calendar import SimpleCalendar, SimpleCalendarCallback

from backend.task_manager.folder import Folder
from backend.task_manager.task_card import TaskCard
from backend.task_manager.tm_handler import TaskManagerHandler
from backend.task_manager import labels


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
            Text(text=['addfolder']), StateFilter(FSMTaskManager.select_folders_action)
        )
        dispatcher.callback_query.register(
            self.delete_folder_command,
            Text(text=['deletefolder']), StateFilter(FSMTaskManager.select_folder_action)
        )
        dispatcher.callback_query.register(
            self.back_command,
            Text(text=['back']), StateFilter(FSMTaskManager.select_folder_action)
        )
        dispatcher.callback_query.register(
            self.show_folder_command,
            StateFilter(FSMTaskManager.select_folders_action), Text(startswith=['folderid'])
        )
        dispatcher.callback_query.register(
            self.edit_folder_command,
            StateFilter(FSMTaskManager.select_folder_action), Text(startswith=['editfolder'])
        )
        dispatcher.callback_query.register(
            self.add_task_request_name_command,
            StateFilter(FSMTaskManager.select_folder_action), Text(startswith=['addtask'])
        )
        dispatcher.message.register(
            self.add_task_request_description_command,
            StateFilter(FSMTaskManager.new_task_request_name)
        )
        dispatcher.message.register(
            self.add_task_request_due_date_command,
            StateFilter(FSMTaskManager.new_task_request_description)
        )
        dispatcher.callback_query.register(
            self.add_task_request_repeat_command,
            StateFilter(FSMTaskManager.new_task_request_due_date), SimpleCalendarCallback.filter()
        )
        dispatcher.message.register(
            self.add_task_request_priority_command,
            StateFilter(FSMTaskManager.new_task_request_repeat)
        )
        dispatcher.callback_query.register(
            self.add_task_confirm,
            StateFilter(FSMTaskManager.new_task_request_priority), Text(startswith="priority")
        )
        dispatcher.callback_query.register(
            self.proceed_add_task,
            StateFilter(FSMTaskManager.new_task_request_confirm), Text(startswith="confirm")
        )
        # dispatcher.message.register(
        #     self.show_task_command,
        #     Command(commands=['task']), StateFilter(FSMTaskManager.request_task)
        # )

    @staticmethod
    async def proceed_exit_command(message: Message | CallbackQuery, state: FSMContext):
        left_message = await message.answer(labels.EXIT_DIALOG)
        await sleep(1)
        await (await state.get_data())["message"].delete()
        if isinstance(message, Message):
            await left_message.delete()
        await state.clear()

    async def show_folders_command(self, message: Message, state: FSMContext):
        folders = self.task_manager_handler.get_folders_by_user_id(message.from_user.id)[message.from_user.id]
        msg_text = self.get_text_show_folders(folders)
        keyboard = self.get_keyboard_show_folders(folders)
        await state.set_state(FSMTaskManager.select_folders_action)
        main_message = await message.answer(msg_text, reply_markup=keyboard)
        await state.update_data(message=main_message, prev_state=default_state)

    async def update_show_folders_command(self, callback: CallbackQuery, state: FSMContext):
        main_message: Message = (await state.get_data())["message"]
        await state.update_data(selected_folder=None)
        folders = self.task_manager_handler.get_folders_by_user_id(callback.from_user.id)[callback.from_user.id]
        msg_text = self.get_text_show_folders(folders)
        keyboard = self.get_keyboard_show_folders(folders)
        await main_message.edit_text(msg_text)
        await main_message.edit_reply_markup(reply_markup=keyboard)
        await state.set_state(FSMTaskManager.select_folders_action)

    @staticmethod
    def get_text_show_folders(folders: list[Folder]) -> str:
        if folders:
            msg_text = labels.SHOW_FOLDERS_TITLE

            for folder in folders:
                tasks_amount = folder.active_tasks.__len__()
                msg_text += labels.SHOW_FOLDERS_FOLDER_FRAME.format(folder_id=folder.id, tasks_amount=tasks_amount)
        else:
            msg_text = labels.SHOW_FOLDERS_NO_FOLDERS

        return msg_text

    @staticmethod
    def get_keyboard_show_folders(folders: list[Folder]) -> InlineKeyboardMarkup:
        add_task_button = InlineKeyboardButton(text=labels.SHOW_FOLDERS_ADD_FOLDER_BUTTON, callback_data="addfolder")
        keyboard_markup = [[add_task_button], []]

        if folders:

            row_index = 1
            for folder in folders:
                button = InlineKeyboardButton(
                    text=labels.SHOW_FOLDERS_SELECT_FOLDER_BUTTON.format(folder_id=folder.id),
                    callback_data=f"folderid_{folder.id}"
                )
                keyboard_markup[row_index].append(button)
                row_index += 1
                keyboard_markup.append([])

            exit_button = InlineKeyboardButton(text=labels.EXIT_BUTTON, callback_data="exit")
            keyboard_markup[row_index].append(exit_button)
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        else:
            exit_button = InlineKeyboardButton(text=labels.EXIT_BUTTON, callback_data="exit")
            keyboard_markup[1].append(exit_button)
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

        return keyboard

    async def add_folder(self, callback: CallbackQuery, state: FSMContext):
        self.task_manager_handler.add_folder(callback.from_user.id)
        await callback.answer(text=labels.CREATE_FOLDER_ALERT)
        await self.update_show_folders_command(callback, state)

    async def show_folder_command(self, callback: CallbackQuery, state: FSMContext):
        folders = self.task_manager_handler.folders[str(callback.from_user.id)]
        tasks = {}
        selected_folder = None
        for folder in folders:
            if folder.id == int(callback.data.split('_')[1]):
                selected_folder = folder
                tasks = selected_folder.active_tasks
        await state.update_data(selected_folder=selected_folder)

        msg_text = self.get_text_show_folder(tasks, selected_folder.id)
        keyboard = self.get_keyboard_show_folder(tasks)

        await state.set_state(FSMTaskManager.select_folder_action)
        await callback.message.edit_text(msg_text, reply_markup=keyboard)

    async def update_show_folder_command(self, callback: CallbackQuery, state: FSMContext):
        selected_folder = (await state.get_data())["selected_folder"]
        tasks = selected_folder.active_tasks
        msg_text = self.get_text_show_folder(tasks, selected_folder.id)
        keyboard = self.get_keyboard_show_folder(tasks)
        await state.set_state(FSMTaskManager.select_folder_action)
        main_message = await callback.message.answer(msg_text, reply_markup=keyboard)
        await state.set_state(FSMTaskManager.select_folder_action)
        await state.update_data(message=main_message)

    @staticmethod
    def get_text_show_folder(tasks: dict[int:TaskCard], folder_id: int) -> str:
        msg_text = labels.SHOW_FOLDER_TITLE.format(folder_id=folder_id)
        if tasks:

            row_index = 1
            for task in tasks.values():
                msg_text += labels.SHOW_FOLDER_TASK_FRAME.format(
                    name=task.name,
                    priority=task.priority,
                    due_date=task.due_date,
                    repeat=task.repeat,
                    description=task.description
                )
                row_index += 1

        else:
            msg_text += labels.SHOW_FOLDER_NO_TASKS

        return msg_text

    @staticmethod
    def get_keyboard_show_folder(tasks: dict[int:TaskCard]) -> InlineKeyboardMarkup:
        add_task_button = InlineKeyboardButton(text=labels.ADD_TASK_BUTTON, callback_data="addtask")
        edit_folder_button = InlineKeyboardButton(text=labels.EDIT_FOLDER_BUTTON, callback_data="editfolder")
        delete_folder_button = InlineKeyboardButton(text=labels.DELETE_FOLDER_BUTTON, callback_data="deletefolder")
        keyboard_markup = [[add_task_button], [edit_folder_button, delete_folder_button], []]
        row_index = 2
        if tasks:

            for task in tasks.values():
                button = InlineKeyboardButton(
                    text=labels.TASK_THUMBNAIL.format(name=task.name),
                    callback_data=f"taskname_{task.name}"
                )
                keyboard_markup[row_index].append(button)
                row_index += 1
                keyboard_markup.append([])

        back_button = InlineKeyboardButton(text=labels.BACK_BUTTON, callback_data="back")
        exit_button = InlineKeyboardButton(text=labels.EXIT_BUTTON, callback_data="exit")
        keyboard_markup[row_index].append(back_button)
        keyboard_markup[row_index].append(exit_button)
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        return keyboard

    async def delete_folder_command(self, callback: CallbackQuery, state: FSMContext):
        folder: Folder = (await state.get_data())["selected_folder"]
        self.task_manager_handler.delete_folder(folder)
        await self.update_show_folders_command(callback, state)

    @staticmethod
    async def edit_folder_command(callback: CallbackQuery, state: FSMContext):
        await callback.answer(labels.NOT_IMPLEMENTED_ALERT)

    @staticmethod
    async def add_task_request_name_command(callback: CallbackQuery, state: FSMContext):
        await state.update_data(new_task={})
        await callback.message.answer(labels.REQUEST_TASK_NAME)
        await state.set_state(FSMTaskManager.new_task_request_name)

    @staticmethod
    async def add_task_request_description_command(message: Message, state: FSMContext):
        (await state.get_data())["new_task"].update({"name": message.text})
        await message.answer(labels.REQUEST_TASK_DESCRIPTION)
        await state.set_state(FSMTaskManager.new_task_request_description)

    @staticmethod
    async def add_task_request_due_date_command(message: Message, state: FSMContext):
        if message.text != "-":
            (await state.get_data())["new_task"].update({"description": message.text})
        inline_calendar = SimpleCalendar()
        await state.update_data(inline_calendar=inline_calendar)
        await message.answer(labels.REQUEST_TASK_DUE_DATE, reply_markup=await inline_calendar.start_calendar())

        await state.set_state(FSMTaskManager.new_task_request_due_date)

    @staticmethod
    async def add_task_request_repeat_command(callback: CallbackQuery, callback_data: dict, state: FSMContext):
        inline_calendar: SimpleCalendar = (await state.get_data())["inline_calendar"]
        selected, date = await inline_calendar.process_selection(callback, callback_data)
        if selected:
            (await state.get_data())["new_task"].update({"due_date": int(date.timestamp())})
            await callback.message.answer(labels.REQUEST_TASK_REPEAT)
            await state.set_state(FSMTaskManager.new_task_request_repeat)

    @staticmethod
    async def add_task_request_priority_command(message: Message, state: FSMContext):
        if message.text != '-':
            (await state.get_data())["new_task"].update({"repeat": message.text})

        msg_text = labels.REQUEST_TASK_PRIORITY
        keyboard_markup = [[
            InlineKeyboardButton(labels.PRIORITY_BUTTON_1, callback_data="priority_1"),
            InlineKeyboardButton(labels.PRIORITY_BUTTON_2, callback_data="priority_2"),
            InlineKeyboardButton(labels.PRIORITY_BUTTON_3, callback_data="priority_3"),
            InlineKeyboardButton(labels.PRIORITY_BUTTON_4, callback_data="priority_4")
        ]]
        await message.answer(text=msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_markup))
        await state.set_state(FSMTaskManager.new_task_request_priority)

    @staticmethod
    async def add_task_confirm(callback: CallbackQuery, state: FSMContext):
        (await state.get_data())["new_task"].update({"priority": callback.data.split('_')[1]})
        task_data = (await state.get_data())["new_task"]
        msg_text = labels.TASK_REVIEW_TITLE
        msg_text += labels.SHOW_FOLDER_TASK_FRAME.format(
            name=task_data["name"],
            priority=task_data["priority"],
            due_date=task_data["due_date"],
            repeat=task_data["repeat"],
            description=task_data["description"]
        )
        msg_text += labels.TASK_CONFIRM
        keyboard_markup = [[
            InlineKeyboardButton(
                text=labels.YES_BUTTON,
                callback_data="confirm_yes"
            ),
            InlineKeyboardButton(
                text=labels.NO_BUTTON,
                callback_data="confirm_no"
            )
        ]]
        await callback.message.answer(msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_markup))
        await state.set_state(FSMTaskManager.new_task_request_confirm)

    async def proceed_add_task(self, callback: CallbackQuery, state: FSMContext):
        match callback.data.split("_")[1]:
            case "yes":
                folder: Folder = (await state.get_data())["selected_folder"]
                new_task_data: dict = (await state.get_data())["new_task"]
                folder.add_task(**new_task_data)
            case "no":
                pass
        await state.update_data(new_task=None)
        await self.update_show_folder_command(callback, state)

    async def back_command(self, callback: CallbackQuery, state: FSMContext):
        prev_state = await state.get_state()
        match prev_state:
            case FSMTaskManager.select_folder_action:
                await self.update_show_folders_command(callback, state)

    @staticmethod
    async def show_task_command(message: Message, state: FSMContext):
        await message.answer(labels.NOT_IMPLEMENTED_ALERT)
        await state.clear()


class FSMTaskManager(StatesGroup):
    select_folders_action = State()
    select_folder_action = State()
    new_task_request_name = State()
    new_task_request_description = State()
    new_task_request_due_date = State()
    new_task_request_repeat = State()
    new_task_request_priority = State()
    new_task_request_confirm = State()
