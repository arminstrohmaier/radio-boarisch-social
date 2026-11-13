"""Prueft einen Entwurf vor dem Commit und zeigt Caption und Bild.

  python -m automat.pruefen entwuerfe/2026-11-12-beispiel.json [--status redaktion] [--bild out.jpg]

--status: Ordner eines Checkouts des Branches 'redaktion' (fuer die Regel
"kein Bild wie im vorigen Post"). Exit-Code 1 bei Regelverstoss.
"""
import argparse
import sys
from pathlib import Path

from . import entwurf as E, render
from .status import Status


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("datei")
    ap.add_argument("--status")
    ap.add_argument("--bild", help="gerendertes Bild hierhin schreiben")
    a = ap.parse_args(argv)
    e = E.laden(Path(a.datei))
    zuletzt = Status(Path(a.status)).zuletzt_genutzte_bilder(ausser=e.get("id")) if a.status else []
    p = E.pruefen(e, zuletzt)
    if p.ok:
        print("=== Caption ===\n" + E.caption(e) + "\n===============")
        if a.bild:
            render.rendern(e["bild"], e["bildtext"], Path(a.bild))
            print(f"Bild: {a.bild}")
    if zuletzt:
        print("Zuletzt genutzte Bilder:", ", ".join(zuletzt))
    if not (e.get("thema_ref") or e.get("hinweis_ref")):
        print("WARNUNG: weder thema_ref noch hinweis_ref – gehoert der Entwurf zu einem gewaehlten "
              "Thema oder Hinweis, MUSS die Kennung aus automat.offen hinein.")
    for h in p.hinweise:
        print("HINWEIS:", h)
    for f in p.fehler:
        print("FEHLER:", f)
    print("OK" if p.ok else "NICHT OK")
    return 0 if p.ok else 1


if __name__ == "__main__":
    sys.exit(main())
