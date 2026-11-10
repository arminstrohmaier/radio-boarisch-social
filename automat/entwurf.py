"""Entwurfsformat, Pruefung nach 06-hoererkommunikation §10 und Caption-Bau.

Ein Entwurf ist eine JSON-Datei entwuerfe/<id>.json mit diesen Feldern:

  id            Kleinbuchstaben, Ziffern, Bindestriche; beginnt mit Datum, z. B.
                "2026-11-12-christkindlmarkt-landshut"
  thema         ein Satz, worum es geht (nur fuer den Betreiber)
  ernst         true bei Todesfaellen und ernsten Meldungen (D-081):
                keine Emojis, kein Dialekt, keine Hashtags
  hook          erste Zeile, traegt das Thema
  text          Tatsachen in eigenen Worten (Kern der Caption)
  aufforderung  kurze Aufforderung am Schluss (bei ernst leer lassen)
  bildtext      kurz, kommt auf das Bild
  bild          Dateiname aus pool/, z. B. "03_text-oben.jpg"
  quelle        {"name": "...", "url": "https://..."}  Primaerquelle
  hashtags      zusaetzliche Hashtags (optional, die festen kommen automatisch)
  recherche     Notiz fuer den Betreiber: Ausloeser, Primaerquelle,
                Quellenregister-Pruefung (wird nicht veroeffentlicht)

Die Caption wird daraus vom Automaten zusammengesetzt, damit Quellenzeile,
Signatur, feste Hashtags und KI-Kennzeichnung nie fehlen.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from . import config

ID_RE = re.compile(r"^20\d\d-\d\d-\d\d-[a-z0-9]+(?:-[a-z0-9]+)*$")
HASHTAG_RE = re.compile(r"^#[0-9A-Za-zÄÖÜäöüß_]+$")
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF\U0000FE0F\U0000200D\U000023E9-\U000023FA]"
)

# 10.3 / 10.4: Nachrichtenagenturen und Sender sind nur Ausloeser, nie Quelle.
AUSLOESER_DOMAINS = ("dpa.de", "dpa.com", "dpa-news.de", "br.de", "antenne.de")

# 06 §6 / §10.3: keine Superlative ueber das eigene Programm, keine Kundendienst-Floskeln.
VERDAECHTIG = [
    r"\bbeste[nrsm]?\b", r"\bgrößte[nrsm]?\b", r"\bnummer\s*(1|eins)\b",
    r"\beinzigartig", r"vielen dank für ihre anfrage", r"ihr anliegen ist uns wichtig",
    r"wir bedauern", r"!{2,}",
]
# 06 §7: keine Zusagen.
ZUSAGEN = [r"\bläuft (bald|demnächst|ab)\b", r"\bin unserer rotation\b",
           r"\bspielen wir (bald|demnächst|ab)\b", r"\bexklusiv\b"]

IG_CAPTION_MAX = 2200
IG_HASHTAG_MAX = 30
BILDTEXT_MAX = 70

PFLICHTFELDER = ["id", "thema", "hook", "text", "bildtext", "bild", "quelle"]


@dataclass
class Pruefung:
    fehler: list[str] = field(default_factory=list)
    hinweise: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.fehler


def laden(pfad: Path) -> dict:
    with open(pfad, encoding="utf-8") as f:
        return json.load(f)


def hashtags(e: dict) -> list[str]:
    if e.get("ernst"):
        return []
    tags = list(config.FESTE_HASHTAGS)
    for t in e.get("hashtags") or []:
        t = t.strip()
        if t and not t.startswith("#"):
            t = "#" + t
        if t and t.lower() not in {x.lower() for x in tags}:
            tags.append(t)
    return tags


def caption(e: dict) -> str:
    """Setzt die Caption nach Raster 10.3 zusammen."""
    q = e["quelle"]
    teile = [e["hook"].strip(), e["text"].strip()]
    if not e.get("ernst") and (e.get("aufforderung") or "").strip():
        teile.append(e["aufforderung"].strip())
    teile.append(f"Quelle: {q['name'].strip()}, {q['url'].strip()}")
    teile.append(config.SIGNATUR)
    tags = hashtags(e)
    if tags:
        teile.append(" ".join(tags))
    if config.POOL_IST_KI:
        teile.append(config.KI_ZEILE)
    return "\n\n".join(teile)


def pruefen(e: dict, zuletzt_genutzte_bilder: list[str] | None = None) -> Pruefung:
    p = Pruefung()
    for f in PFLICHTFELDER:
        if not e.get(f):
            p.fehler.append(f"Pflichtfeld fehlt: {f}")
    if p.fehler:
        return p

    if not ID_RE.match(e["id"]) or len(e["id"]) > 80:
        p.fehler.append("id muss 'JJJJ-MM-TT-stichwort' sein (klein, Bindestriche, max. 80 Zeichen)")

    bild = e["bild"]
    if "/" in bild or not (config.POOL_DIR / bild).is_file():
        p.fehler.append(f"Bild '{bild}' liegt nicht in pool/")

    q = e["quelle"]
    if not isinstance(q, dict) or not q.get("name") or not q.get("url"):
        p.fehler.append("quelle braucht name und url")
    else:
        u = urlparse(q["url"])
        if u.scheme not in ("http", "https") or not u.netloc:
            p.fehler.append("quelle.url ist keine gueltige http(s)-Adresse")
        host = u.netloc.lower().split(":")[0]
        if any(host == d or host.endswith("." + d) for d in AUSLOESER_DOMAINS):
            p.fehler.append(f"{host} ist nur Ausloeser, nie Quelle (10.3) – Primaerquelle suchen")

    bt = e["bildtext"].strip()
    if len(bt) > BILDTEXT_MAX:
        p.fehler.append(f"bildtext zu lang ({len(bt)} > {BILDTEXT_MAX} Zeichen)")
    if EMOJI_RE.search(bt):
        p.fehler.append("bildtext ohne Emojis (wird auf das Bild gesetzt)")

    fliesstext = " ".join([e["hook"], e["text"], e.get("aufforderung") or ""])
    if "quelle:" in fliesstext.lower():
        p.fehler.append("Quellenzeile nicht selbst schreiben – sie wird automatisch angehaengt")
    if "#" in fliesstext:
        p.hinweise.append("Hashtags gehoeren ins Feld 'hashtags', nicht in den Text")

    for t in e.get("hashtags") or []:
        tt = t if t.startswith("#") else "#" + t
        if not HASHTAG_RE.match(tt):
            p.fehler.append(f"ungueltiger Hashtag: {t}")

    if e.get("ernst"):
        if EMOJI_RE.search(fliesstext):
            p.fehler.append("ernste Meldung: keine Emojis (D-081)")
        if e.get("hashtags"):
            p.fehler.append("ernste Meldung: keine Hashtags (D-081)")
        if (e.get("aufforderung") or "").strip():
            p.hinweise.append("ernste Meldung: Aufforderung wird weggelassen")
        for w in ("servus", "grias", "pfiad", "vergelt"):
            if w in fliesstext.lower():
                p.fehler.append(f"ernste Meldung: kein Dialekt ('{w}…')")
    else:
        if not EMOJI_RE.search(fliesstext):
            p.hinweise.append("lebendige Caption: Emojis als Gliederung fehlen (10.3)")
        if not (e.get("aufforderung") or "").strip():
            p.hinweise.append("kurze Aufforderung am Schluss fehlt (10.3)")

    low = fliesstext.lower()
    for muster in VERDAECHTIG:
        if re.search(muster, low):
            p.hinweise.append(f"bitte pruefen (Superlativ/Floskel): /{muster}/")
    for muster in ZUSAGEN:
        if re.search(muster, low):
            p.fehler.append(f"klingt nach Zusage (06 §7): /{muster}/")

    cap = caption(e)
    if len(cap) > IG_CAPTION_MAX:
        p.fehler.append(f"Caption zu lang fuer Instagram ({len(cap)} > {IG_CAPTION_MAX})")
    if len(hashtags(e)) > IG_HASHTAG_MAX:
        p.fehler.append(f"zu viele Hashtags (max. {IG_HASHTAG_MAX})")

    if zuletzt_genutzte_bilder and bild in zuletzt_genutzte_bilder:
        p.fehler.append(f"Bild {bild} wurde in den letzten Posts schon verwendet – anderes waehlen")
    return p
