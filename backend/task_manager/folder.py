import json
from pathlib import Path


class Folder:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.active_tasks = []

    def load(self, path: Path):
        raise NotImplemented
