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
    max_breite = int(W * 0.60) if spalte else W - 2 * RAND
    max_zeilen = 6 if spalte else 4

    draw = ImageDraw.Draw(img)
    groesse = 92 if spalte else 96
    while True:
        font = ImageFont.truetype(str(config.FONT_PATH), groesse)
        zeilen = _umbrechen(draw, bildtext.strip(), font, max_breite)
        breitest = max(draw.textlength(z, font=font) for z in zeilen)
        if (len(zeilen) <= max_zeilen and breitest <= max_breite) or groesse <= 44:
            break
        groesse -= 4
    zeilenhoehe = int(groesse * 1.18)
    block_h = zeilenhoehe * len(zeilen)
    block_w = int(breitest)

    if hz == "links":
        x0 = RAND
    elif hz == "rechts":
        x0 = W - RAND - block_w
    else:
        x0 = (W - block_w) // 2
    if v == "oben":
        y0 = int(H * 0.08)
    elif v == "unten":
        y0 = H - int(H * 0.08) - block_h
    else:
        y0 = (H - block_h) // 2

    # weicher dunkler Schleier hinter dem Text fuer Lesbarkeit
    schleier = Image.new("L", ZIEL, 0)
    sd = ImageDraw.Draw(schleier)
    pad = int(groesse * 0.9)
    sd.rounded_rectangle(
        (x0 - pad, y0 - pad, x0 + block_w + pad, y0 + block_h + pad),
        radius=pad, fill=140,
    )
    schleier = schleier.filter(ImageFilter.GaussianBlur(pad * 0.8))
    img = Image.composite(Image.new("RGB", ZIEL, (0, 0, 0)), img, schleier)

    # Text mit leichtem Schatten
    schatten = Image.new("RGBA", ZIEL, (0, 0, 0, 0))
    text = Image.new("RGBA", ZIEL, (0, 0, 0, 0))
    sdraw, tdraw = ImageDraw.Draw(schatten), ImageDraw.Draw(text)
    for i, z in enumerate(zeilen):
        zw = draw.textlength(z, font=font)
        if hz == "links":
            x = x0
        elif hz == "rechts":
            x = x0 + block_w - zw
        else:
            x = x0 + (block_w - zw) / 2
        y = y0 + i * zeilenhoehe
        sdraw.text((x + 3, y + 3), z, font=font, fill=(0, 0, 0, 180))
        tdraw.text((x, y), z, font=font, fill=(255, 255, 255, 255))
    schatten = schatten.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(Image.alpha_composite(img.convert("RGBA"), schatten), text)

    img = logo_setzen(img.convert("RGB"), logo_ecke(v, hz))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    img.save(ziel, "JPEG", quality=90, optimize=True, progressive=False)
    return ziel
