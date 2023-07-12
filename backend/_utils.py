import json
import aiohttp
from pathlib import Path
from typing import NoReturn

from aiogram import Bot

from backend.data_classes import ConfigData, WEEKDAYS
from backend.exceptions import ConfigLoadFailed, MakingRequestFailed, RepeatTimeFormattingFailed
from backend.task_manager.task_card import TaskCard
from backend.task_manager.labels import TASK_FRAME


def get_config(config_path: Path = Path("./data/config.json")) -> ConfigData:
    if config_path.exists():
        try:
            with open(config_path, "r") as file:
                config_data = json.load(file)
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
        repeat_text = repeat_text.split()
        if repeat_text[0] != 'every':
            raise RepeatTimeFormattingFailed("First word must be every")
        if repeat_text[1] == 'day':
            delta = 86400
        elif repeat_text[1] in WEEKDAYS:
            delta = 86400 * 7
        elif repeat_text[1].isdecimal() and repeat_text[2] == 'days':
            delta = 86400 * int(repeat_text[1])
        else:
            raise RepeatTimeFormattingFailed("Invalid repeat text format")

        return delta
    except Exception:
        raise RepeatTimeFormattingFailed("Error with formatting repeat text")


async def send_notification(bot: Bot, chat_id: int, task: TaskCard):
    msg_text = TASK_FRAME.format(
        name=task.name,
        priority=task.priority,
        description=task.description,
        due_date=task.due_date,
        repeat=task.repeat
    )
    await bot.send_message(chat_id=chat_id, text=msg_text)
