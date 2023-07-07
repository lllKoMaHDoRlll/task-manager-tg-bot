import os
from pathlib import Path

from backend.exceptions import LoadFailed
from backend.task_manager.folder import Folder


class TaskManagerHandler:
    def __init__(self, data_path: Path):
        self.folders = dict()
        self.data_path = data_path

    def load(self):
        if self.data_path.exists():
            try:
                for user_id in os.listdir(self.data_path):
                    path_to_user = self.data_path.joinpath(user_id)
                    folders = []
                    for folder_id in os.listdir(path_to_user):
                        print(folder_id[:-5])
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
        raise NotImplemented


