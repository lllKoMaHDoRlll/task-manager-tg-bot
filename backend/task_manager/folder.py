import json
from pathlib import Path
from datetime import datetime

from backend.data_classes import PriorityLevel
from backend.task_manager.task_card import TaskCard
from backend.exceptions import LoadFailed


class Folder:
    def __init__(self, user_id: int, id_: int, data_path: Path):
        self.user_id = user_id
        self.id = id_
        self.data_path = data_path
        self.active_tasks: dict[int, TaskCard] = dict()

    def load(self, path: Path) -> None:
        if path.exists():
            try:
                with open(path, "r") as file:
                    data = json.load(file)

                for task_id in data:
                    self._add_task(**(data[task_id]))
            except Exception:
                raise LoadFailed("Error while loading tasks")
        else:
            raise LoadFailed("Tasks' data file not exists")

    def save(self) -> None:
        json.dump({task.id: task.get_attrs() for task in self.active_tasks.values()}, self.data_path.open("w"), indent=4)

    def get_tasks_amount(self) -> int:
        return self.active_tasks.__len__()

    def _get_available_task_id(self) -> int:
        tasks_ids = [task.id for task in self.active_tasks.values()]
        for index in range(len(tasks_ids)):
            if index not in tasks_ids:
                return index
        return len(tasks_ids)

    def get_task_by_id(self, id_: int) -> TaskCard | None:
        for task in self.active_tasks.values():
            if task.id == id_:
                return task
        return None

    def _add_task(self, name: str, due_date: datetime, description: str = "", repeat: str | None = None,
                  priority: int = 4, **kwargs) -> TaskCard:
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        task = TaskCard(
            id_=self._get_available_task_id(),
            name=name,
            parent=self,
            due_date=due_date,
            description=description,
            repeat=repeat,
            priority=PriorityLevel(int(priority))
        )
        self.active_tasks.update({task.id: task})
        return task

    def add_new_task(self, name: str, due_date: datetime, description: str = "", repeat=None,
                     priority: int = 4, **kwargs) -> TaskCard:
        task = self._add_task(
            name=name,
            description=description,
            due_date=due_date,
            repeat=repeat,
            priority=priority
        )
        self.save()
        return task

    def remove_task(self, task: TaskCard) -> None:
        self.active_tasks.pop(task.id)
        self.save()

    def complete_task(self, task: TaskCard) -> None:
        self.remove_task(task)

