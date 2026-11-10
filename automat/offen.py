"""Zeigt gewaehlte Themen, zu denen Claude noch den Entwurf schreiben muss.

  python -m automat.offen --status <checkout des Branches redaktion>

Ausgabe: JSON-Liste; leer ([]) heisst: nichts zu tun.
"""
import argparse
import json
from pathlib import Path

from . import themen
from .lauf import _veraltet
from .status import Status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    a = ap.parse_args()
    print(json.dumps(themen.offen(Status(Path(a.status)), _veraltet), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
