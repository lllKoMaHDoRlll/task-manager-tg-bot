from typing import NoReturn

from backend.data_classes import PriorityLevel


class TaskCard:
    def __init__(self, id_: int, name: str, parent, description: str = "", due_date=None, repeat=None,
                 priority: PriorityLevel = PriorityLevel.NO):
        self.id = id_
        self.name = name
        self.parent = parent
        self.description = description
        self.due_date = due_date
        self.repeat = repeat
        self.priority = priority

    def get_attrs(self) -> dict:
        data = dict()
        data["id"] = self.id
        data["name"] = self.name
        data["parent"] = self.parent.id
        data["description"] = self.description
        data["due_date"] = self.due_date
        data["repeat"] = self.repeat
        data["priority"] = self.priority.value

        return data

    def edit_name(self, new_name: str) -> str:
        self.name = new_name
        return self.name

    def edit_parent(self, new_parent):
        self.parent = new_parent
        return self.parent

    def edit_description(self, new_description: str) -> str:
        self.description = new_description
        return self.description

    def edit_due_date(self, new_due_date):
        self.due_date = new_due_date
        return self.due_date

    def edit_repeat(self, new_repeat):
        self.repeat = new_repeat
        return self.repeat

    def edit_priority(self, new_priority: PriorityLevel) -> PriorityLevel:
        self.priority = new_priority
        return self.priority

    def delete(self) -> NoReturn:
        self.parent.remove_task(self)

    def complete(self) -> NoReturn:
        raise NotImplemented
