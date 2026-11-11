"""Bilderzeugung mit Cloudflare Workers AI, FLUX.1 schnell (Free-Tarif).

Bildregel 06 §10.3: dokumentarisch, fotorealistisch, 4:5, ohne Schrift, Logos, Tracht,
Kitsch und erkennbare Gesichter. FLUX schnell kennt keinen Negativ-Prompt und liefert
quadratisch (1024x1024); daher werden die Verbote positiv formuliert ("leere Strasse",
"Menschen nur klein von hinten") und das Bild mittig auf 4:5 zugeschnitten. Die freie
Textflaeche liegt deshalb immer oben oder unten (links/rechts faellt beim Zuschnitt weg).

Secrets (nur als GitHub-Actions-Secrets): CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN
(Berechtigung "Workers AI: Read & Edit" bzw. "Workers AI – Bearbeiten").

Bildtest (Schritt 1):  python -m automat.bildgen --test test/flux-1-schnell/
Modellvergleich:       python -m automat.bildgen --vergleich test/
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
KONTO_API = "https://api.cloudflare.com/client/v4/accounts/{konto}/ai"
API = KONTO_API + "/run/" + MODELL

# Modellvergleich: in dieser Reihenfolge, soweit im Konto verfuegbar (vermutlich guenstige
# zuerst, damit das Tageskontingent fuer moeglichst viele reicht). Weitere flux-2-* kommen dazu.
VERGLEICH = [
    "@cf/black-forest-labs/flux-2-klein-4b",
    "@cf/black-forest-labs/flux-2-klein-9b",
    "@cf/black-forest-labs/flux-2-dev",
    "@cf/leonardo/phoenix-1.0",
    "@cf/leonardo/lucid-origin",
]
# Modelle mit freier Bildgroesse erzeugen gleich 4:5; klein gehalten wegen des Kontingents.
GROESSE = (896, 1120)

# Betrieb (Betreiberentscheidung 11.11.2026 nach Modellvergleich): Leonardo Lucid Origin,
# direkt in 4:5. Faellt es aus, nimmt der Automat das Pool-Bild aus dem Entwurf.
PRODUKTIV = "@cf/leonardo/lucid-origin"
PRODUKTIV_GROESSE = (1088, 1360)
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


def _fehlertext(r: requests.Response) -> str:
    try:
        daten = r.json()
        return "; ".join(str(f.get("message", f)) for f in daten.get("errors", [])) or r.text[:300]
    except ValueError:
        return r.text[:300]


def _bild_aus_antwort(r: requests.Response) -> Image.Image:
    art = r.headers.get("content-type", "")
    if r.ok and art.startswith("image/"):
        return Image.open(io.BytesIO(r.content))
    try:
        daten = r.json()
    except ValueError:
        raise BildFehler(f"HTTP {r.status_code}, unerwartete Antwort ({art})")
    if not r.ok or not daten.get("success", True):
        raise BildFehler(f"HTTP {r.status_code}: {_fehlertext(r)}")
    erg = daten.get("result", daten)
    b64 = erg if isinstance(erg, str) else (erg or {}).get("image")
    if not b64:
        raise BildFehler("Antwort enthaelt kein Bild")
    return Image.open(io.BytesIO(base64.b64decode(b64)))


class EingabeFehler(BildFehler):
    """HTTP 400: das Modell erwartet andere Parameter."""


def _senden(konto, token, modell, art, felder) -> Image.Image:
    url = f"{KONTO_API.format(konto=konto)}/run/{modell}"
    kopf = {"Authorization": f"Bearer {token}"}
    if art == "form":
        r = requests.post(url, files={k: (None, str(v)) for k, v in felder.items()},
                          timeout=180, headers=kopf)
    else:
        r = requests.post(url, json=felder, timeout=180, headers=kopf)
    if r.status_code == 400:
        raise EingabeFehler(f"HTTP 400: {_fehlertext(r)}")
    return _bild_aus_antwort(r)


def varianten(modell: str, text: str, groesse=GROESSE) -> list[tuple[str, dict]]:
    """Moegliche Aufrufformen; die erste, die das Modell annimmt, gilt."""
    if modell == MODELL:
        return [("json", {"prompt": text, "steps": 8})]
    b, h = groesse
    return [
        ("json", {"prompt": text, "width": b, "height": h}),
        ("form", {"prompt": text, "width": b, "height": h}),
        ("json", {"prompt": text}),
        ("form", {"prompt": text}),
    ]


def erzeugen(motiv: str, ziel: Path, seed: int | None = None, modell: str = MODELL,
             zugangsdaten: tuple[str, str] | None = None, groesse=GROESSE,
             fertig: str | None = None) -> str:
    """Erzeugt ein Bild zum Motiv, speichert es als 1080x1350-JPEG und gibt die
    verwendete Aufrufform zurueck. seed wird nicht gesendet (flux-1-schnell lehnt ihn ab)."""
    konto, token = zugangsdaten or zugang()
    letzter = None
    for art, felder in varianten(modell, fertig or prompt(motiv), groesse):
        try:
            roh = _senden(konto, token, modell, art, felder)
        except EingabeFehler as e:
            letzter = e
            continue
        ziel.parent.mkdir(parents=True, exist_ok=True)
        auf_4_5(roh).save(ziel, "JPEG", quality=90, optimize=True)
        return f"{art}:{','.join(k for k in felder if k != 'prompt') or 'nur prompt'}; roh {roh.size[0]}x{roh.size[1]}"
    raise letzter or BildFehler("keine Aufrufform passt")


def konfiguriert() -> bool:
    try:
        zugang()
        return True
    except BildFehler:
        return False


def ki_bild(text: str, ziel: Path) -> str:
    """Bild fuer einen Beitrag mit dem Betriebsmodell (1080x1350 JPEG ohne Bildtext).
    text ist der fertige Prompt (automat.bildsprache)."""
    return erzeugen("", ziel, modell=PRODUKTIV, groesse=PRODUKTIV_GROESSE, fertig=text)


def modelle_im_konto(z) -> list[str] | None:
    konto, token = z
    try:
        r = requests.get(f"{KONTO_API.format(konto=konto)}/models/search",
                         params={"task": "Text-to-Image", "per_page": 100}, timeout=60,
                         headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return sorted(m["name"] for m in r.json().get("result", []))
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        print(f"Modellliste nicht abrufbar ({e}), nehme feste Liste", file=sys.stderr)
        return None


def bildtest(ordner: Path, modell: str = MODELL, z=None) -> dict:
    """5 Testmotive mit einem Modell; vorhandene Bilder werden nicht neu erzeugt
    (ein erneuter Lauf macht nach leerem Tageskontingent dort weiter)."""
    z = z or zugang()
    protokoll = []
    for m in TESTMOTIVE:
        ziel = ordner / m["datei"]
        eintrag = {"datei": m["datei"], "prompt": prompt(m["motiv"])}
        if ziel.exists():
            protokoll.append({**eintrag, "ok": True, "aufruf": "schon vorhanden"})
            continue
        try:
            aufruf = erzeugen(m["motiv"], ziel, modell=modell, zugangsdaten=z)
            print(f"OK     {ziel}  ({aufruf})")
            protokoll.append({**eintrag, "ok": True, "aufruf": aufruf})
        except (BildFehler, requests.RequestException) as e:
            print(f"FEHLER {ziel}: {e}", file=sys.stderr)
            protokoll.append({**eintrag, "ok": False, "fehler": str(e)})
            # Derselbe Fehler kaeme bei jedem Motiv wieder (Parameter, Kontingent, Rechte):
            # Modell abbrechen, Kontingent sparen.
            break
    ergebnis = {"modell": modell, "bilder": protokoll}
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "prompts.json").write_text(
        json.dumps(ergebnis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ergebnis


def vergleich(ordner: Path) -> int:
    z = zugang()
    vorhanden = modelle_im_konto(z)
    if vorhanden is None:
        auswahl = VERGLEICH
    else:
        auswahl = [m for m in VERGLEICH if m in vorhanden]
        auswahl += [m for m in vorhanden if "flux-2" in m and m not in auswahl]
    print("Text-to-Image im Konto:", vorhanden)
    print("Vergleich mit:", auswahl)
    uebersicht = {"im_konto": vorhanden, "verglichen": {}}
    for modell in [MODELL] + auswahl:
        erg = bildtest(ordner / modell.split("/")[-1], modell, z)
        ok = sum(b["ok"] for b in erg["bilder"])
        uebersicht["verglichen"][modell] = f"{ok}/{len(TESTMOTIVE)} Bilder"
    (ordner / "vergleich.json").write_text(
        json.dumps(uebersicht, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(uebersicht["verglichen"], ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--test", type=Path, metavar="ORDNER", help="die 5 Testbilder erzeugen")
    ap.add_argument("--vergleich", type=Path, metavar="ORDNER",
                    help="die 5 Testmotive mit mehreren Modellen, je Modell ein Unterordner")
    ap.add_argument("--betrieb", type=Path, metavar="ORDNER",
                    help="Probe des Betriebswegs: Beispielentwurf -> KI-Bild -> Bildtext")
    ap.add_argument("--motiv", help="ein einzelnes Motiv (englisch)")
    ap.add_argument("--ziel", type=Path, help="Zieldatei fuer --motiv")
    a = ap.parse_args(argv)
    try:
        if a.betrieb:
            from . import config, render
            e = json.loads((config.REPO_ROOT / "docs" / "beispiel-entwurf.json").read_text("utf-8"))
            roh = a.betrieb / "ki-roh.jpg"
            from . import bildsprache
            muster = json.loads((config.REPO_ROOT / "docs" / "bildsprache-muster.json")
                                .read_text("utf-8"))
            faelle = [("beispiel", e["bild_ki"], e["bildtext"])] + \
                     [(m["name"], m["bild_ki"], m.get("bildtext", "")) for m in muster]
            for name, b, bt in faelle:
                ziel = a.betrieb / f"{name}.jpg"
                if ziel.exists():
                    continue
                roh = a.betrieb / "roh" / f"{name}.jpg"
                text = bildsprache.prompt(b)
                (a.betrieb / "roh").mkdir(parents=True, exist_ok=True)
                (a.betrieb / "roh" / f"{name}.txt").write_text(text + "\n", encoding="utf-8")
                print(name, ki_bild(text, roh))
                render.rendern("", bt, ziel, quelle=roh, lage=b["lage"])
            return 0
        if a.vergleich:
            return vergleich(a.vergleich)
        if a.test:
            ok = sum(b["ok"] for b in bildtest(a.test)["bilder"])
            return 0 if ok else 1
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
