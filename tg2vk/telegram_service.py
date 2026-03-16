from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

from telethon import TelegramClient, events
from telethon.tl.custom import Message
from telethon.utils import get_peer_id

from tg2vk.config import ChannelConfig


@dataclass(frozen=True)
class IncomingPost:
    channel_id: int
    channel_title: str
    vk_peer_id: int
    text: str
    photo_bytes: bytes | None
    has_unsupported_video: bool


PostHandler = Callable[[IncomingPost], Awaitable[None]]


class TelegramService:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session: str,
        channels: list[ChannelConfig],
        post_handler: PostHandler,
    ) -> None:
        self.client = TelegramClient(session, api_id, api_hash)
        self.channels = channels
        self.post_handler = post_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.channel_titles: dict[int, str] = {}
        self.channel_peer_ids: dict[int, int] = {}

    async def run(self) -> None:
        self.logger.info("Starting Telegram client")
        await self.client.start()
        await self._register_handlers()
        self.logger.info("Connected to Telegram successfully")
        await self.client.run_until_disconnected()

    async def _register_handlers(self) -> None:
        channel_inputs = []
        for channel in self.channels:
            entity = await self.client.get_entity(channel.tg_channel)
            channel_inputs.append(await self.client.get_input_entity(channel.tg_channel))
            peer_id = get_peer_id(entity)
            self.channel_titles[peer_id] = channel.source_title
            self.channel_peer_ids[peer_id] = channel.vk_peer_id

        @self.client.on(events.NewMessage(chats=channel_inputs))
        async def on_new_message(event: events.NewMessage.Event) -> None:
            await self._handle_event(event.message)

    async def _handle_event(self, message: Message) -> None:
        channel_id = getattr(message.peer_id, "channel_id", None)
        if channel_id is None:
            self.logger.warning("Skipped message because channel_id could not be determined")
            return

        full_channel_id = self._normalize_channel_id(channel_id)
        channel_title = self.channel_titles.get(full_channel_id, f"Telegram channel {full_channel_id}")
        vk_peer_id = self.channel_peer_ids.get(full_channel_id)
        if vk_peer_id is None:
            self.logger.warning("VK peer_id was not found for Telegram channel %s", full_channel_id)
            return
        text = message.message or ""

        photo_bytes = None
        if message.photo:
            try:
                # Telethon returns raw bytes when file=bytes is passed.
                photo_bytes = await message.download_media(file=bytes)
            except Exception:
                self.logger.exception("Failed to download photo from Telegram message")
        elif message.file and (message.file.mime_type or "").startswith("image/"):
            try:
                # Some Telegram channels send images as documents instead of photo objects.
                photo_bytes = await message.download_media(file=bytes)
            except Exception:
                self.logger.exception("Failed to download image document from Telegram message")

        has_unsupported_video = False
        if message.video or (message.file and (message.file.mime_type or "").startswith("video/")):
            has_unsupported_video = True
            self.logger.info(
                "Video attachment detected in Telegram channel %s, but VK video forwarding is not implemented yet",
                full_channel_id,
            )

        incoming_post = IncomingPost(
            channel_id=full_channel_id,
            channel_title=channel_title,
            vk_peer_id=vk_peer_id,
            text=text,
            photo_bytes=photo_bytes,
            has_unsupported_video=has_unsupported_video,
        )

        try:
            await self.post_handler(incoming_post)
        except Exception:
            self.logger.exception("Failed to process Telegram message from channel %s", full_channel_id)

    @staticmethod
    def _normalize_channel_id(channel_id: int) -> int:
        if str(channel_id).startswith("-100"):
            return channel_id
        return int(f"-100{channel_id}")
