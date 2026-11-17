"""Setzt den Bildtext und das Radio-Boarisch-Logo auf das Bild (06 §10.3).

Der Dateiname nennt die freie Textflaeche, z. B. 03_text-oben.jpg,
11_text-linksunten.jpg, 15_text-obenlinks.jpg. Ausgabe: 1080x1350 JPEG (4:5).
"""
from __future__ import annotations

import re
from pathlib import Path

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

from . import config

ZIEL = (1080, 1350)
RAND = 72
LOGO_BREITE = 500      # px bei 1080 Breite (das Logo ist ein breites Querformat, ca. 3:1)
LOGO_RAND = 40
LOGO_DECKKRAFT = 0.92


def textflaeche(dateiname: str) -> tuple[str, str]:
    """-> (vertikal, horizontal) mit vertikal in oben/mitte/unten,
    horizontal in links/mitte/rechts."""
    m = re.search(r"text-([a-z]+)", dateiname)
    lage = m.group(1) if m else "unten"
    v = "oben" if "oben" in lage else "unten" if "unten" in lage else "mitte"
    h = "links" if "links" in lage else "rechts" if "rechts" in lage else "mitte"
    return v, h


def _woerter(text: str) -> list[str]:
    """Trennt an Leerzeichen; ein Datum wie "27. November" bleibt zusammen."""
    woerter = []
    for w in re.split(r"[ \t\n]+", text.strip()):
        if woerter and re.fullmatch(r"\d{1,2}\.", woerter[-1]):
            woerter[-1] += "\u00a0" + w
        elif woerter and w in ("–", "-", "—"):
            woerter[-1] += "\u00a0" + w   # Gedankenstrich nie allein am Zeilenanfang
        elif w:
            woerter.append(w)
    return woerter


def teilen(bildtext: str) -> tuple[str, str]:
    """Hauptzeile und Zusatzzeile: getrennt am ersten " – ", " · " oder " | "."""
    teile = re.split(r"\s+[–·|]\s+", bildtext.strip(), maxsplit=1)
    return teile[0].strip(), (teile[1].strip() if len(teile) > 1 else "")


@lru_cache(maxsize=64)
def _font_cache(pfad: str, groesse: int):
    return ImageFont.truetype(pfad, groesse)


def _font(pfad: Path, groesse: int):
    if not Path(pfad).is_file():
        pfad = config.FONT_PATH
    return _font_cache(str(pfad), groesse)


def _zeilenhoehe(font) -> int:
    auf, ab = font.getmetrics()
    return int((auf + ab) * 0.92)


def _schwung(x: float, y: float, breite: int, staerke: int) -> list[tuple[float, float]]:
    """Leicht geschwungener, nach rechts ansteigender Pinselstrich (wie in den manuellen Posts)."""
    hub = max(4, staerke * 1.2)
    pts = []
    for i in range(41):
        t = i / 40
        # quadratische Kurve: links tiefer, Mitte durchhaengend, rechts etwas hoeher
        py = y + (1 - t) * hub * 0.6 - 4 * t * (1 - t) * hub * -0.5 - t * hub * 0.6
        pts.append((x + t * breite, py))
    return pts


def _umbrechen(draw, text, font, breite):
    zeilen, aktuell = [], ""
    for wort in _woerter(text):
        probe = f"{aktuell} {wort}".strip()
        if draw.textlength(probe, font=font) <= breite or not aktuell:
            aktuell = probe
        else:
            zeilen.append(aktuell)
            aktuell = wort
    if aktuell:
        zeilen.append(aktuell)
    return zeilen


@lru_cache(maxsize=4)
def _logo(pfad: str) -> Image.Image:
    img = Image.open(pfad).convert("RGBA")
    img = img.crop(img.getbbox())
    h = round(img.height * LOGO_BREITE / img.width)
    return img.resize((LOGO_BREITE, h), Image.LANCZOS)


def logo_ecke(v: str, hz: str) -> tuple[str, str]:
    """Ecke fuer das Logo: unten, auf der Seite gegenueber dem Bildtext; liegt der Text
    unten, dann oben rechts (bzw. oben links, wenn der Text rechts steht)."""
    senk = "oben" if v == "unten" else "unten"
    waag = "links" if hz == "rechts" else "rechts"
    return senk, waag


def logo_setzen(img: Image.Image, ecke: tuple[str, str]) -> Image.Image:
    """Setzt das Radio-Boarisch-Logo dezent in eine Ecke. Helle Ecke -> farbiges Logo,
    dunkle Ecke -> Logo mit weisser Schrift; dazu ein weicher Schatten."""
    if not (config.LOGO_HELL.is_file() and config.LOGO_DUNKEL.is_file()):
        return img
    W, H = img.size
    probe = _logo(str(config.LOGO_HELL))
    w, h = probe.size
    x = LOGO_RAND if ecke[1] == "links" else W - LOGO_RAND - w
    y = LOGO_RAND if ecke[0] == "oben" else H - LOGO_RAND - h
    hell = ImageStat.Stat(img.convert("L").crop((x, y, x + w, y + h))).mean[0] > 150
    logo = _logo(str(config.LOGO_DUNKEL if hell else config.LOGO_HELL)).copy()
    alpha = logo.getchannel("A").point(lambda a: int(a * LOGO_DECKKRAFT))
    logo.putalpha(alpha)
    basis = img.convert("RGBA")
    farbe = (255, 255, 255) if hell else (0, 0, 0)   # Schatten hebt das Logo vom Grund ab
    maske = Image.new("L", img.size, 0)
    maske.paste(alpha.point(lambda a: int(a * 0.55)), (x + 2, y + 3))
    schatten = Image.new("RGBA", img.size, farbe + (0,))
    schatten.putalpha(maske.filter(ImageFilter.GaussianBlur(6)))
    basis = Image.alpha_composite(basis, schatten)
    basis.alpha_composite(logo, (x, y))
    return basis.convert("RGB")


