from asyncio import sleep
from datetime import datetime

from aiogram import Dispatcher
from aiogram.filters import Command, StateFilter, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiogram3_calendar.simple_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram_timepicker.aiogram3_timepicker.full_time_picker import FullTimePicker, FullTimePickerCallback

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
            Text(text=['back']), ~StateFilter(default_state)
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
            self.add_task_request_time_command,
            StateFilter(FSMTaskManager.new_task_request_due_date), SimpleCalendarCallback.filter()
        )
        dispatcher.callback_query.register(
            self.add_task_request_repeat_command,
            StateFilter(FSMTaskManager.new_task_request_time), FullTimePickerCallback.filter()
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
        dispatcher.callback_query.register(
            self.show_task_command,
            StateFilter(FSMTaskManager.select_folder_action), Text(startswith="taskid")
        )

    @staticmethod
    async def proceed_exit_command(message: Message | CallbackQuery, state: FSMContext):
        left_message = await message.answer(labels.EXIT_DIALOG)
        await sleep(0.5)
        await (await state.get_data())["message"].delete()
        if isinstance(message, Message):
            await left_message.delete()
        await state.clear()

    async def show_folders_command(self, message: Message, state: FSMContext):
        folders = self.task_manager_handler.get_folders_by_user_id(message.from_user.id)[message.from_user.id]

        msg_text = self.get_text_show_folders(folders)
        keyboard = self.get_keyboard_show_folders(folders)
        main_message = await message.answer(msg_text, reply_markup=keyboard)

        await state.set_state(FSMTaskManager.select_folders_action)
        await state.update_data(message=main_message)

    async def update_show_folders_command(self, callback: CallbackQuery, state: FSMContext):
        folders = self.task_manager_handler.get_folders_by_user_id(callback.from_user.id)[callback.from_user.id]
        main_message: Message = (await state.get_data())["message"]

        msg_text = self.get_text_show_folders(folders)
        keyboard = self.get_keyboard_show_folders(folders)
        await main_message.edit_text(msg_text)
        await main_message.edit_reply_markup(reply_markup=keyboard)

        await state.update_data(selected_folder=None)
        await state.set_state(FSMTaskManager.select_folders_action)

    @staticmethod
    def get_text_show_folders(folders: list[Folder]) -> str:
        if folders:
            msg_text = labels.SHOW_FOLDERS_TITLE
            msg_text += "\n".join([
                labels.SHOW_FOLDERS_FOLDER_FRAME.format(folder_id=folder.id, tasks_amount=folder.get_tasks_amount())
                for folder in folders
            ])
        else:
            msg_text = labels.SHOW_FOLDERS_NO_FOLDERS

        return msg_text

    @staticmethod
    def get_keyboard_show_folders(folders: list[Folder]) -> InlineKeyboardMarkup:
        add_task_button = InlineKeyboardButton(text=labels.SHOW_FOLDERS_ADD_FOLDER_BUTTON, callback_data="addfolder")
        keyboard_markup = [[add_task_button]]

        if folders:
            keyboard_markup += [[InlineKeyboardButton(
                text=labels.SHOW_FOLDERS_SELECT_FOLDER_BUTTON.format(folder_id=folder.id),
                callback_data=f"folderid_{folder.id}"
            )]
                for folder in folders
            ]

        exit_button = InlineKeyboardButton(text=labels.EXIT_BUTTON, callback_data="exit")
        keyboard_markup.append([exit_button])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

        return keyboard

    async def add_folder(self, callback: CallbackQuery, state: FSMContext):
        self.task_manager_handler.add_folder(callback.from_user.id)

        await callback.answer(text=labels.CREATE_FOLDER_ALERT)
        await self.update_show_folders_command(callback, state)

    async def show_folder_command(self, callback: CallbackQuery, state: FSMContext):
        selected_folder = self.task_manager_handler.get_folder_by_folder_id(
            user_id=callback.from_user.id,
            folder_id=int(callback.data.split("_")[1])
        )
        tasks = selected_folder.active_tasks

        await state.update_data(selected_folder=selected_folder)

        msg_text = self.get_text_show_folder(tasks, selected_folder.id)
        keyboard = self.get_keyboard_show_folder(tasks)
        await callback.message.edit_text(msg_text, reply_markup=keyboard)

        await state.set_state(FSMTaskManager.select_folder_action)

    async def update_show_folder_command(self, callback: CallbackQuery, state: FSMContext):
        selected_folder = (await state.get_data())["selected_folder"]
        main_message: Message = (await state.get_data())["message"]
        tasks = selected_folder.active_tasks

        msg_text = self.get_text_show_folder(tasks, selected_folder.id)
        keyboard = self.get_keyboard_show_folder(tasks)
        await main_message.edit_text(text=msg_text)
        await main_message.edit_reply_markup(reply_markup=keyboard)

        await state.set_state(FSMTaskManager.select_folder_action)
        await state.update_data(message=main_message)

    @staticmethod
    def get_text_show_folder(tasks: dict[int:TaskCard], folder_id: int) -> str:
        msg_text = labels.SHOW_FOLDER_TITLE.format(folder_id=folder_id)

        if tasks:
            msg_text += "".join([labels.TASK_FRAME.format(
                    name=task.name,
                    priority=task.priority,
                    due_date=task.due_date,
                    repeat=task.repeat,
                    description=task.description
                ) for task in tasks.values()
            ])
        else:
            msg_text += labels.SHOW_FOLDER_NO_TASKS

        return msg_text

    @staticmethod
    def get_keyboard_show_folder(tasks: dict[int:TaskCard]) -> InlineKeyboardMarkup:
        add_task_button = InlineKeyboardButton(text=labels.ADD_TASK_BUTTON, callback_data="addtask")
        edit_folder_button = InlineKeyboardButton(text=labels.EDIT_FOLDER_BUTTON, callback_data="editfolder")
        delete_folder_button = InlineKeyboardButton(text=labels.DELETE_FOLDER_BUTTON, callback_data="deletefolder")

        keyboard_markup = [
            [add_task_button],
            [edit_folder_button, delete_folder_button]
        ]
        if tasks:
            keyboard_markup += [
                [InlineKeyboardButton(
                    text=labels.TASK_THUMBNAIL.format(name=task.name),
                    callback_data=f"taskid_{task.id}"
                )] for task in tasks.values()
            ]

        back_button = InlineKeyboardButton(text=labels.BACK_BUTTON, callback_data="back")
        exit_button = InlineKeyboardButton(text=labels.EXIT_BUTTON, callback_data="exit")
        keyboard_markup.append([back_button, exit_button])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        return keyboard

    async def delete_folder_command(self, callback: CallbackQuery, state: FSMContext):
        folder: Folder = (await state.get_data())["selected_folder"]

        self.task_manager_handler.delete_folder(folder)

        await callback.answer(labels.DELETE_FOLDER_ALERT.format(folder_id=folder.id))
        await self.update_show_folders_command(callback, state)

    @staticmethod
    async def edit_folder_command(callback: CallbackQuery, state: FSMContext):
        await callback.answer(labels.NOT_IMPLEMENTED_ALERT)

    @staticmethod
    async def add_task_request_name_command(callback: CallbackQuery, state: FSMContext):
        await state.update_data(new_task={})

        message = await callback.message.answer(labels.REQUEST_TASK_NAME)
        await state.update_data(new_task_message=message)

        await state.set_state(FSMTaskManager.new_task_request_name)

    @staticmethod
    async def add_task_request_description_command(message: Message, state: FSMContext):
        (await state.get_data())["new_task"].update({"name": message.text})
        new_task_message: Message = (await state.get_data())["new_task_message"]

        await new_task_message.edit_text(labels.REQUEST_TASK_DESCRIPTION)
        await state.set_state(FSMTaskManager.new_task_request_description)

    @staticmethod
    async def add_task_request_due_date_command(message: Message, state: FSMContext):
        if message.text != "-":
            (await state.get_data())["new_task"].update({"description": message.text})

        new_task_message: Message = (await state.get_data())["new_task_message"]

        await new_task_message.edit_text(labels.REQUEST_TASK_DUE_DATE)
        await new_task_message.edit_reply_markup(reply_markup=await SimpleCalendar().start_calendar())

        await state.set_state(FSMTaskManager.new_task_request_due_date)

    @staticmethod
    async def add_task_request_time_command(callback: CallbackQuery, callback_data: dict, state: FSMContext):
        selected, date = await SimpleCalendar().process_selection(callback, callback_data)

        if selected:
            (await state.get_data())["new_task"].update({"due_date": date})
            new_task_message: Message = (await state.get_data())["new_task_message"]

            keyboard = await FullTimePicker().start_picker()

            await new_task_message.edit_text(labels.REQUEST_TASK_TIME)
            await new_task_message.edit_reply_markup(reply_markup=keyboard)

            await state.set_state(FSMTaskManager.new_task_request_time)

    @staticmethod
    async def add_task_request_repeat_command(callback: CallbackQuery, callback_data: dict, state: FSMContext):
        selected, time = await FullTimePicker().process_selection(callback, callback_data)

        if selected:
            date: datetime = (await state.get_data())["new_task"]["due_date"]
            task_datetime = datetime(date.year, date.month, date.day, time.hour, time.minute)

            (await state.get_data())["new_task"].update({"due_date": task_datetime})
            new_task_message: Message = (await state.get_data())["new_task_message"]

            await new_task_message.edit_text(labels.REQUEST_TASK_REPEAT)
            await state.set_state(FSMTaskManager.new_task_request_repeat)

    @staticmethod
    async def add_task_request_priority_command(message: Message, state: FSMContext):
        if message.text != '-':
            (await state.get_data())["new_task"].update({"repeat": message.text})

        msg_text = labels.REQUEST_TASK_PRIORITY
        keyboard_markup = [[
            InlineKeyboardButton(text=labels.PRIORITY_BUTTON_1, callback_data="priority_1"),
            InlineKeyboardButton(text=labels.PRIORITY_BUTTON_2, callback_data="priority_2"),
            InlineKeyboardButton(text=labels.PRIORITY_BUTTON_3, callback_data="priority_3"),
            InlineKeyboardButton(text=labels.PRIORITY_BUTTON_4, callback_data="priority_4")
        ]]

        new_task_message: Message = (await state.get_data())["new_task_message"]

        await new_task_message.edit_text(text=msg_text)
        await new_task_message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_markup))
        await state.set_state(FSMTaskManager.new_task_request_priority)

    @staticmethod
    async def add_task_confirm(callback: CallbackQuery, state: FSMContext):
        (await state.get_data())["new_task"].update({"priority": callback.data.split('_')[1]})
        task_data = (await state.get_data())["new_task"]

        msg_text = labels.TASK_REVIEW_TITLE
        msg_text += labels.TASK_FRAME.format(
            name=task_data["name"],
            priority=task_data["priority"],
            due_date=task_data["due_date"],
            repeat=task_data["repeat"] if "repeat" in task_data.keys() else "-",
            description=task_data["description"] if "description" in task_data.keys() else "-"
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

        new_task_message: Message = (await state.get_data())["new_task_message"]

        await new_task_message.edit_text(text=msg_text)
        await new_task_message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_markup))
        await state.set_state(FSMTaskManager.new_task_request_confirm)

    async def proceed_add_task(self, callback: CallbackQuery, state: FSMContext):
        match callback.data.split("_")[1]:
            case "yes":
                folder: Folder = (await state.get_data())["selected_folder"]
                new_task_data: dict = (await state.get_data())["new_task"]
                folder.add_task(**new_task_data)
                await callback.answer(labels.ADD_TASK_COMPLETE)
            case "no":
                await callback.answer(labels.ADD_TASK_ABORT)

        new_task_message: Message = (await state.get_data())["new_task_message"]
        await new_task_message.delete()

        await state.update_data(new_task=None)
        await state.update_data(new_task_message=None)
        await self.update_show_folder_command(callback, state)

    async def back_command(self, callback: CallbackQuery, state: FSMContext):
        prev_state = await state.get_state()
        match prev_state:
            case FSMTaskManager.select_folder_action:
                await self.update_show_folders_command(callback, state)
            case FSMTaskManager.select_task_action:
                await self.update_show_folder_command(callback, state)

    async def show_task_command(self, callback: CallbackQuery, state: FSMContext):
        task_id = int(callback.data.split("_")[1])
        selected_folder: Folder = (await state.get_data())["selected_folder"]
        selected_task = selected_folder.get_task_by_id(task_id)
        main_message: Message = (await state.get_data())["message"]

        await state.update_data(selected_task=selected_task)

        msg_text = self.get_text_show_task(selected_task)
        keyboard = self.get_keyboard_show_task()
        await main_message.edit_text(text=msg_text)
        await main_message.edit_reply_markup(reply_markup=keyboard)

        await state.set_state(FSMTaskManager.select_task_action)


    @staticmethod
    def get_text_show_task(task: TaskCard):
        msg_text = labels.TASK_FRAME.format(
            name=task.name,
            description=task.description,
            due_date=task.due_date,
            repeat=task.repeat,
            priority=task.priority
        )
        return msg_text

    @staticmethod
    def get_keyboard_show_task() -> InlineKeyboardMarkup:
        complete_button = InlineKeyboardButton(text=labels.COMPLETE_TASK_BUTTON,
                                               callback_data="completetask")

        edit_name_button = InlineKeyboardButton(text=labels.EDIT_TASK_NAME_BUTTON,
                                                callback_data="edittask_name")
        edit_description_button = InlineKeyboardButton(text=labels.EDIT_TASK_DESCRIPTION_BUTTON,
                                                       callback_data="edittask_description")
        edit_due_date_button = InlineKeyboardButton(text=labels.EDIT_TASK_DUE_DATE_BUTTON,
                                                    callback_data="edittask_duedate")
        edit_repeat_button = InlineKeyboardButton(text=labels.EDIT_TASK_REPEAT_BUTTON,
                                                  callback_data="edittask_repeat")
        edit_priority_button = InlineKeyboardButton(text=labels.EDIT_TASK_PRIORITY_BUTTON,
                                                    callback_data="edittask_priority")

        delete_button = InlineKeyboardButton(text=labels.DELETE_TASK_BUTTON,
                                             callback_data="deletetask")

        back_button = InlineKeyboardButton(text=labels.BACK_BUTTON, callback_data="back")
        exit_button = InlineKeyboardButton(text=labels.EXIT_BUTTON, callback_data="exit")
        keyboard_markup = [
            [complete_button],
            [edit_name_button, edit_description_button],
            [edit_due_date_button, edit_repeat_button, edit_priority_button],
            [delete_button],
            [back_button, exit_button]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        return keyboard


class FSMTaskManager(StatesGroup):
    select_folders_action = State()
    select_folder_action = State()
    select_task_action = State()
    new_task_request_name = State()
    new_task_request_description = State()
    new_task_request_due_date = State()
    new_task_request_time = State()
    new_task_request_repeat = State()
    new_task_request_priority = State()
    new_task_request_confirm = State()
