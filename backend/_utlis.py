import json
import aiohttp
from pathlib import Path
from typing import NoReturn

from backend.data_classes import ConfigData
from backend.exceptions import ConfigLoadFailed


def get_config(config_path: Path = Path("./data/config.json")) -> ConfigData:
    if config_path.exists():
        try:
            with open(config_path, "r") as file:
                config_data = json.load(file)
            config_data = ConfigData(**config_data)
            return config_data
        except:
            raise ConfigLoadFailed
    else:
        raise ConfigLoadFailed