def rendern(bild: str, bildtext: str, ziel: Path, quelle: Path | None = None,
            lage: str | None = None) -> Path:
    """bild: Dateiname im Pool; bei eigenen Bildern quelle = Pfad und lage = Textflaeche
    (z. B. "unten", "obenlinks"). Leerer bildtext: Bild ohne Text."""
    img = Image.open(quelle or (config.POOL_DIR / bild)).convert("RGB")
    # auf 4:5 zuschneiden und auf 1080x1350 bringen
    w, h = img.size
    soll_h = round(w * 5 / 4)
    if soll_h <= h:
        oben = (h - soll_h) // 2
        img = img.crop((0, oben, w, oben + soll_h))
    else:
        soll_w = round(h * 4 / 5)
        links = (w - soll_w) // 2
        img = img.crop((links, 0, links + soll_w, h))
    img = img.resize(ZIEL, Image.LANCZOS)
    W, H = ZIEL
    v, hz = textflaeche(f"text-{lage}" if lage else bild)
    if not bildtext.strip():
        img = logo_setzen(img, logo_ecke("", ""))
        ziel.parent.mkdir(parents=True, exist_ok=True)
        img.save(ziel, "JPEG", quality=90, optimize=True)
        return ziel

    spalte = hz != "mitte"
    max_breite = int(W * 0.62) if spalte else W - 2 * RAND
    haupt_text, unter_text = teilen(bildtext)

    draw = ImageDraw.Draw(img)
    groesse = 104 if spalte else 118
    while True:
        fh = _font(config.FONT_HAUPT, groesse)
        fu = _font(config.FONT_UNTER, max(32, round(groesse * 0.5)))
        haupt = _umbrechen(draw, haupt_text, fh, max_breite)
        unter = _umbrechen(draw, unter_text, fu, max_breite) if unter_text else []
        breitest = max(draw.textlength(z, font=f) for z, f in
                       [(z, fh) for z in haupt] + [(z, fu) for z in unter])
        passt = (len(haupt) <= (5 if spalte else 3) and len(unter) <= 2
                 and breitest <= max_breite)
        if passt or groesse <= 52:
            break
        groesse -= 4

    zh_h = _zeilenhoehe(fh)
    zh_u = _zeilenhoehe(fu)
    strich = max(8, round(groesse * 0.12))
    abstand = round(groesse * 0.22)
    block_w = int(breitest)
    block_h = zh_h * len(haupt) + abstand + strich + (abstand + zh_u * len(unter) if unter else 0)

    if hz == "links":
        x0 = RAND
    elif hz == "rechts":
        x0 = W - RAND - block_w
    else:
        x0 = (W - block_w) // 2
    if v == "oben":
        y0 = int(H * 0.07)
    elif v == "unten":
        y0 = H - int(H * 0.08) - block_h
    else:
        y0 = (H - block_h) // 2

    # weicher dunkler Schleier hinter dem Text fuer Lesbarkeit
    schleier = Image.new("L", ZIEL, 0)
    sd = ImageDraw.Draw(schleier)
    pad = int(groesse * 0.8)
    sd.rounded_rectangle(
        (x0 - pad, y0 - pad, x0 + block_w + pad, y0 + block_h + pad),
        radius=pad, fill=140,
    )
    schleier = schleier.filter(ImageFilter.GaussianBlur(pad * 0.8))
    img = Image.composite(Image.new("RGB", ZIEL, (0, 0, 0)), img, schleier)

    # Text und goldener Schwung mit leichtem Schatten
    schatten = Image.new("RGBA", ZIEL, (0, 0, 0, 0))
    text = Image.new("RGBA", ZIEL, (0, 0, 0, 0))
    sdraw, tdraw = ImageDraw.Draw(schatten), ImageDraw.Draw(text)

    def ausrichten(breite):
        if hz == "links":
            return x0
        if hz == "rechts":
            return x0 + block_w - breite
        return x0 + (block_w - breite) / 2

    y = y0
    for z in haupt:
        x = ausrichten(draw.textlength(z, font=fh))
        sdraw.text((x + 3, y + 4), z, font=fh, fill=(0, 0, 0, 190))
        tdraw.text((x, y), z, font=fh, fill=(255, 255, 255, 255))
        y += zh_h
    y += abstand
    sw = min(block_w, int(max(draw.textlength(z, font=fh) for z in haupt) * 0.82))
    sx = ausrichten(sw)
    punkte = _schwung(sx, y + strich, sw, strich)
    sdraw.line([(px + 3, py + 4) for px, py in punkte], fill=(0, 0, 0, 160), width=strich, joint="curve")
    tdraw.line(punkte, fill=config.GOLD + (255,), width=strich, joint="curve")
    y += strich + abstand
    for z in unter:
        x = ausrichten(draw.textlength(z, font=fu))
        sdraw.text((x + 2, y + 3), z, font=fu, fill=(0, 0, 0, 190))
        tdraw.text((x, y), z, font=fu, fill=(255, 255, 255, 255))
        y += zh_u
    schatten = schatten.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(Image.alpha_composite(img.convert("RGBA"), schatten), text)

    img = logo_setzen(img.convert("RGB"), logo_ecke(v, hz))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    img.save(ziel, "JPEG", quality=90, optimize=True, progressive=False)
    return ziel
