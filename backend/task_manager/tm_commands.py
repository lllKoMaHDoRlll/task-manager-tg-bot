from backend.task_manager.tm_handler import TaskManagerHandler
from aiogram.types import Message


class TaskManagerCommands:
    def __init__(self, task_manager_handler: TaskManagerHandler):
        self.task_manager_handler = task_manager_handler


