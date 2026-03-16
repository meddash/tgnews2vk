from __future__ import annotations

import logging
import random
from io import BytesIO
from typing import Any

import requests


class VKService:
    API_URL = "https://api.vk.com/method/"

    def __init__(self, access_token: str, api_version: str) -> None:
        self.access_token = access_token
        self.api_version = api_version
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_message(self, peer_id: int, text: str, photo_bytes: bytes | None = None) -> int:
        attachments: list[str] = []

        if photo_bytes:
            try:
                attachment = self._upload_message_photo(photo_bytes)
                attachments.append(attachment)
            except Exception:
                self.logger.exception("Failed to upload photo to VK, continuing with text only")

        params: dict[str, Any] = {
            "peer_id": peer_id,
            "message": text,
            "random_id": random.randint(1, 2_147_483_647),
        }
        if attachments:
            params["attachments"] = ",".join(attachments)

        response = self._call_api("messages.send", params)
        message_id = int(response)
        self.logger.info("VK message sent successfully: peer_id=%s message_id=%s", peer_id, message_id)
        return message_id

    def _upload_message_photo(self, photo_bytes: bytes) -> str:
        upload_data = self._call_api("photos.getMessagesUploadServer", {})
        upload_url = upload_data["upload_url"]

        files = {"photo": ("telegram_photo.jpg", BytesIO(photo_bytes), "image/jpeg")}
        upload_response = requests.post(upload_url, files=files, timeout=60)
        upload_response.raise_for_status()
        uploaded = upload_response.json()

        saved = self._call_api(
            "photos.saveMessagesPhoto",
            {
                "photo": uploaded["photo"],
                "server": uploaded["server"],
                "hash": uploaded["hash"],
            },
        )

        photo = saved[0]
        return f"photo{photo['owner_id']}_{photo['id']}"

    def _call_api(self, method: str, params: dict[str, Any]) -> Any:
        response = requests.post(
            f"{self.API_URL}{method}",
            data={
                **params,
                "access_token": self.access_token,
                "v": self.api_version,
            },
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        error = data.get("error")
        if error:
            raise RuntimeError(f"VK API error {error.get('error_code')}: {error.get('error_msg')}")

        return data["response"]
