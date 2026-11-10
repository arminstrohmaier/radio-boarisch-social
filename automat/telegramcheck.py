"""Diagnose der Telegram-Verbindung (Ergebnis per Telegram, nichts wird veroeffentlicht).

Prueft, ob ein Webhook gesetzt ist (dann bekommt der Automat keine Knopfdruecke) und
wie viele Nachrichten bei Telegram auf Abholung warten.
"""
import sys
from datetime import datetime, timezone

from .config import Settings
from .telegram import Telegram, TelegramFehler


def main() -> int:
    s = Settings.from_env()
    if not s.telegram_token:
        print("::warning::TELEGRAM_BOT_TOKEN fehlt")
        return 1
    tg = Telegram(s.telegram_token)
    try:
        me = tg.ich()
        w = tg.webhook_info()
    except TelegramFehler as ex:
        print(f"::error::{ex}")
        return 1
    z = [f"🤖 Bot: @{me.get('username')}"]
    if w.get("url"):
        z.append("❌ Es ist ein Webhook gesetzt – ein anderes Programm empfängt die Knopfdrücke. "
                 "Der Automat bekommt dann nichts.")
    else:
        z.append("✅ Kein Webhook gesetzt.")
    z.append(f"ℹ️ Wartende Nachrichten bei Telegram: {w.get('pending_update_count', 0)}")
    if w.get("last_error_date"):
        t = datetime.fromtimestamp(w["last_error_date"], timezone.utc)
        z.append(f"⚠️ Letzter Webhook-Fehler {t:%d.%m. %H:%M} UTC: {w.get('last_error_message')}")
    text = "🔧 Telegram-Diagnose\n\n" + "\n".join(z)
    print("Webhook gesetzt:", bool(w.get("url")), "| wartend:", w.get("pending_update_count", 0))
    if s.telegram_chat_id:
        tg.text(s.telegram_chat_id, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
