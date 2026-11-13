"""Zeigt gewaehlte Themen, zu denen Claude noch den Entwurf schreiben muss.

  python -m automat.offen --status <checkout des Branches redaktion>

Ausgabe: JSON-Liste; leer ([]) heisst: nichts zu tun.
Themen/Hinweise, zu denen in entwuerfe/ oder rueckmeldungen/ (aktueller Checkout)
schon eine Datei mit passendem thema_ref/hinweis_ref liegt, gelten als erledigt.
"""
import argparse
import json
from pathlib import Path

from . import themen
from .lauf import _veraltet
from .status import Status


def erledigte_refs(*ordner: Path) -> set[str]:
    refs = set()
    for o in ordner:
        for f in sorted(Path(o).glob("*.json")) if Path(o).is_dir() else []:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if isinstance(d, dict):
                refs.update(r for r in (d.get("thema_ref"), d.get("hinweis_ref")) if r)
    return refs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--entwuerfe", default="entwuerfe")
    ap.add_argument("--rueckmeldungen", default="rueckmeldungen")
    a = ap.parse_args(argv)
    erledigt = erledigte_refs(Path(a.entwuerfe), Path(a.rueckmeldungen))
    print(json.dumps(themen.offen(Status(Path(a.status)), _veraltet, erledigt), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
