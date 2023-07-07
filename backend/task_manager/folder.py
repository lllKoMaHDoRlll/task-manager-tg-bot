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

    def load(self, path: Path) -> None:
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

    def save(self, path: Path) -> None:
        json.dump([task.get_attrs() for task in self.active_tasks], path.open("w"), indent=4)

    def add_task(self, name: str, parent=None, description: str = "", due_date=None, repeat=None,
                 priority: int = 4) -> TaskCard:
        task = TaskCard(name, self, description, due_date, repeat, PriorityLevel(int))
        self.active_tasks.append(task)
        return task

    def remove_task(self, task: TaskCard) -> None:
        self.active_tasks.remove(task)
