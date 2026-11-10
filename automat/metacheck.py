"""Prueft den Meta-Zugang, ohne etwas zu veroeffentlichen.

Das Ergebnis geht per Telegram an den Betreiber (nicht ins oeffentliche
Actions-Protokoll). Der Token selbst wird nie ausgegeben.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from .config import Settings
from .meta import Meta, MetaFehler
from .telegram import Telegram

NOETIG_IG = {"instagram_basic", "instagram_content_publish"}
NOETIG_FB = {"pages_manage_posts", "pages_read_engagement", "pages_show_list"}


def pruefen(s: Settings, meta: Meta) -> tuple[bool, list[str]]:
    z, ok = [], True

    def gut(t): z.append(f"✅ {t}")

    def schlecht(t):
        nonlocal ok
        ok = False
        z.append(f"❌ {t}")

    if not s.meta_token:
        schlecht("Secret META_PAGE_TOKEN fehlt")
        return ok, z
    try:
        d = meta._req("GET", "debug_token", input_token=s.meta_token).get("data", {})
    except MetaFehler as ex:
        schlecht(f"Token wird von Meta nicht akzeptiert: {ex}")
        return ok, z
    if not d.get("is_valid"):
        schlecht(f"Token ungültig: {d.get('error', {}).get('message', 'unbekannt')}")
        return ok, z
    typ = d.get("type", "?")
    gut(f"Token gültig, Typ: {typ}" + (" (Seiten-Token)" if typ == "PAGE" else ""))
    ablauf = d.get("expires_at")
    if not ablauf:
        gut("Läuft ab: nie")
    else:
        dt = datetime.fromtimestamp(ablauf, timezone.utc)
        tage = (dt - datetime.now(timezone.utc)).days
        schlecht(f"Läuft ab am {dt:%d.%m.%Y} (in {tage} Tagen) – Seiten-Token nach B2 Schritt 5–6 erzeugen")
    dz = d.get("data_access_expires_at")
    if dz:
        dt = datetime.fromtimestamp(dz, timezone.utc)
        z.append(f"ℹ️ Datenzugriff gilt bis {dt:%d.%m.%Y} – wird durch regelmäßiges Posten verlängert")
    rechte = set(d.get("scopes", []))
    fehlt = sorted((NOETIG_IG | NOETIG_FB) - rechte)
    if fehlt:
        schlecht("Berechtigungen fehlen: " + ", ".join(fehlt))
    else:
        gut("Alle Berechtigungen vorhanden")

    if s.meta_page_id:
        try:
            p = meta._req("GET", s.meta_page_id, fields="name,instagram_business_account")
            gut(f"Facebook-Seite: {p.get('name')}")
            verkn = (p.get("instagram_business_account") or {}).get("id")
            if s.meta_ig_user_id and verkn and verkn != s.meta_ig_user_id:
                schlecht("META_IG_USER_ID passt nicht zum Instagram-Konto dieser Seite")
            elif not verkn:
                schlecht("Mit der Seite ist kein Instagram-Professional-Konto verknüpft (B0)")
        except MetaFehler as ex:
            schlecht(f"Seite nicht abrufbar (META_PAGE_ID?): {ex}")
        if typ != "PAGE":
            try:
                meta.seiten_token(s.meta_page_id)
                gut("Seiten-Token lässt sich aus diesem Token ableiten – Facebook-Posten geht")
            except MetaFehler as ex:
                schlecht(f"Kein Seiten-Token ableitbar: {ex}")
    else:
        z.append("ℹ️ META_PAGE_ID fehlt – es wird nicht auf Facebook gepostet")

    if s.meta_ig_user_id:
        try:
            ig = meta._req("GET", s.meta_ig_user_id, fields="username")
            gut(f"Instagram-Konto: @{ig.get('username')}")
        except MetaFehler as ex:
            schlecht(f"Instagram-Konto nicht abrufbar (META_IG_USER_ID?): {ex}")
        try:
            lim = meta._req("GET", f"{s.meta_ig_user_id}/content_publishing_limit",
                            fields="quota_usage,config").get("data", [{}])[0]
            gut(f"Instagram-Posten erlaubt (heute genutzt: {lim.get('quota_usage', 0)} "
                f"von {lim.get('config', {}).get('quota_total', '?')})")
        except MetaFehler as ex:
            schlecht(f"Instagram-Posten nicht erlaubt: {ex}")
    else:
        z.append("ℹ️ META_IG_USER_ID fehlt – es wird nicht auf Instagram gepostet")
    return ok, z


def main() -> int:
    s = Settings.from_env()
    ok, zeilen = pruefen(s, Meta(s.meta_token, s.meta_api_version))
    text = ("🔑 Meta-Prüfung: alles bereit" if ok else "🔑 Meta-Prüfung: es fehlt noch etwas") \
        + "\n\n" + "\n".join(zeilen) + "\n\nEs wurde nichts veröffentlicht."
    if s.telegram_token and s.telegram_chat_id:
        Telegram(s.telegram_token).text(s.telegram_chat_id, text)
        print("Ergebnis per Telegram geschickt:", "OK" if ok else "NICHT OK")
    else:
        print("::warning::Telegram nicht eingerichtet – Ergebnis nur kurz:", "OK" if ok else "NICHT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
