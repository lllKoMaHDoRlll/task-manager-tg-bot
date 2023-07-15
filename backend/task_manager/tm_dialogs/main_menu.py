from asyncio import sleep

from aiogram import Dispatcher
from aiogram.filters import Command, StateFilter, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from backend.task_manager.folder import Folder
from backend.task_manager.task_card import TaskCard
from backend.task_manager.tm_handler import TaskManagerHandler
from backend.task_manager import labels
from backend.task_manager.tm_dialogs.new_task import TaskManagerNewTask
from backend.task_manager.tm_dialogs.menu_types import (
    FoldersActions, FolderCallback, FolderActions, FoldersCallback, TaskActions, TaskCallback
)


class TaskManagerMainMenu:
    def __init__(self, task_manager_handler: TaskManagerHandler):
        self.task_manager_handler = task_manager_handler
        self.fsm_tm_new_task = TaskManagerNewTask(task_manager_handler, on_exit=self.update_show_folder_command)

    def register(self, dispatcher: Dispatcher):
        self.fsm_tm_new_task.register(dispatcher)
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
            self.process_folders_action,
            StateFilter(FSMTaskManager.select_folders_action), FoldersCallback.filter()
        )
        dispatcher.callback_query.register(
            self.process_folder_action,
            StateFilter(FSMTaskManager.select_folder_action), FolderCallback.filter()
        )
        dispatcher.callback_query.register(
            self.process_task_action,
            StateFilter(FSMTaskManager.select_task_action), TaskCallback.filter()
        )

    @staticmethod
    async def proceed_exit_command(query: CallbackQuery, state: FSMContext):
        await query.answer(labels.EXIT_DIALOG)
        await sleep(0.5)
        await (await state.get_data())["message"].delete()
        await state.clear()

    async def show_folders_command(self, message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return None

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
        add_task_button = InlineKeyboardButton(
            text=labels.SHOW_FOLDERS_ADD_FOLDER_BUTTON,
            callback_data=FoldersCallback(act=FoldersActions.ADD_FOLDER).pack()
        )
        keyboard_markup = [[add_task_button]]

        if folders:
            keyboard_markup += [[InlineKeyboardButton(
                text=labels.SHOW_FOLDERS_SELECT_FOLDER_BUTTON.format(folder_id=folder.id),
                callback_data=FoldersCallback(act=FoldersActions.SELECT_FOLDER, folder_id=folder.id).pack()
            )]
                for folder in folders
            ]

        exit_button = InlineKeyboardButton(
            text=labels.EXIT_BUTTON,
            callback_data=FoldersCallback(act=FoldersActions.EXIT).pack()
        )
        keyboard_markup.append([exit_button])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

        return keyboard

    async def process_folders_action(self, query: CallbackQuery, callback_data: FoldersCallback, state: FSMContext):
        match callback_data.act:
            case FoldersActions.ADD_FOLDER:
                await self.add_folder(query=query, state=state)
            case FoldersActions.SELECT_FOLDER:
                await self.show_folder_command(query=query, data=callback_data, state=state)
            case FoldersActions.EXIT:
                await self.proceed_exit_command(query=query, state=state)
            case _:
                raise ValueError(f"Incorrect action value: {callback_data.act}")

    async def add_folder(self, query: CallbackQuery, state: FSMContext):
        self.task_manager_handler.add_folder(query.from_user.id)

        await query.answer(text=labels.CREATE_FOLDER_ALERT)
        await self.update_show_folders_command(query, state)

    async def show_folder_command(self, query: CallbackQuery, data: FoldersCallback, state: FSMContext):
        if not query.data or not query.message or data.folder_id is None:
            return None
        selected_folder = self.task_manager_handler.get_folder_by_folder_id(
            user_id=query.from_user.id,
            folder_id=data.folder_id
        )

        await state.update_data(selected_folder=selected_folder)

        msg_text = self.get_text_show_folder(selected_folder)
        keyboard = self.get_keyboard_show_folder(selected_folder)
        await query.message.edit_text(msg_text, reply_markup=keyboard)

        await state.set_state(FSMTaskManager.select_folder_action)

    async def update_show_folder_command(self, state: FSMContext):
        selected_folder = (await state.get_data())["selected_folder"]
        main_message: Message = (await state.get_data())["message"]

        msg_text = self.get_text_show_folder(selected_folder)
        keyboard = self.get_keyboard_show_folder(selected_folder)
        await main_message.edit_text(text=msg_text)
        await main_message.edit_reply_markup(reply_markup=keyboard)

        await state.set_state(FSMTaskManager.select_folder_action)
        await state.update_data(message=main_message)

    @staticmethod
    def get_text_show_folder(folder: Folder) -> str:
        msg_text = labels.SHOW_FOLDER_TITLE.format(folder_id=folder.id)

        tasks = folder.active_tasks
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
    def get_keyboard_show_folder(folder: Folder) -> InlineKeyboardMarkup:
        tasks = folder.active_tasks
        add_task_button = InlineKeyboardButton(
            text=labels.ADD_TASK_BUTTON,
            callback_data=FolderCallback(act=FolderActions.ADD_TASK, folder_id=folder.id).pack()
        )
        edit_folder_button = InlineKeyboardButton(
            text=labels.EDIT_FOLDER_BUTTON,
            callback_data=FolderCallback(act=FolderActions.EDIT_FOLDER, folder_id=folder.id).pack()
        )
        delete_folder_button = InlineKeyboardButton(
            text=labels.DELETE_FOLDER_BUTTON,
            callback_data=FolderCallback(act=FolderActions.DELETE_FOLDER, folder_id=folder.id).pack()
        )

        keyboard_markup = [
            [add_task_button],
            [edit_folder_button, delete_folder_button]
        ]
        if tasks:
            keyboard_markup += [
                [InlineKeyboardButton(
                    text=labels.TASK_THUMBNAIL.format(name=task.name),
                    callback_data=FolderCallback(
                        act=FolderActions.SELECT_TASK,
                        folder_id=folder.id,
                        task_id=task.id
                    ).pack()
                )] for task in tasks.values()
            ]

        back_button = InlineKeyboardButton(
            text=labels.BACK_BUTTON,
            callback_data=FolderCallback(act=FolderActions.BACK, folder_id=folder.id).pack()
        )
        exit_button = InlineKeyboardButton(
            text=labels.EXIT_BUTTON,
            callback_data=FolderCallback(act=FolderActions.EXIT, folder_id=folder.id).pack()
        )
        keyboard_markup.append([back_button, exit_button])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        return keyboard

    async def process_folder_action(
            self, query: CallbackQuery, callback_data: FolderCallback, state: FSMContext
    ):
        match callback_data.act:
            case FolderActions.DELETE_FOLDER:
                await self.delete_folder_command(query=query, state=state)
            case FolderActions.EDIT_FOLDER:
                await self.edit_folder_command(query=query)
            case FolderActions.BACK:
                await self.back_command(query=query, state=state)
            case FolderActions.SELECT_TASK:
                await self.show_task_command(data=callback_data, state=state)
            case FolderActions.ADD_TASK:
                await self.fsm_tm_new_task.add_task_request_name_command(query=query, state=state)
            case FolderActions.EXIT:
                await self.proceed_exit_command(query=query, state=state)
            case _:
                raise ValueError(f"Incorrect action value: {callback_data.act}")

    async def delete_folder_command(self,
                                    query: CallbackQuery, state: FSMContext):
        folder: Folder = (await state.get_data())["selected_folder"]

        self.task_manager_handler.delete_folder(folder)

        await query.answer(labels.DELETE_FOLDER_ALERT.format(folder_id=folder.id))
        await self.update_show_folders_command(query, state)

    @staticmethod
    async def edit_folder_command(query: CallbackQuery):
        await query.answer(labels.NOT_IMPLEMENTED_ALERT)

    async def back_command(self, query: CallbackQuery, state: FSMContext):
        prev_state = await state.get_state()
        match prev_state:
            case FSMTaskManager.select_folder_action:
                await self.update_show_folders_command(query, state)
            case FSMTaskManager.select_task_action:
                await self.update_show_folder_command(state)

    async def show_task_command(self, data: FolderCallback, state: FSMContext):
        if data.task_id is None:
            return None

        selected_folder: Folder = (await state.get_data())["selected_folder"]
        selected_task = selected_folder.get_task_by_id(data.task_id)
        if not selected_task:
            return None
        main_message: Message = (await state.get_data())["message"]

        await state.update_data(selected_task=selected_task)

        msg_text = self.get_text_show_task(selected_task)
        keyboard = self.get_keyboard_show_task(selected_task)
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
    def get_keyboard_show_task(task: TaskCard) -> InlineKeyboardMarkup:
        complete_button = InlineKeyboardButton(
            text=labels.COMPLETE_TASK_BUTTON,
            callback_data=TaskCallback(act=TaskActions.COMPLETE_TASK, folder_id=task.parent.id, task_id=task.id).pack()
        )

        edit_name_button = InlineKeyboardButton(
            text=labels.EDIT_TASK_NAME_BUTTON,
            callback_data=TaskCallback(act=TaskActions.EDIT_TASK_NAME, folder_id=task.parent.id, task_id=task.id).pack()
        )
        edit_description_button = InlineKeyboardButton(
            text=labels.EDIT_TASK_DESCRIPTION_BUTTON,
            callback_data=TaskCallback(act=TaskActions.EDIT_TASK_DESCRIPTION, folder_id=task.parent.id,
                                       task_id=task.id).pack()
        )
        edit_due_date_button = InlineKeyboardButton(
            text=labels.EDIT_TASK_DUE_DATE_BUTTON,
            callback_data=TaskCallback(act=TaskActions.EDIT_TASK_DUE_DATE, folder_id=task.parent.id,
                                       task_id=task.id).pack()
        )
        edit_repeat_button = InlineKeyboardButton(
            text=labels.EDIT_TASK_REPEAT_BUTTON,
            callback_data=TaskCallback(act=TaskActions.EDIT_TASK_REPEAT, folder_id=task.parent.id,
                                       task_id=task.id).pack()
        )
        edit_priority_button = InlineKeyboardButton(
            text=labels.EDIT_TASK_PRIORITY_BUTTON,
            callback_data=TaskCallback(act=TaskActions.EDIT_TASK_PRIORITY, folder_id=task.parent.id,
                                       task_id=task.id).pack()
        )

        delete_button = InlineKeyboardButton(
            text=labels.DELETE_TASK_BUTTON,
            callback_data=TaskCallback(act=TaskActions.DELETE_TASK, folder_id=task.parent.id, task_id=task.id).pack()
        )

        back_button = InlineKeyboardButton(
            text=labels.BACK_BUTTON,
            callback_data=TaskCallback(act=TaskActions.BACK, folder_id=task.parent.id, task_id=task.id).pack()
        )
        exit_button = InlineKeyboardButton(
            text=labels.EXIT_BUTTON,
            callback_data=TaskCallback(act=TaskActions.EXIT, folder_id=task.parent.id, task_id=task.id).pack()
        )
        keyboard_markup = [
            [complete_button],
            [edit_name_button, edit_description_button],
            [edit_due_date_button, edit_repeat_button, edit_priority_button],
            [delete_button],
            [back_button, exit_button]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)
        return keyboard

    async def process_task_action(self,
                                  query: CallbackQuery, callback_data: TaskCallback, state: FSMContext):
        match callback_data.act:
            case TaskActions.DELETE_TASK:
                pass
            case TaskActions.BACK:
                await self.back_command(query=query, state=state)
            case TaskActions.COMPLETE_TASK:
                await self.proceed_task_completion(query=query, state=state)
            case TaskActions.EDIT_TASK_DESCRIPTION:
                pass
            case TaskActions.EDIT_TASK_DUE_DATE:
                pass
            case TaskActions.EDIT_TASK_NAME:
                pass
            case TaskActions.EDIT_TASK_PRIORITY:
                pass
            case TaskActions.EDIT_TASK_REPEAT:
                pass
            case TaskActions.EXIT:
                await self.proceed_exit_command(query=query, state=state)
            case _:
                raise ValueError(f"Incorrect action value: {callback_data.act}")

    async def proceed_task_completion(self, query: CallbackQuery, state: FSMContext):
        message: Message = (await state.get_data())["message"]
        folder: Folder = (await state.get_data())["selected_folder"]
        task: TaskCard = (await state.get_data())["selected_task"]
        await self.task_manager_handler.complete_task(task)
        await query.answer(text=labels.TASK_COMPLETE_NOTIFICATION)

        msg_text = self.get_text_show_folder(folder)
        keyboard = self.get_keyboard_show_folder(folder)

        await message.edit_text(text=msg_text)
        await message.edit_reply_markup(reply_markup=keyboard)
        await state.set_state(FSMTaskManager.select_folder_action)


class FSMTaskManager(StatesGroup):
    select_folders_action = State()
    select_folder_action = State()
    select_task_action = State()
