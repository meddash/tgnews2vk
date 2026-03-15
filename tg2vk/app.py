from __future__ import annotations

import asyncio
import logging

from tg2vk.config import AppConfig, load_channels, load_config
from tg2vk.logging_config import setup_logging
from tg2vk.telegram_service import IncomingPost, TelegramService
from tg2vk.vk_service import VKService


class RepostApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.channels = load_channels(config.channels_config_path)
        self.vk_service = VKService(
            access_token=config.vk_access_token,
            api_version=config.vk_api_version,
        )
        self.telegram_service = TelegramService(
            api_id=config.tg_api_id,
            api_hash=config.tg_api_hash,
            session=config.tg_session,
            channels=self.channels,
            post_handler=self.handle_post,
        )

    async def start(self) -> None:
        self.logger.info("Service started")
        self.logger.info("Watching %s Telegram channel(s)", len(self.channels))
        await self.telegram_service.run()

    async def handle_post(self, post: IncomingPost) -> None:
        if not post.text and not post.photo_bytes:
            self.logger.info("Skipped empty Telegram post from %s", post.channel_title)
            return

        if not post.text and post.photo_bytes:
            self.logger.info("Processing media-only Telegram post from %s", post.channel_title)

        vk_text = self._build_vk_text(post.channel_title, post.text)
        await asyncio.to_thread(
            self.vk_service.send_message,
            post.vk_peer_id,
            vk_text,
            post.photo_bytes,
        )
        self.logger.info(
            "Telegram post from '%s' was sent to VK chat %s",
            post.channel_title,
            post.vk_peer_id,
        )

    @staticmethod
    def _build_vk_text(channel_title: str, message_text: str) -> str:
        source = f"[Источник: {channel_title}]"
        if not message_text.strip():
            return source
        return f"{source}\n\n{message_text.strip()}"


def run() -> None:
    config = load_config()
    setup_logging(config.log_level)
    app = RepostApp(config)
    asyncio.run(app.start())
