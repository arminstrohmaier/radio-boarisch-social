"""Ein Durchlauf des Automaten (laeuft alle 10 Minuten in GitHub Actions).

  1. Import    neue Entwuerfe (entwuerfe/*.json auf allen Branches) uebernehmen
  2. Senden    Bild rendern, per Telegram mit Ja/Nein-Knopf an den Betreiber
  3. Antworten Telegram-Knoepfe auswerten: Ja -> freigegeben, Nein -> verworfen
  4. Posten    Freigegebene ueber die Meta Graph API veroeffentlichen

Ohne Antwort bleibt ein Entwurf liegen; es passiert nichts.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from . import config, entwurf as E, render, themen
from .config import Settings
from .meta import Meta, MetaFehler
from .status import ABGESCHLOSSEN, Status, git_commit, inhalt_hash, jetzt, schluessel
from .telegram import Telegram, TelegramFehler

KANAL_NAME = {"instagram": "Instagram", "facebook": "Facebook"}


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- Import

def entwuerfe_finden(repo: Path, ordner: str = "entwuerfe") -> list[tuple[str, str, dict]]:
    """-> [(herkunft, dateiname, inhalt)] aus allen Remote-Branches und dem Arbeitsordner."""
    gefunden = []

    def git(*a):
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)

    refs = git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").stdout.split()
    for ref in refs:
        if ref in ("origin/HEAD", "origin/redaktion", "origin"):
            continue
        for pfad in git("ls-tree", "--name-only", ref, f"{ordner}/").stdout.split():
            if not pfad.endswith(".json"):
                continue
            r = git("show", f"{ref}:{pfad}")
            try:
                gefunden.append((ref.removeprefix("origin/"), pfad, json.loads(r.stdout)))
            except ValueError:
                gefunden.append((ref.removeprefix("origin/"), pfad, {"_kaputt": True}))
    lokal = repo / ordner
    if lokal.is_dir():
        for f in sorted(lokal.glob("*.json")):
            try:
                gefunden.append(("arbeitsordner", f"{ordner}/{f.name}", E.laden(f)))
            except ValueError:
                gefunden.append(("arbeitsordner", f"{ordner}/{f.name}", {"_kaputt": True}))
    return gefunden


MAX_ALTER_TAGE = 4


def _veraltet(pid: str, heute: date | None = None) -> bool:
    """Entwuerfe, deren Datum (Anfang der id) mehr als MAX_ALTER_TAGE zurueckliegt,
    werden nicht mehr gesendet – sonst kaeme nach einer Pause ein Stapel alter Posts."""
    try:
        d = date.fromisoformat(pid[:10])
    except ValueError:
        return False
    return (heute or date.today()) - d > timedelta(days=MAX_ALTER_TAGE)


def importieren(st: Status, kandidaten, tg: Telegram | None, chat_id: str) -> int:
    neu = 0
    for herkunft, pfad, e in kandidaten:
        pid = e.get("id") or Path(pfad).stem
        if e.get("_kaputt"):
            pid = Path(pfad).stem
        bekannt = st.posts.get(pid)
        h = inhalt_hash(e)
        if bekannt and not (bekannt.get("status") == "ungueltig" and bekannt.get("hash") != h):
            continue  # bekannt -> nie neu senden (das Ja gilt fuer genau die gezeigte Fassung)
        if not bekannt and _veraltet(pid):
            st.posts[pid] = {"status": "veraltet", "key": schluessel(pid), "hash": h,
                             "herkunft": f"{herkunft}:{pfad}", "importiert": jetzt()}
            log(f"veraltet, nicht gesendet: {pid}")
            continue
        if e.get("_kaputt"):
            p = E.Pruefung(fehler=["Datei ist kein gueltiges JSON"])
        else:
            p = E.pruefen(e, st.zuletzt_genutzte_bilder(ausser=pid))
        eintrag = {"status": "neu" if p.ok else "ungueltig", "key": schluessel(pid), "hash": h,
                   "herkunft": f"{herkunft}:{pfad}", "importiert": jetzt(),
                   "bild": e.get("bild"), "thema": e.get("thema", ""),
                   "hinweise": p.hinweise, "fehler": p.fehler}
        st.posts[pid] = eintrag
        if p.ok:
            ordner = st.post_ordner(pid)
            ordner.mkdir(parents=True, exist_ok=True)
            (ordner / "entwurf.json").write_text(json.dumps(e, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8")
            themen.entwurf_verknuepfen(st, e, pid)
            neu += 1
            log(f"importiert: {pid}")
        else:
            log(f"UNGUELTIG: {pid}: {p.fehler}")
            if tg and chat_id:
                tg.text(chat_id, "⚠️ Entwurf abgelehnt (Regelpruefung), nichts gesendet:\n"
                        f"{pid}\n\n" + "\n".join(f"• {f}" for f in p.fehler))
    return neu


# ---------------------------------------------------------------- Senden

def vorschau_text(e: dict, cap: str, hinweise: list[str], test: bool) -> str:
    kopf = "🧪 TEST – bei Ja wird NICHTS veröffentlicht\n\n" if test else ""
    teile = [f"{kopf}📝 Neuer Entwurf: {e.get('thema', e['id'])}",
             "────────────", cap, "────────────"]
    if e.get("recherche"):
        teile.append(f"🔎 Recherche: {e['recherche']}")
    if hinweise:
        teile.append("Hinweise der Prüfung:\n" + "\n".join(f"• {h}" for h in hinweise))
    teile.append("Veröffentlichen auf Instagram und Facebook?")
    return "\n\n".join(teile)


def senden(st: Status, tg: Telegram, chat_id: str) -> int:
    n = 0
    for pid, p in sorted(st.posts.items(), key=lambda kv: kv[1].get("importiert", "")):
        if p.get("status") != "neu":
            continue
        e = st.entwurf(pid)
        bild = render.rendern(e["bild"], e["bildtext"], st.bild(pid))
        cap = E.caption(e)
        foto = tg.foto(chat_id, bild, caption=f"Entwurf {pid}")
        knoepfe = [[{"text": "✅ Ja, veröffentlichen", "callback_data": f"ja:{p['key']}"},
                    {"text": "❌ Nein, verwerfen", "callback_data": f"nein:{p['key']}"}]]
        msg = tg.text(chat_id, vorschau_text(e, cap, p.get("hinweise", []), p.get("test", False)),
                      knoepfe, antwort_auf=foto["message_id"])
        p.update(status="gesendet", gesendet=jetzt(), tg_foto=foto["message_id"],
                 tg_msg=msg["message_id"])
        n += 1
        log(f"gesendet: {pid}")
    return n


# ---------------------------------------------------------------- Antworten

def antworten(st: Status, tg: Telegram, chat_id: str) -> int:
    updates = tg.updates(_offset(st))
    n = 0
    for u in updates:
        st.daten["telegram_offset"] = u["update_id"] + 1
        if "callback_query" in u:
            n += _knopf(st, tg, chat_id, u["callback_query"])
        elif "message" in u:
            _nachricht(st, tg, chat_id, u["message"])
    return n


def _offset(st: Status):
    return st.daten.get("telegram_offset")


def _knopf(st: Status, tg: Telegram, chat_id: str, cq: dict) -> int:
    absender = str(cq.get("from", {}).get("id", ""))
    chat = str(cq.get("message", {}).get("chat", {}).get("id", ""))
    if not chat_id or (chat != chat_id and absender != chat_id):
        tg.callback_antwort(cq["id"], "Nicht berechtigt.")
        log(f"Knopf von fremdem Chat ignoriert")
        return 0
    aktion, _, key = (cq.get("data") or "").partition(":")
    if aktion == "t":
        return themen.knopf(st, tg, chat_id, cq, key)
    pid = st.nach_schluessel(key)
    msg_id = cq.get("message", {}).get("message_id")
    if not pid:
        tg.callback_antwort(cq["id"], "Entwurf unbekannt.")
        return 0
    p = st.posts[pid]
    if aktion in ("ja", "nein") and p.get("status") != "gesendet":
        tg.callback_antwort(cq["id"], f"Schon entschieden: {p.get('status')}")
        if msg_id:
            tg.knoepfe_weg(chat_id, msg_id)
        return 0
    if aktion == "ja":
        p.update(status="freigegeben", entschieden=jetzt())
        tg.callback_antwort(cq["id"], "Freigegeben – wird veröffentlicht.")
        tg.knoepfe_weg(chat_id, msg_id)
        tg.text(chat_id, "✅ Freigegeben. Wird jetzt veröffentlicht …", antwort_auf=msg_id)
        log(f"freigegeben: {pid}")
        return 1
    if aktion == "nein":
        p.update(status="verworfen", entschieden=jetzt())
        tg.callback_antwort(cq["id"], "Verworfen.")
        tg.knoepfe_weg(chat_id, msg_id)
        tg.text(chat_id, "❌ Verworfen. Es wird nichts veröffentlicht.", antwort_auf=msg_id)
        log(f"verworfen: {pid}")
        return 1
    if aktion == "nochmal" and p.get("status") in ("fehler", "teilweise"):
        for k in p.get("kanaele", {}).values():
            if k.get("status") != "ok":
                k["status"] = "offen"
        p["status"] = "freigegeben"
        tg.callback_antwort(cq["id"], "Neuer Versuch …")
        tg.knoepfe_weg(chat_id, msg_id)
        log(f"neuer Versuch: {pid}")
        return 1
    tg.callback_antwort(cq["id"])
    return 0


def _nachricht(st: Status, tg: Telegram, chat_id: str, m: dict):
    text = (m.get("text") or "").strip().lower()
    chat = str(m.get("chat", {}).get("id", ""))
    if m.get("chat", {}).get("type") != "private":
        return
    if not chat_id:
        if text.startswith("/start") or text.startswith("/id"):
            tg.text(chat, f"Servus! Deine Chat-ID ist:\n\n{chat}\n\nTrag sie als GitHub-Secret "
                          "TELEGRAM_CHAT_ID ein (siehe docs/EINRICHTUNG.md, Schritt 3).")
        return
    if chat != chat_id:
        return  # fremde Chats ignorieren
    if text.startswith("/status"):
        offen = [f"• {pid}: {p.get('status')}" for pid, p in st.posts.items()
                 if p.get("status") not in ABGESCHLOSSEN and p.get("status") != "ungueltig"]
        offen += [f"• Themen {tid}: {t.get('status')}" for tid, t in st.themen.items()
                  if t.get("status") in ("neu", "gesendet", "gewaehlt")]
        tg.text(chat_id, "Offen:\n" + ("\n".join(offen) if offen else "nichts"))
    elif text.startswith("/start") or text.startswith("/id"):
        tg.text(chat_id, "Servus! Der Automat ist eingerichtet. Entwürfe kommen hier mit "
                         "Ja/Nein-Knopf an. /status zeigt offene Entwürfe.")


# ---------------------------------------------------------------- Posten

def posten(st: Status, s: Settings, tg: Telegram, meta: Meta | None, commit) -> int:
    n = 0
    for pid, p in st.posts.items():
        if p.get("status") != "freigegeben":
            continue
        n += 1
        if p.get("test"):
            p["status"] = "test_ok"
            tg.text(s.telegram_chat_id, "🧪 Test erfolgreich: Ja-Knopf kam an. Es wurde nichts "
                    "veröffentlicht.", antwort_auf=p.get("tg_msg"))
            continue
        if meta is None:
            p["status"] = "freigegeben_manuell"
            tg.text(s.telegram_chat_id, "ℹ️ Der Meta-Zugang ist noch nicht eingerichtet. Bitte "
                    "von Hand posten: Bild und Text stehen oben.", antwort_auf=p.get("tg_msg"))
            continue
        e = st.entwurf(pid)
        cap = E.caption(e)
        url = f"{s.public_base_url}/posts/{pid}/bild.jpg"
        kanaele = p.setdefault("kanaele", {})
        ziele = []
        if s.meta_ig_user_id:
            ziele.append(("instagram", lambda: meta.instagram(s.meta_ig_user_id, url, cap)))
        if s.meta_page_id:
            ziele.append(("facebook", lambda: meta.facebook(s.meta_page_id, url, cap)))
        for name, aufruf in ziele:
            k = kanaele.setdefault(name, {"status": "offen", "versuche": 0})
            if k["status"] == "ok":
                continue
            if k["status"] == "laeuft":
                # voriger Lauf brach mitten im Veroeffentlichen ab -> nicht blind wiederholen
                k.update(status="fehler", fehler="Abbruch waehrend des Postens – bitte auf "
                         f"{KANAL_NAME[name]} pruefen, ob der Post schon online ist")
                continue
            k["status"] = "laeuft"
            k["versuche"] = k.get("versuche", 0) + 1
            st.speichern()
            commit(f"{pid}: {name} wird veroeffentlicht")
            try:
                k.update(status="ok", **aufruf(), zeit=jetzt())
                k.pop("fehler", None)
                log(f"{name} ok: {pid}")
            except MetaFehler as ex:
                k.update(status="fehler", fehler=str(ex))
                log(f"{name} FEHLER: {pid}: {ex}")
            st.speichern()
            commit(f"{pid}: {name} {k['status']}")
        oks = [n_ for n_, k in kanaele.items() if k["status"] == "ok"]
        p["status"] = ("veroeffentlicht" if len(oks) == len(ziele)
                       else "teilweise" if oks else "fehler")
        zeilen = []
        for name, _ in ziele:
            k = kanaele[name]
            if k["status"] == "ok":
                zeilen.append(f"✅ {KANAL_NAME[name]}: {k.get('link') or k.get('id')}")
            else:
                zeilen.append(f"⚠️ {KANAL_NAME[name]}: {k.get('fehler')}")
        knoepfe = None
        if p["status"] != "veroeffentlicht":
            knoepfe = [[{"text": "🔁 Nochmal versuchen", "callback_data": f"nochmal:{p['key']}"}]]
        kopf = "📣 Veröffentlicht" if p["status"] == "veroeffentlicht" else "⚠️ Nicht vollständig veröffentlicht"
        tg.text(s.telegram_chat_id, kopf + "\n\n" + "\n".join(zeilen), knoepfe, antwort_auf=p.get("tg_msg"))
    return n


# ---------------------------------------------------------------- Testentwurf

def testentwurf(st: Status) -> str:
    bild = random.choice(sorted(f.name for f in config.POOL_DIR.glob("*.jpg")))
    pid = f"{jetzt()[:10]}-test-{jetzt()[11:19].replace(':', '')}"
    e = {
        "id": pid, "thema": "Testlauf der Telegram-Verbindung", "ernst": False,
        "hook": "🧪 Servus! Des is a Testpost vom Automaten.",
        "text": "📻 Wenn du des liest, kommt der Entwurf sauber per Telegram an.",
        "aufforderung": "👉 Drück auf Ja oder Nein – veröffentlicht wird beim Test nix.",
        "bildtext": "Testlauf Automat", "bild": bild,
        "quelle": {"name": "Radio Boarisch", "url": "https://radio-boarisch.de"},
        "recherche": "Test, keine Recherche.",
    }
    ordner = st.post_ordner(pid)
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "entwurf.json").write_text(json.dumps(e, indent=2, ensure_ascii=False), encoding="utf-8")
    st.posts[pid] = {"status": "neu", "key": schluessel(pid), "hash": inhalt_hash(e), "test": True,
                     "herkunft": "testentwurf", "importiert": jetzt(), "bild": bild,
                     "thema": e["thema"], "hinweise": [], "fehler": []}
    return pid


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", default="redaktion", help="Ordner des Status-Checkouts")
    ap.add_argument("--repo", default=str(config.REPO_ROOT))
    ap.add_argument("--commit", action="store_true", help="Status committen und pushen")
    ap.add_argument("--testentwurf", action="store_true")
    a = ap.parse_args(argv)

    s = Settings.from_env()
    st = Status(Path(a.status))
    commit = (lambda msg: git_commit(st.ordner, msg)) if a.commit else (lambda msg: None)

    if not s.telegram_ok:
        log("::warning::TELEGRAM_BOT_TOKEN fehlt – siehe docs/EINRICHTUNG.md. Nichts zu tun.")
        return 0
    tg = Telegram(s.telegram_token)
    meta = Meta(s.meta_token, s.meta_api_version) if s.meta_ok else None
    chat = s.telegram_chat_id

    try:
        if chat:
            if a.testentwurf:
                log(f"Testentwurf: {testentwurf(st)}")
            themen.importieren(st, entwuerfe_finden(Path(a.repo), "themen"), tg, chat, _veraltet)
            importieren(st, entwuerfe_finden(Path(a.repo)), tg, chat)
            st.speichern(); commit("Import")
            themen.senden(st, tg, chat)
            senden(st, tg, chat)
            st.speichern(); commit("Entwuerfe gesendet")
        else:
            log("::warning::TELEGRAM_CHAT_ID fehlt – schreib dem Bot /start, er antwortet mit der ID.")
        antworten(st, tg, chat)
        st.speichern(); commit("Telegram-Antworten")
        if chat:
            tg.updates(_offset(st))  # bestaetigt verarbeitete Updates bei Telegram
            posten(st, s, tg, meta, commit)
            st.speichern(); commit("Veroeffentlichung")
    except TelegramFehler as ex:
        st.speichern(); commit("Zwischenstand nach Telegram-Fehler")
        log(f"::error::Telegram: {ex}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
