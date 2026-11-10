"""Stufe 1: Themenvorschlaege. Claude legt themen/<JJJJ-MM-TT>-themen.json mit
bis zu drei Themen an; der Betreiber waehlt per Telegram 1, 2, 3 oder keins.
Erst danach schreibt Claude den vollstaendigen Entwurf (Stufe 2, entwuerfe/),
der wie bisher mit Ja/Nein freigegeben wird.

Format:
  {
    "id": "2026-11-11-themen",
    "themen": [
      {"titel": "Nürnberger Christkindlesmarkt öffnet",
       "worum": "ein bis zwei Sätze, worum es geht",
       "quelle": {"name": "Stadt Nürnberg", "url": "https://..."},
       "ernst": false},
      ...
    ]
  }
"""
from __future__ import annotations

from urllib.parse import urlparse

from . import entwurf as E
from .status import jetzt, schluessel

NUMMERN = ["1️⃣", "2️⃣", "3️⃣"]


def pruefen(t: dict) -> list[str]:
    fehler = []
    if not t.get("id") or not E.ID_RE.match(t["id"]):
        fehler.append("id muss 'JJJJ-MM-TT-themen' o. ae. sein")
    liste = t.get("themen")
    if not isinstance(liste, list) or not 1 <= len(liste) <= 3:
        fehler.append("themen: ein bis drei Eintraege")
        return fehler
    for i, th in enumerate(liste, 1):
        if not (th.get("titel") or "").strip():
            fehler.append(f"Thema {i}: titel fehlt")
        if not (th.get("worum") or "").strip():
            fehler.append(f"Thema {i}: worum fehlt")
        q = th.get("quelle") or {}
        u = urlparse(q.get("url") or "")
        if not q.get("name") or u.scheme not in ("http", "https"):
            fehler.append(f"Thema {i}: quelle braucht name und http(s)-url")
        host = u.netloc.lower().split(":")[0]
        if any(host == d or host.endswith("." + d) for d in E.AUSLOESER_DOMAINS):
            fehler.append(f"Thema {i}: {host} ist nur Ausloeser, nie Quelle")
    return fehler


def anfordern(st) -> str:
    """/themen im Telegram-Chat: zusaetzlichen Themenlauf anfordern."""
    offen = [a for a in st.daten.setdefault("anforderungen", [])
             if a.get("status") == "offen" and a.get("art") == "themenlauf"]
    if offen:
        return "⏳ Ist schon angefordert – die Vorschläge kommen mit der nächsten stündlichen Runde (zur Minute :37)."
    st.daten["anforderungen"].append({"art": "themenlauf", "zeit": jetzt(), "status": "offen"})
    return ("👍 Angefordert. Drei neue Themenvorschläge kommen mit der nächsten stündlichen Runde "
            "(zur Minute :37, zwischen 6 und 22 Uhr), meist innerhalb einer guten Stunde.")


def importieren(st, kandidaten, tg, chat_id, veraltet) -> int:
    neu = 0
    for herkunft, pfad, t in kandidaten:
        tid = t.get("id") or pfad
        if tid in st.themen:
            continue
        if t.get("_kaputt"):
            fehler = ["Datei ist kein gueltiges JSON"]
        else:
            fehler = pruefen(t)
        if not fehler and veraltet(tid):
            st.themen[tid] = {"status": "veraltet", "importiert": jetzt()}
            continue
        st.themen[tid] = {"status": "neu" if not fehler else "ungueltig", "key": schluessel(tid),
                          "herkunft": f"{herkunft}:{pfad}", "importiert": jetzt(),
                          "themen": t.get("themen", []), "fehler": fehler}
        if not fehler:
            for a in st.daten.get("anforderungen", []):
                if a.get("status") == "offen" and a.get("art") == "themenlauf":
                    a.update(status="erledigt", themen=tid)
        if fehler:
            if tg and chat_id:
                tg.text(chat_id, f"⚠️ Themenvorschlag abgelehnt (Regelpruefung): {tid}\n\n"
                        + "\n".join(f"• {f}" for f in fehler))
        else:
            neu += 1
    return neu


