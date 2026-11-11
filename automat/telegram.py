"""Schlanker Telegram-Bot-API-Client (kostenlos, https://core.telegram.org/bots/api)."""
from __future__ import annotations

from pathlib import Path

import requests


class TelegramFehler(RuntimeError):
    pass


class Telegram:
    def __init__(self, token: str, timeout: int = 30):
        self._basis = f"https://api.telegram.org/bot{token}/"
        self._datei_basis = f"https://api.telegram.org/file/bot{token}/"
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

    def updates(self, offset: int | None, warten: int = 0):
        """warten > 0: Long-Polling – Telegram antwortet sofort, sobald etwas kommt."""
        p = {"timeout": warten, "allowed_updates": ["message", "callback_query"]}
        if offset is not None:
            p["offset"] = offset
        alt = self._timeout
        self._timeout = max(alt, warten + 15)
        try:
            return self._call("getUpdates", **p)
        finally:
            self._timeout = alt

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

    def datei(self, file_id: str) -> bytes:
        """Laedt eine Datei (z. B. ein Foto) herunter, die dem Bot geschickt wurde."""
        pfad = self._call("getFile", file_id=file_id)["file_path"]
        try:
            r = requests.get(self._datei_basis + pfad, timeout=self._timeout)
        except requests.RequestException as ex:
            raise TelegramFehler(f"Download: Netzwerkfehler {type(ex).__name__}") from None
        if r.status_code != 200:
            raise TelegramFehler(f"Download: HTTP {r.status_code}")
        return r.content

    def webhook_info(self) -> dict:
        return self._call("getWebhookInfo")

    def ich(self) -> dict:
        return self._call("getMe")

    def befehle(self, liste: list[tuple[str, str]]):
        """Befehlsmenue im Telegram-Chat (Knopf "Menü" neben dem Eingabefeld)."""
        self._call("setMyCommands", commands=[{"command": c, "description": d} for c, d in liste])

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
