import json
from pathlib import Path

from backend.data_classes import PriorityLevel
from backend.task_manager.task_card import TaskCard
from backend.exceptions import FolderLoadFailed


class Folder:
    def __init__(self, user_id: int, id_: int):
        self.user_id = user_id
        self.id = id_
        self.active_tasks = []

    def load(self, path: Path):
        if path.exists():
            try:
                with open(path, "r") as file:
                    data = json.load(file)

                for task in data:
                    self.add_task(**task)
            except:
                raise FolderLoadFailed
        else:
            raise FolderLoadFailed


    def save(self, path: Path):
        raise NotImplemented

    def add_task(self, name: str, parent, description: str = "", due_date=None, repeat=None,
                 priority: PriorityLevel = PriorityLevel.NO) -> TaskCard:
        task = TaskCard(name, parent, description, due_date, repeat, priority)
        self.active_tasks.append(task)
        return task

    def remove_task(self, task: TaskCard) -> None:
        self.active_tasks.remove(task)