def senden(st, tg, chat_id) -> int:
    n = 0
    for tid, t in st.themen.items():
        if t.get("status") != "neu":
            continue
        zeilen = [f"🗂️ Themen für den nächsten Post ({tid[8:10]}.{tid[5:7]}.)",
                  "Wähl eins aus – dann schreib ich den Entwurf und schick ihn dir zum Freigeben."]
        for i, th in enumerate(t["themen"]):
            ernst = " (ernste Meldung)" if th.get("ernst") else ""
            zeilen.append(f"{NUMMERN[i]} {th['titel']}{ernst}\n{th['worum']}\n"
                          f"Quelle: {th['quelle']['name']}, {th['quelle']['url']}")
        knoepfe = [[{"text": NUMMERN[i], "callback_data": f"t:{t['key']}:{i + 1}"}
                    for i in range(len(t["themen"]))],
                   [{"text": "❌ Keins davon", "callback_data": f"t:{t['key']}:0"}]]
        msg = tg.text(chat_id, "\n\n".join(zeilen), knoepfe)
        t.update(status="gesendet", gesendet=jetzt(), tg_msg=msg["message_id"])
        n += 1
    return n


def knopf(st, tg, chat_id, cq, key_nr: str) -> int:
    key, _, nr = key_nr.partition(":")
    msg_id = cq.get("message", {}).get("message_id")
    tid = next((i for i, t in st.themen.items() if t.get("key") == key), None)
    if not tid:
        tg.callback_antwort(cq["id"], "Themenvorschlag unbekannt.")
        return 0
    t = st.themen[tid]
    if t.get("status") != "gesendet":
        tg.callback_antwort(cq["id"], f"Schon entschieden: {t.get('status')}")
        tg.knoepfe_weg(chat_id, msg_id)
        return 0
    try:
        n = int(nr)
    except ValueError:
        return 0
    tg.knoepfe_weg(chat_id, msg_id)
    if n == 0:
        t.update(status="verworfen", entschieden=jetzt())
        tg.callback_antwort(cq["id"], "Keins – verworfen.")
        tg.text(chat_id, "❌ Keins davon. Nächste Vorschläge kommen zum nächsten Termin.",
                antwort_auf=msg_id)
        return 1
    if not 1 <= n <= len(t["themen"]):
        return 0
    t.update(status="gewaehlt", gewaehlt=n, entschieden=jetzt())
    tg.callback_antwort(cq["id"], f"Thema {n} gewählt.")
    tg.text(chat_id, f"👍 Thema {n} gewählt: {t['themen'][n - 1]['titel']}\n"
            "Der fertige Entwurf kommt in etwa einer Stunde zum Freigeben.", antwort_auf=msg_id)
    return 1


def entwurf_verknuepfen(st, entwurf: dict, pid: str):
    """Ein Entwurf mit "thema_ref": "<themen-id>#<nr>" erledigt das gewaehlte Thema."""
    ref = entwurf.get("thema_ref") or ""
    tid, _, _ = ref.partition("#")
    t = st.themen.get(tid)
    if t and t.get("status") == "gewaehlt":
        t.update(status="erledigt", entwurf=pid)


def offen(st, veraltet) -> list[dict]:
    """Was Claude jetzt tun muss: angeforderte Themenlaeufe (/themen) und
    gewaehlte Themen, zu denen noch kein Entwurf existiert."""
    anf = [a for a in st.daten.get("anforderungen", []) if a.get("status") == "offen"]
    aus = [{"art": "themenlauf", "angefordert": a["zeit"]}
           for a in anf if a.get("art") == "themenlauf"][:1]
    for a in anf:
        if a.get("art") == "hinweis":
            h = {"art": "hinweis", "hinweis_ref": a["id"], "text": a["text"], "angefordert": a["zeit"]}
            if a.get("bild"):
                h["eigenes_foto"] = str(st.ordner / a["bild"])
                h["bild_feld"] = f"eigen:{a['id']}"
            aus.append(h)
    for tid, t in st.themen.items():
        if t.get("status") == "gewaehlt" and not veraltet(tid):
            n = t["gewaehlt"]
            aus.append({"art": "entwurf", "thema_ref": f"{tid}#{n}", **t["themen"][n - 1]})
    return aus
