import json
from pathlib import Path

from backend.data_classes import PriorityLevel
from backend.task_manager.task_card import TaskCard
from backend.exceptions import LoadFailed


class Folder:
    def __init__(self, user_id: int, id_: int):
        self.user_id = user_id
        self.id = id_
        self.active_tasks = dict()

    def load(self, path: Path) -> None:
        if path.exists():
            try:
                with open(path, "r") as file:
                    data = json.load(file)

                for task in data:
                    self.add_task(**task)
            except:
                raise LoadFailed
        else:
            raise LoadFailed

    def save(self, path: Path) -> None:
        json.dump({task.id: task.get_attrs() for task in self.active_tasks}, path.open("w"), indent=4)

    def get_available_task_id(self):
        tasks_ids = [task.id for task in self.active_tasks]
        for index in range(len(tasks_ids)):
            if index not in tasks_ids:
                return index
        return len(tasks_ids)

    def add_task(self, name: str, parent=None, description: str = "", due_date=None, repeat=None,
                 priority: int = 4) -> TaskCard:
        task = TaskCard(self.get_available_task_id(), name, self, description, due_date, repeat, PriorityLevel(priority))
        self.active_tasks.update({task.id: task})
        return task

    def remove_task(self, task: TaskCard) -> None:
        self.active_tasks.pop(task.id)

