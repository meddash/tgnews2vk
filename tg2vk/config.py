from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class ChannelConfig:
    tg_channel: str | int
    source_title: str
    vk_peer_id: int


@dataclass(frozen=True)
class AppConfig:
    tg_api_id: int
    tg_api_hash: str
    tg_session: str
    vk_access_token: str
    vk_api_version: str
    channels_config_path: Path
    log_level: str


def load_config() -> AppConfig:
    load_dotenv()

    return AppConfig(
        tg_api_id=_get_env_int("TG_API_ID"),
        tg_api_hash=_get_env_str("TG_API_HASH"),
        tg_session=_get_env_str("TG_SESSION"),
        vk_access_token=_get_env_str("VK_ACCESS_TOKEN"),
        vk_api_version=os.getenv("VK_API_VERSION", "5.199"),
        channels_config_path=Path(os.getenv("CHANNELS_CONFIG_PATH", "config/channels.json")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


def load_channels(config_path: Path) -> list[ChannelConfig]:
    with config_path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    channels = raw_data.get("channels")
    if not isinstance(channels, list):
        raise ValueError("JSON config must contain a 'channels' array")

    result: list[ChannelConfig] = []
    for item in channels:
        if not isinstance(item, dict):
            raise ValueError("Each channel entry must be an object")

        tg_channel = item.get("tg_channel")
        source_title = item.get("source_title")
        vk_peer_id = item.get("vk_peer_id")

        if not isinstance(tg_channel, (str, int)):
            raise ValueError("Channel 'tg_channel' must be a string username or integer ID")
        if not isinstance(source_title, str) or not source_title.strip():
            raise ValueError("Channel 'source_title' must be a non-empty string")
        if not isinstance(vk_peer_id, int):
            raise ValueError("Channel 'vk_peer_id' must be an integer")

        normalized_tg_channel: str | int
        if isinstance(tg_channel, str):
            normalized_tg_channel = tg_channel.strip()
            if not normalized_tg_channel:
                raise ValueError("Channel 'tg_channel' must not be empty")
            if not normalized_tg_channel.startswith("@"):
                normalized_tg_channel = f"@{normalized_tg_channel}"
        else:
            normalized_tg_channel = tg_channel

        result.append(
            ChannelConfig(
                tg_channel=normalized_tg_channel,
                source_title=source_title.strip(),
                vk_peer_id=vk_peer_id,
            )
        )

    if not result:
        raise ValueError("At least one Telegram channel must be configured")

    return result


def _get_env_str(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable {name} is required")
    return value


def _get_env_int(name: str) -> int:
    value = _get_env_str(name)
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"Environment variable {name} must be an integer") from error
