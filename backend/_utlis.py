import json
import aiohttp
from pathlib import Path
from typing import NoReturn

from backend.data_classes import ConfigData
from backend.exceptions import ConfigLoadFailed, MakingRequestFailed


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


async def make_request_get(url: str, params: dict | None = None) -> str | NoReturn:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                return await resp.json()
    except:
        raise MakingRequestFailed
