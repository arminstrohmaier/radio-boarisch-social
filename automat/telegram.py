"""Schlanker Telegram-Bot-API-Client (kostenlos, https://core.telegram.org/bots/api)."""
from __future__ import annotations

from pathlib import Path

import requests


class TelegramFehler(RuntimeError):
    pass


class Telegram:
    def __init__(self, token: str, timeout: int = 30):
        self._basis = f"https://api.telegram.org/bot{token}/"
        self._timeout = timeout

    def _call(self, methode: str, files=None, **params):
        try:
            if files:
                r = requests.post(self._basis + methode, data=params, files=files, timeout=self._timeout)
            else:
                r = requests.post(self._basis + methode, json=params, timeout=self._timeout)
        except requests.RequestException as ex:  # Token nie in Fehlermeldungen
            raise TelegramFehler(f"{methode}: Netzwerkfehler {type(ex).__name__}") from None
        try:
            daten = r.json()
        except ValueError:
            raise TelegramFehler(f"{methode}: HTTP {r.status_code}") from None
        if not daten.get("ok"):
            raise TelegramFehler(f"{methode}: {daten.get('description', r.status_code)}")
        return daten["result"]

    def updates(self, offset: int | None):
        p = {"timeout": 0, "allowed_updates": ["message", "callback_query"]}
        if offset is not None:
            p["offset"] = offset
        return self._call("getUpdates", **p)

    def foto(self, chat_id: str, pfad: Path, caption: str = "") -> dict:
        with open(pfad, "rb") as f:
            return self._call("sendPhoto", files={"photo": (pfad.name, f, "image/jpeg")},
                              chat_id=chat_id, caption=caption[:1024])

    def text(self, chat_id: str, text: str, knoepfe: list[list[dict]] | None = None,
             antwort_auf: int | None = None) -> dict:
        p = {"chat_id": chat_id, "text": text[:4096], "disable_web_page_preview": True}
        if knoepfe:
            p["reply_markup"] = {"inline_keyboard": knoepfe}
        if antwort_auf:
            p["reply_parameters"] = {"message_id": antwort_auf, "allow_sending_without_reply": True}
        return self._call("sendMessage", **p)

    def knoepfe_weg(self, chat_id: str, message_id: int):
        try:
            self._call("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id,
                       reply_markup={"inline_keyboard": []})
        except TelegramFehler:
            pass  # z. B. schon entfernt

    def callback_antwort(self, callback_id: str, text: str = ""):
        try:
            self._call("answerCallbackQuery", callback_query_id=callback_id, text=text[:200])
        except TelegramFehler:
            pass  # Callback zu alt (>15 min) – unkritisch
