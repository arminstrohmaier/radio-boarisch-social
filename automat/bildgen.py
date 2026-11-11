"""Bilderzeugung mit Cloudflare Workers AI, FLUX.1 schnell (Free-Tarif).

Bildregel 06 §10.3: dokumentarisch, fotorealistisch, 4:5, ohne Schrift, Logos, Tracht,
Kitsch und erkennbare Gesichter. FLUX schnell kennt keinen Negativ-Prompt und liefert
quadratisch (1024x1024); daher werden die Verbote positiv formuliert ("leere Strasse",
"Menschen nur klein von hinten") und das Bild mittig auf 4:5 zugeschnitten. Die freie
Textflaeche liegt deshalb immer oben oder unten (links/rechts faellt beim Zuschnitt weg).

Secrets (nur als GitHub-Actions-Secrets): CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN
(Berechtigung "Workers AI: Read & Edit" bzw. "Workers AI – Bearbeiten").

Bildtest (Schritt 1):  python -m automat.bildgen --test test/
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path

import requests
from PIL import Image

MODELL = "@cf/black-forest-labs/flux-1-schnell"
API = "https://api.cloudflare.com/client/v4/accounts/{konto}/ai/run/" + MODELL
ZIEL = (1080, 1350)

# Wird an jedes Motiv angehaengt: die Bildregel in Worten, die FLUX versteht.
STIL = (
    "Documentary photograph, photorealistic, natural available light, muted realistic colours, "
    "shot on a 35mm lens, slight film grain, unstaged, ordinary everyday scene in rural Bavaria. "
    "No people in the frame. Plain surfaces without any lettering, signs, posters, brand names "
    "or logos. Not decorated, not picturesque postcard style, no traditional costume."
)

# Testmotive fuer Schritt 1. textflaeche: wo spaeter der Bildtext stehen kann.
TESTMOTIVE = [
    {
        "datei": "01_landstrasse-herbst_text-oben.jpg",
        "motiv": "An empty two-lane country road in autumn winding between harvested fields and a "
                 "row of birch trees with yellow leaves, overcast grey sky filling the upper third "
                 "of the image, wet asphalt, eye level from the roadside.",
        "seed": 1101,
    },
    {
        "datei": "02_wirtshaus_text-oben.jpg",
        "motiv": "Interior of an empty old village inn dining room in the late afternoon, simple "
                 "wooden tables and benches, scrubbed wooden floor, a tiled stove in the corner, "
                 "plain whitewashed wall and ceiling in the upper part of the image, soft window light.",
        "seed": 1102,
    },
    {
        "datei": "03_dorfplatz_text-oben.jpg",
        "motiv": "A quiet village square in Bavaria on an early morning, cobblestones, a plain "
                 "baroque church tower and simple plastered houses without signs, a single linden "
                 "tree, calm pale sky across the upper third of the image, nobody around.",
        "seed": 1103,
    },
    {
        "datei": "04_see_text-oben.jpg",
        "motiv": "A Bavarian lake on a calm grey morning, a wooden jetty reaching into flat water, "
                 "reeds in the foreground, a low forested shoreline on the far side, soft mist "
                 "and a wide empty sky across the upper half of the image.",
        "seed": 1104,
    },
    {
        "datei": "05_neutral_text-mitte.jpg",
        "motiv": "A wide misty meadow landscape in the foothills of the Alps, gentle hills fading "
                 "into fog, a few dark spruce trees at the edges, very calm and even tones with "
                 "a large quiet area in the centre of the image, suitable as a neutral background.",
        "seed": 1105,
    },
]


class BildFehler(Exception):
    pass


def zugang() -> tuple[str, str]:
    konto = (os.environ.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()
    token = (os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()
    fehlt = [n for n, v in (("CLOUDFLARE_ACCOUNT_ID", konto), ("CLOUDFLARE_API_TOKEN", token)) if not v]
    if fehlt:
        raise BildFehler("Secret fehlt: " + ", ".join(fehlt))
    return konto, token


def prompt(motiv: str) -> str:
    return f"{motiv} {STIL}"


def auf_4_5(img: Image.Image) -> Image.Image:
    """Mittig auf 4:5 zuschneiden und auf 1080x1350 bringen."""
    img = img.convert("RGB")
    w, h = img.size
    if w * 5 > h * 4:   # zu breit
        soll_w = round(h * 4 / 5)
        x = (w - soll_w) // 2
        img = img.crop((x, 0, x + soll_w, h))
    else:
        soll_h = round(w * 5 / 4)
        y = (h - soll_h) // 2
        img = img.crop((0, y, w, y + soll_h))
    return img.resize(ZIEL, Image.LANCZOS)


def _bild_aus_antwort(r: requests.Response) -> Image.Image:
    art = r.headers.get("content-type", "")
    if art.startswith("image/"):
        return Image.open(io.BytesIO(r.content))
    try:
        daten = r.json()
    except ValueError:
        raise BildFehler(f"HTTP {r.status_code}, unerwartete Antwort ({art})")
    if not r.ok or not daten.get("success", True):
        fehler = "; ".join(str(f.get("message", f)) for f in daten.get("errors", [])) or r.text[:300]
        raise BildFehler(f"HTTP {r.status_code}: {fehler}")
    b64 = (daten.get("result") or {}).get("image")
    if not b64:
        raise BildFehler("Antwort enthaelt kein Bild")
    return Image.open(io.BytesIO(base64.b64decode(b64)))


def erzeugen(motiv: str, ziel: Path, seed: int | None = None, steps: int = 8,
             zugangsdaten: tuple[str, str] | None = None) -> Path:
    """Erzeugt ein Bild zum Motiv und speichert es als 1080x1350-JPEG."""
    konto, token = zugangsdaten or zugang()
    # seed nimmt die Workers-AI-Schnittstelle nicht an (HTTP 400, 11.11.2026);
    # das Argument bleibt nur fuers Protokoll.
    body = {"prompt": prompt(motiv), "steps": steps}
    r = requests.post(API.format(konto=konto), json=body, timeout=120,
                      headers={"Authorization": f"Bearer {token}"})
    roh = _bild_aus_antwort(r)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    auf_4_5(roh).save(ziel, "JPEG", quality=90, optimize=True)
    return ziel


def bildtest(ordner: Path) -> int:
    z = zugang()
    protokoll, fehler = [], 0
    for m in TESTMOTIVE:
        ziel = ordner / m["datei"]
        try:
            erzeugen(m["motiv"], ziel, seed=m["seed"], zugangsdaten=z)
            print(f"OK     {ziel}")
            protokoll.append({**m, "prompt": prompt(m["motiv"]), "ok": True})
        except (BildFehler, requests.RequestException) as e:
            fehler += 1
            print(f"FEHLER {ziel}: {e}", file=sys.stderr)
            protokoll.append({**m, "prompt": prompt(m["motiv"]), "ok": False, "fehler": str(e)})
    (ordner / "prompts.json").write_text(
        json.dumps({"modell": MODELL, "steps": 8, "bilder": protokoll}, ensure_ascii=False, indent=2)
        + "\n", encoding="utf-8")
    return 1 if fehler == len(TESTMOTIVE) else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--test", type=Path, metavar="ORDNER", help="die 5 Testbilder erzeugen")
    ap.add_argument("--motiv", help="ein einzelnes Motiv (englisch)")
    ap.add_argument("--ziel", type=Path, help="Zieldatei fuer --motiv")
    a = ap.parse_args(argv)
    try:
        if a.test:
            return bildtest(a.test)
        if a.motiv and a.ziel:
            print(erzeugen(a.motiv, a.ziel))
            return 0
    except BildFehler as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
