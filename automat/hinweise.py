"""Hinweise des Betreibers per Telegram: Stichwoerter oder ein Link, den er
irgendwo aufgeschnappt hat. Claude recherchiert in der naechsten stuendlichen
Runde und legt direkt einen Entwurf an (Feld "hinweis_ref") – oder, wenn es
keine taugliche Primaerquelle gibt, eine Rueckmeldung:

  rueckmeldungen/<JJJJ-MM-TT>-<stichwort>.json
  {"id": "...", "hinweis_ref": "<id>", "text": "kurze Begruendung"}

Der Automat schickt die Rueckmeldung per Telegram und schliesst den Hinweis.
"""
from __future__ import annotations

import io

from PIL import Image, ImageOps

from .status import jetzt, schluessel

MAX_LAENGE = 1000
MAX_KANTE = 2048


def bild_speichern(st, hid: str, daten: bytes) -> str:
    """Speichert ein Foto ohne Metadaten (kein GPS, keine Kameradaten) im Status-Branch."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(daten))).convert("RGB")
    img.thumbnail((MAX_KANTE, MAX_KANTE))
    rel = f"eigene_bilder/{hid}.jpg"
    ziel = st.ordner / rel
    ziel.parent.mkdir(parents=True, exist_ok=True)
    img.save(ziel, "JPEG", quality=92)  # ohne exif=… -> keine Metadaten
    return rel


def eigenes_bild(st, entwurf: dict):
    """Pfad zum eigenen Foto eines Entwurfs ("bild": "eigen:<kennung>") oder None."""
    hid = str(entwurf.get("bild", "")).partition(":")[2]
    pfad = st.ordner / "eigene_bilder" / f"{hid}.jpg"
    return pfad if hid and pfad.is_file() else None


def aufnehmen(st, tg, chat_id: str, text: str, msg_id: int | None = None,
              bild: bytes | None = None):
    text = text.strip()[:MAX_LAENGE]
    hid = schluessel(f"{jetzt()}-{text}-{msg_id}")
    eintrag = {"art": "hinweis", "id": hid, "text": text, "zeit": jetzt(), "status": "offen"}
    if bild is not None:
        eintrag["bild"] = bild_speichern(st, hid, bild)
    st.daten.setdefault("anforderungen", []).append(eintrag)
    zusatz = (" Dein Foto schau ich mir dabei an und nehm es für den Post, wenn es passt."
              if bild is not None else "")
    tg.text(chat_id, "📝 Notiert. Ich recherchiere dazu in der nächsten stündlichen Runde "
            "(zur Minute :37, zwischen 6 und 22 Uhr)." + zusatz + " Finde ich eine Primärquelle, "
            "kommt direkt der fertige Entwurf zum Freigeben – sonst sag ich dir kurz, warum nicht.",
            [[{"text": "❌ Doch nicht", "callback_data": f"h:{hid}"}]], antwort_auf=msg_id)


def _finden(st, hid):
    return next((a for a in st.daten.get("anforderungen", [])
                 if a.get("art") == "hinweis" and a.get("id") == hid), None)


def knopf(st, tg, chat_id, cq, hid: str) -> int:
    a = _finden(st, hid)
    msg_id = cq.get("message", {}).get("message_id")
    tg.knoepfe_weg(chat_id, msg_id)
    if not a or a.get("status") != "offen":
        tg.callback_antwort(cq["id"], "Schon erledigt.")
        return 0
    a.update(status="verworfen", entschieden=jetzt())
    tg.callback_antwort(cq["id"], "Hinweis verworfen.")
    return 1


def entwurf_verknuepfen(st, entwurf: dict, pid: str):
    a = _finden(st, entwurf.get("hinweis_ref") or "")
    if a and a.get("status") == "offen":
        a.update(status="erledigt", entwurf=pid)


def rueckmeldungen(st, kandidaten, tg, chat_id) -> int:
    bekannt = st.daten.setdefault("rueckmeldungen", [])
    n = 0
    for _, pfad, r in kandidaten:
        rid = r.get("id") or pfad
        if rid in bekannt or r.get("_kaputt"):
            continue
        bekannt.append(rid)
        a = _finden(st, r.get("hinweis_ref") or "")
        if not a or a.get("status") != "offen":
            continue
        a.update(status="ohne_entwurf", rueckmeldung=rid)
        tg.text(chat_id, f"🔎 Zu deinem Hinweis „{a['text'][:200]}“:\n\n{(r.get('text') or '').strip()[:3000]}")
        n += 1
    return n
