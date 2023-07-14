from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Dispatcher
from aiogram.filters import StateFilter, Text

from aiogram3_calendar.simple_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram_timepicker.aiogram3_timepicker.full_time_picker import FullTimePicker, FullTimePickerCallback
from datetime import datetime
from typing import Callable

from backend.task_manager.tm_handler import TaskManagerHandler
from backend.task_manager.folder import Folder
from backend.task_manager import labels


class TaskManagerNewTask:
    def __init__(self, task_manager_handler: TaskManagerHandler, on_exit: Callable):
        self.task_manager_handler = task_manager_handler
        self.on_exit = on_exit

    def register(self, dispatcher: Dispatcher):
        dispatcher.message.register(
            self.add_task_request_description_command,
            StateFilter(FSMTaskManagerNewTask.new_task_request_name)
        )
        dispatcher.message.register(
            self.add_task_request_due_date_command,
            StateFilter(FSMTaskManagerNewTask.new_task_request_description)
        )
        dispatcher.callback_query.register(
            self.add_task_request_time_command,
            StateFilter(FSMTaskManagerNewTask.new_task_request_due_date), SimpleCalendarCallback.filter()
        )
        dispatcher.callback_query.register(
            self.add_task_request_repeat_command,
            StateFilter(FSMTaskManagerNewTask.new_task_request_time), FullTimePickerCallback.filter()
        )
        dispatcher.message.register(
            self.add_task_request_priority_command,
            StateFilter(FSMTaskManagerNewTask.new_task_request_repeat)
        )
        dispatcher.callback_query.register(
            self.add_task_confirm,
            StateFilter(FSMTaskManagerNewTask.new_task_request_priority), Text(startswith="priority")
        )
        dispatcher.callback_query.register(
            self.proceed_add_task,
            StateFilter(FSMTaskManagerNewTask.new_task_request_confirm), Text(startswith="confirm")
        )
    @staticmethod
    async def add_task_request_name_command(callback: CallbackQuery, state: FSMContext):
        await state.update_data(new_task={})

        message = await callback.message.answer(labels.REQUEST_TASK_NAME)
        await state.update_data(new_task_message=message)

        await state.set_state(FSMTaskManagerNewTask.new_task_request_name)

    @staticmethod
    async def add_task_request_description_command(message: Message, state: FSMContext):
        (await state.get_data())["new_task"].update({"name": message.text})
        new_task_message: Message = (await state.get_data())["new_task_message"]

        await new_task_message.edit_text(labels.REQUEST_TASK_DESCRIPTION)
        await state.set_state(FSMTaskManagerNewTask.new_task_request_description)

    @staticmethod
    async def add_task_request_due_date_command(message: Message, state: FSMContext):
        if message.text != "-":
            (await state.get_data())["new_task"].update({"description": message.text})

        new_task_message: Message = (await state.get_data())["new_task_message"]

        await new_task_message.edit_text(labels.REQUEST_TASK_DUE_DATE)
        await new_task_message.edit_reply_markup(reply_markup=await SimpleCalendar().start_calendar())

        await state.set_state(FSMTaskManagerNewTask.new_task_request_due_date)

    @staticmethod
    async def add_task_request_time_command(callback: CallbackQuery, callback_data: dict, state: FSMContext):
        selected, date = await SimpleCalendar().process_selection(callback, callback_data)

        if selected:
            (await state.get_data())["new_task"].update({"due_date": date})
            new_task_message: Message = (await state.get_data())["new_task_message"]

            keyboard = await FullTimePicker().start_picker()

            await new_task_message.edit_text(labels.REQUEST_TASK_TIME)
            await new_task_message.edit_reply_markup(reply_markup=keyboard)

            await state.set_state(FSMTaskManagerNewTask.new_task_request_time)

    @staticmethod
    async def add_task_request_repeat_command(callback: CallbackQuery, callback_data: dict, state: FSMContext):
        selected, time = await FullTimePicker().process_selection(callback, callback_data)

        if selected:
            date: datetime = (await state.get_data())["new_task"]["due_date"]
            task_datetime = datetime(date.year, date.month, date.day, time.hour, time.minute)

            (await state.get_data())["new_task"].update({"due_date": task_datetime})
            new_task_message: Message = (await state.get_data())["new_task_message"]

            await new_task_message.edit_text(labels.REQUEST_TASK_REPEAT)
            await state.set_state(FSMTaskManagerNewTask.new_task_request_repeat)

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
        await state.set_state(FSMTaskManagerNewTask.new_task_request_priority)

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
        await state.set_state(FSMTaskManagerNewTask.new_task_request_confirm)

    async def proceed_add_task(self, callback: CallbackQuery, state: FSMContext):
        match callback.data.split("_")[1]:
            case "yes":
                folder: Folder = (await state.get_data())["selected_folder"]
                new_task_data: dict = (await state.get_data())["new_task"]
                task = folder.add_new_task(**new_task_data)
                await self.task_manager_handler.task_scheduler.schedule_task(task, callback.from_user.id)
                await callback.answer(labels.ADD_TASK_COMPLETE)
            case "no":
                await callback.answer(labels.ADD_TASK_ABORT)

        new_task_message: Message = (await state.get_data())["new_task_message"]
        await new_task_message.delete()

        await state.update_data(new_task=None)
        await state.update_data(new_task_message=None)
        await self.on_exit(callback, state)


class FSMTaskManagerNewTask(StatesGroup):
    new_task_request_name = State()
    new_task_request_description = State()
    new_task_request_due_date = State()
    new_task_request_time = State()
    new_task_request_repeat = State()
    new_task_request_priority = State()
    new_task_request_confirm = State()