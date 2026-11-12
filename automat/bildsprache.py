"""Bildsprache von Radio Boarisch fuer KI-Bilder (docs/BILDSPRACHE.md).

Ein Bildgenerator wie Leonardo Lucid Origin ergaenzt keinen Kontext: Er malt, was im
Prompt steht, und versteht Verneinungen schlecht ("no dirndl" erzeugt eher ein Dirndl).
Deshalb beschreibt der Entwurf das Bild in Bausteinen (Feld "bild_ki"), und dieses Modul
setzt daraus einen langen, positiv formulierten Prompt zusammen:

  Aufbau  ->  Motiv  ->  Umgebung  ->  Bayern von heute  ->  Licht  ->  Farbwelt
          ->  Region  ->  Themenart  ->  Hausstil  ->  freie Flaeche fuer den Bildtext

Grundlage: North Star §5/§8/§12, Strategie §2/§4 ("Bayern beweisen, nicht behaupten",
"bayerisch, aber nicht folkloristisch", "verwurzelt, aber nicht verstaubt"),
06 §10.3 (Bildregel) und §10.4 (Blaulicht, ernste Meldungen).
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------- Hausstil

HAUSSTIL = (
    "Contemporary documentary photograph for a regional Bavarian magazine, present-day "
    "Bavaria as it really looks today. Full-frame camera, 35mm lens, natural "
    "available light, honest true-to-life colours with moderate saturation, fine film grain, "
    "real textures, weathered materials and small everyday imperfections. Unposed, quietly "
    "observed, calm and warm in feeling, grounded and unpretentious. Plain unmarked surfaces: "
    "blank walls, bare wood, clean facades."
)

# Betreiberentscheidung 11.11.2026: Menschen erlaubt, nie erkennbar; Blaulicht/Nachruf ohne.
MENSCHEN = (
    "People, if any, appear small in the middle distance or seen from behind, faces turned "
    "away or hidden in shadow, adults in ordinary present-day clothes such as jeans, rain "
    "jackets, knitwear and sneakers."
)
MENSCHENLEER = "The place is deserted, quiet and still."

# ---------------------------------------------------------------- Themenarten (§10.2)

ARTEN = {
    "musik": (
        "Live music as it happens in Bavaria today: a real stage or rehearsal room, warm "
        "stage light, cables, monitor speakers, microphone stands, brass and acoustic "
        "instruments as honest objects. Musicians only as distant silhouettes or from behind, "
        "faces in shadow.", True),
    "veranstaltung": (
        "A real event in present-day Bavaria, observed calmly at its edges, in the moments "
        "before it starts or after it ends: set-up, empty benches, lights coming on, "
        "packed-away gear.", True),
    "brauchtum": (
        "A living custom as it is practised today, told through honest details: hands at "
        "work, materials, tools, preparation, the place where it happens. Participants in "
        "ordinary present-day clothes.", True),
    "kultur": (
        "Culture in Bavaria today: a real venue, workshop, studio or exhibition space, "
        "contemporary and lived-in, with quiet light and visible craft.", True),
    "meldung": (
        "A calm, neutral and recognisably Bavarian scene that fits the topic without "
        "illustrating any single person.", True),
    "sender": (
        "Radio of today: a small, contemporary radio studio or a kitchen table with a "
        "simple radio, headphones, a microphone, warm practical light, plain equipment.",
        True),
    "blaulicht": (
        "A calm, neutral place connected to the region of the report, serene and orderly; "
        "an empty road, a quiet edge of town or a landscape on an ordinary, "
        "uneventful day.", False),
    "nachruf": (
        "Quiet, dignified and respectful: a single meaningful object or an empty, familiar "
        "place, soft diffused light, muted and restrained colours, a sense of stillness.",
        False),
}

# ---------------------------------------------------------------- Regionen

# Kurz gehalten: nur Bau- und Landschaftscharakter. Was im Bild konkret zu sehen ist, steht
# in motiv/umgebung; ein langer Regionsblock wuerde den Generator Dinge dazumalen lassen.
REGIONEN = {
    "oberbayern": "Upper Bavaria, Alpine foothills: wide low-pitched roofs, white plaster, plain wooden balconies.",
    "niederbayern": "Lower Bavaria: gentle hills, market towns with long squares, colourful plastered facades, Gothic brick.",
    "oberpfalz": "Upper Palatinate: spruce forests, granite, fish ponds, modest plastered houses with steep roofs.",
    "oberfranken": "Upper Franconia: half-timbering, sandstone, limestone rocks, narrow wooded valleys.",
    "mittelfranken": "Middle Franconia: red and yellow sandstone, half-timbered houses, quiet lakes and heath.",
    "unterfranken": "Lower Franconia: vineyards on terraced slopes, baroque sandstone, half-timbered wine villages.",
    "schwaben": "Bavarian Swabia: wide river plains, plastered towns with stepped gables, green Allgaeu hills.",
    "bayern": "",
}

# ---------------------------------------------------------------- Bildaufbau-Katalog

AUFBAU = {
    "weite": "Wide establishing shot, the main subject small within a large space.",
    "mittel": "Medium shot at eye level, the main subject in the lower half of the frame.",
    "detail": "Close-up detail shot with shallow depth of field, background softly blurred.",
    "rahmen": "Framed through a foreground element such as a doorway, window or branches.",
    "diagonale": "A strong diagonal line leads from a lower corner deep into the image.",
    "zentral": "Symmetrical one-point perspective with a centred vanishing point.",
    "aufsicht": "Slightly elevated viewpoint looking down onto the scene.",
    "untersicht": "Low viewpoint close to the ground, looking slightly upwards.",
    "gegenlicht": "Soft backlight, the subject outlined against the light, gentle contrast.",
}

FLAECHE = {
    "oben": "The upper third of the frame is calm and uncluttered: open sky, a plain wall or soft background.",
    "unten": "The lower third of the frame is calm and uncluttered: plain ground, water, grass or soft foreground.",
    "mitte": "A calm, evenly toned, uncluttered area runs across the centre of the frame.",
    "links": "The left third of the frame is calm and uncluttered.",
    "rechts": "The right third of the frame is calm and uncluttered.",
}

FELDER = ["art", "region", "motiv", "umgebung", "heute", "licht", "farbwelt", "aufbau", "lage"]
TEXTFELDER = ["motiv", "umgebung", "heute", "licht", "farbwelt"]
LAENGE = {"motiv": (25, 400), "umgebung": (20, 300), "heute": (15, 250),
          "licht": (10, 200), "farbwelt": (10, 160)}
PROMPT_MAX = 2000

# ---------------------------------------------------------------- Verbote

# Was ein Generator woertlich malt, auch wenn es verneint dasteht. Nicht einmal nennen.
VERBOTEN = {
    r"\bdirndl": "Dirndl",
    r"\blederhose": "Lederhosen",
    r"\btracht|\bcostume|\bfolk dress|\btraditional (dress|clothing|outfit)": "Tracht",
    r"\bedelwei(ss|ß)": "Edelweiss",
    r"\bgentian|\benzian": "Enzian",
    r"blue[- ]and[- ]white|blue/white|white[- ]and[- ]blue|wei(ß|ss)[- ]?blau|blau[- ]?wei(ß|ss)": "Blau-Weiss",
    r"\brhomb|\blozenge|\bdiamond pattern|\braute": "Rauten",
    r"\bflags?\b|\bbanners?\b|\bbunting\b": "Fahnen/Banner",
    r"\blogos?\b|\bbrand(ed|s)?\b|\btrademark": "Logos/Marken",
    r"\btext\b|\bletter(s|ing)\b|\bwords?\b|\bwriting\b|\btypograph|\bcaption|\bsigns?\b|"
    r"\bsignage\b|\bposters?\b|\blabels?\b|\bnumber plate|\blicen[cs]e plate": "Schrift/Schilder",
    r"\bportrait|\bfaces?\b|\bclose-up of (a )?(man|woman|person)|\blooking at the camera|"
    r"\bselfie|\bsmiling": "Gesichter/Portraet",
    r"\bchild|\bchildren\b|\bkids?\b|\bbab(y|ies)\b|\bgirls?\b|\bboys?\b|\bteen": "Kinder/Minderjaehrige",
    r"\bpostcard|\bpicturesque|\bidyllic|\bfairy ?tale|\bkitsch|\bmagical|\bdreamy|\bromantic": "Kitsch",
    r"\bneuschwanstein|\boktoberfest|\bwiesn\b": "touristisches Bayern-Klischee",
    r"\bno\b|\bnot\b|\bwithout\b|\bnever\b|\bavoid": "Verneinung (Generator ignoriert sie, das Wort wird gemalt)",
}

# Moeglich, aber oft Klischee oder Kitsch: Hinweis fuer den Betreiber.
VORSICHT = {
    r"\bbeer stein|\bmaß|\bmass\b|\bpretzels?\b|\bbrezn": "Masskrug/Brezn (Klischee?)",
    r"\bgolden hour|\bsunset|\bsunrise|\balpenglow|\bdramatic|\bepic\b|\bvibrant|\bglowing": "Kitschlicht?",
    r"\bmaypole|\bmaibaum": "Maibaum nur als geschaelter Stamm, ohne Bemalung und Schilder",
    r"\bcastle|\bschloss|\bmonastery|\babbey": "echtes Bauwerk? Nur allgemein beschreiben",
    r"\bcows?\b|\bcattle": "Kuehe (Klischee?)",
}


def _treffer(muster: dict, text: str) -> list[str]:
    low = text.lower()
    return sorted({name for rx, name in muster.items() if re.search(rx, low)})


def pruefen(b, zuletzt: list[dict] | None = None) -> tuple[list[str], list[str]]:
    """-> (fehler, hinweise) fuer das Feld bild_ki eines Entwurfs."""
    fehler, hinweise = [], []
    if not isinstance(b, dict):
        return ["bild_ki muss ein Objekt mit den Bausteinen sein (docs/BILDSPRACHE.md)"], []
    for f in FELDER:
        if not str(b.get(f) or "").strip():
            fehler.append(f"bild_ki.{f} fehlt")
    if fehler:
        return fehler, hinweise
    if b["art"] not in ARTEN:
        fehler.append(f"bild_ki.art: eines von {', '.join(ARTEN)}")
    if b["region"] not in REGIONEN:
        fehler.append(f"bild_ki.region: eines von {', '.join(REGIONEN)}")
    if b["aufbau"] not in AUFBAU:
        fehler.append(f"bild_ki.aufbau: eines von {', '.join(AUFBAU)}")
    if not re.fullmatch(r"(oben|unten|mitte|links|rechts)(oben|unten|links|rechts|mitte)?", b["lage"]):
        fehler.append("bild_ki.lage: oben, unten, mitte, links, rechts (oder z. B. linksunten)")
    for f in TEXTFELDER:
        lo, hi = LAENGE[f]
        n = len(str(b[f]).strip())
        if not lo <= n <= hi:
            fehler.append(f"bild_ki.{f}: {lo} bis {hi} Zeichen (jetzt {n})")
        if re.search(r"[äöüÄÖÜß]", str(b[f])) and f != "farbwelt":
            hinweise.append(f"bild_ki.{f}: bitte englisch schreiben (Generator versteht Deutsch schlecht)")
    alles = " ".join(str(b[f]) for f in TEXTFELDER)
    for name in _treffer(VERBOTEN, alles):
        fehler.append(f"bild_ki: '{name}' nicht beschreiben, auch nicht verneint (Bildregel 10.3)")
    for name in _treffer(VORSICHT, alles):
        hinweise.append(f"bild_ki: {name}")
    for vorher in (zuletzt or [])[:1]:
        if vorher.get("aufbau") == b["aufbau"]:
            fehler.append(f"bild_ki.aufbau '{b['aufbau']}' wie im letzten Post – anderen Bildaufbau "
                          "waehlen (10.3: kein Post wie der vorige)")
    for vorher in (zuletzt or [])[:3]:
        if (vorher.get("farbwelt") or "").strip().lower() == b["farbwelt"].strip().lower():
            fehler.append("bild_ki.farbwelt wie in einem der letzten Posts – eigene Farbwelt waehlen")
            break
    if not fehler and len(prompt(b)) > PROMPT_MAX:
        fehler.append(f"bild_ki: Prompt zu lang ({len(prompt(b))} > {PROMPT_MAX}) – Bausteine kuerzen")
    return fehler, hinweise


def prompt(b: dict) -> str:
    """Setzt den Prompt aus den Bausteinen zusammen (wichtigstes zuerst)."""
    art_text, menschen_erlaubt = ARTEN[b["art"]]
    lage = b["lage"]
    flaeche = FLAECHE.get(lage) or " ".join(FLAECHE[t] for t in ("oben", "unten", "mitte", "links", "rechts")
                                            if t in lage)
    teile = [
        AUFBAU[b["aufbau"]],
        b["motiv"].strip(),
        b["umgebung"].strip(),
        b["heute"].strip(),
        b["licht"].strip(),
        f"Colour palette: {b['farbwelt'].strip()}.",
        REGIONEN[b["region"]],
        art_text,
        HAUSSTIL,
        MENSCHEN if menschen_erlaubt else MENSCHENLEER,
        flaeche,
    ]
    return " ".join(t if t.endswith(".") else t + "." for t in teile if t)


def einfach(motiv: str) -> str:
    """Alter Weg (Feld bildmotiv als Freitext): Motiv plus Hausstil."""
    return f"{motiv.strip()} {HAUSSTIL} {MENSCHEN}"
