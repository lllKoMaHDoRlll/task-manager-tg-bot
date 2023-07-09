import os
from pathlib import Path

from backend.exceptions import LoadFailed
from backend.task_manager.folder import Folder


class TaskManagerHandler:
    def __init__(self, data_path: Path):
        self.folders = dict()
        self.data_path = data_path

    def get_folders_by_user_id(self, user_id: int) -> dict:
        if str(user_id) in self.folders.keys():
            return {user_id: self.folders[str(user_id)]}
        else:
            return {user_id: []}

    def add_folder(self, user_id: int) -> None:
        folder_path = self.data_path.joinpath(str(user_id))
        if not folder_path.exists():
            self.folders.update({str(user_id): []})
            os.mkdir(folder_path)
        folder_id = self.get_available_folder_id(folder_path)
        folder = Folder(user_id, folder_id)
        self.folders[str(user_id)].append(folder)

    def load(self):
        if self.data_path.exists():
            try:
                for user_id in os.listdir(self.data_path):
                    path_to_user = self.data_path.joinpath(user_id)
                    folders = []
                    for folder_id in os.listdir(path_to_user):
                        path_to_folder = path_to_user.joinpath(folder_id)
                        folder = Folder(int(user_id), int(folder_id[:-5]))
                        folder.load(path_to_folder)
                        folders.append(folder)

                    self.folders.update({user_id: folders})

            except:
                raise LoadFailed
        else:
            raise LoadFailed

    def save(self):
        for user_id in self.folders:
            path_to_user = self.data_path.joinpath(user_id)
            for folder in self.folders[user_id]:
                path_to_folder = path_to_user.joinpath(f"{folder.id}.json")
                folder.save(path_to_folder)

    @staticmethod
    def get_available_folder_id(path: Path):
        files = [int(file[:5]) for file in os.listdir(path)]

        prob_id = 0
        for _ in range(len(files)):
            if prob_id not in files:
                return int(prob_id)
            prob_id += 1
        return int(prob_id) + 1
