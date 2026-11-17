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
    st = Status(Path(a.status)) if a.status else None
    zuletzt = st.zuletzt_genutzte_bilder(ausser=e.get("id")) if st else []
    p = E.pruefen(e, zuletzt, st.zuletzt_bildsprache(ausser=e.get("id")) if st else [])
    if p.ok and isinstance(e.get("bild_ki"), dict):
        from . import bildsprache
        print("=== Bild-Prompt ===\n" + bildsprache.prompt(e["bild_ki"]))
    if p.ok:
        print("=== Caption ===\n" + E.caption(e) + "\n===============")
        if a.bild:
            render.rendern(e["bild"], e["bildtext"], Path(a.bild))
            print(f"Bild: {a.bild}")
    if zuletzt:
        print("Zuletzt genutzte Bilder:", ", ".join(zuletzt))
    for h in p.hinweise:
        print("HINWEIS:", h)
    for f in p.fehler:
        print("FEHLER:", f)
    print("OK" if p.ok else "NICHT OK")
    return 0 if p.ok else 1


if __name__ == "__main__":
    sys.exit(main())
