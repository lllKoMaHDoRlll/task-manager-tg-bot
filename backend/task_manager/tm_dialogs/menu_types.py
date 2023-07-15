from enum import IntEnum

from aiogram.filters.callback_data import CallbackData


class FoldersActions(IntEnum):
    ADD_FOLDER = 0
    SELECT_FOLDER = 1
    EXIT = 2


class FoldersCallback(CallbackData, prefix="folders_actions"):
    act: FoldersActions
    folder_id: int | None = None


class FolderActions(IntEnum):
    ADD_TASK = 0
    EDIT_FOLDER = 1
    DELETE_FOLDER = 2
    SELECT_TASK = 3
    BACK = 4
    EXIT = 5


class FolderCallback(CallbackData, prefix="folder_actions"):
    act: FolderActions
    folder_id: int
    task_id: int | None = None


class TaskActions(IntEnum):
    COMPLETE_TASK = 0
    EDIT_TASK_NAME = 1
    EDIT_TASK_DESCRIPTION = 2
    EDIT_TASK_DUE_DATE = 3
    EDIT_TASK_REPEAT = 4
    EDIT_TASK_PRIORITY = 5
    DELETE_TASK = 6
    BACK = 7
    EXIT = 8


class TaskCallback(CallbackData, prefix="task_actions"):
    act: TaskActions
    folder_id: int
    task_id: int
