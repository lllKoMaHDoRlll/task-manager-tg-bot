import json
import os
import aiohttp
from pathlib import Path
from typing import NoReturn

from backend.data_classes import ConfigData, WEEKDAYS
from backend.exceptions import ConfigLoadFailed, MakingRequestFailed, RepeatTimeFormattingFailed


def get_config(config_path: Path = Path("./data/config.json")) -> ConfigData:
    if config_path.exists():
        try:
            with open(config_path, "r") as file:
                config_data = json.load(file)
                config_data.update({"token": os.getenv("TOKEN")})
            config_data = ConfigData(**config_data)
            return config_data
        except Exception:
            raise ConfigLoadFailed("Error while loading config")
    else:
        raise ConfigLoadFailed("Config data file not exists")


async def make_request_get(url: str, params: dict | None = None) -> str | NoReturn:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                return await resp.json()
    except Exception:
        raise MakingRequestFailed


def format_repeat_time(repeat_text: str) -> int | NoReturn:
    try:
        repeat_text_ = repeat_text.split()
        if repeat_text_[0] != 'every':
            raise RepeatTimeFormattingFailed("First word must be every")
        if repeat_text_[1] == 'day':
            delta = 86400
        elif repeat_text_[1] in WEEKDAYS:
            delta = 86400 * 7
        elif repeat_text_[1].isdecimal() and repeat_text_[2] == 'days':
            delta = 86400 * int(repeat_text_[1])
        else:
            raise RepeatTimeFormattingFailed("Invalid repeat text format")

        return delta
    except Exception:
        raise RepeatTimeFormattingFailed("Error with formatting repeat text")
