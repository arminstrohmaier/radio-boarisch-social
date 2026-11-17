"""Zustand des Automaten. Liegt im Branch 'redaktion' (eigener Checkout),
damit main nur Code enthaelt und die Bilder eine oeffentliche URL haben."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OFFEN = "gesendet"
ABGESCHLOSSEN = {"veroeffentlicht", "verworfen", "test_ok", "freigegeben_manuell", "veraltet"}


def jetzt() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def schluessel(post_id: str) -> str:
    return hashlib.sha1(post_id.encode()).hexdigest()[:10]


def inhalt_hash(entwurf: dict) -> str:
    return hashlib.sha1(json.dumps(entwurf, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class Status:
    def __init__(self, ordner: Path):
        self.ordner = Path(ordner)
        self.datei = self.ordner / "status.json"
        if self.datei.exists():
            self.daten = json.loads(self.datei.read_text(encoding="utf-8"))
        else:
            self.daten = {"telegram_offset": None, "posts": {}}
        self.daten.setdefault("posts", {})
        self.daten.setdefault("telegram_offset", None)
        self.daten.setdefault("themen", {})

    @property
    def themen(self) -> dict:
        return self.daten["themen"]

    @property
    def posts(self) -> dict:
        return self.daten["posts"]

    def post_ordner(self, post_id: str) -> Path:
        return self.ordner / "posts" / post_id

    def entwurf(self, post_id: str) -> dict:
        return json.loads((self.post_ordner(post_id) / "entwurf.json").read_text(encoding="utf-8"))

    def bild(self, post_id: str) -> Path:
        return self.post_ordner(post_id) / "bild.jpg"

    def nach_schluessel(self, key: str) -> str | None:
        for pid, p in self.posts.items():
            if p.get("key") == key:
                return pid
        return None

    def zuletzt_genutzte_bilder(self, ausser: str | None = None, anzahl: int = 3) -> list[str]:
        kandidaten = [
            (p.get("importiert", ""), p.get("bild"))
            for pid, p in self.posts.items()
            if pid != ausser and not p.get("test")
            and p.get("status") not in ("verworfen", "ungueltig", "veraltet")
        ]
        kandidaten.sort(reverse=True)
        return [b for _, b in kandidaten[:anzahl] if b]

    def zuletzt_bildsprache(self, ausser: str | None = None, anzahl: int = 3) -> list[dict]:
        """Aufbau und Farbwelt der letzten KI-Bilder, neuestes zuerst."""
        kandidaten = [
            (p.get("importiert", ""), p["bild_ki"])
            for pid, p in self.posts.items()
            if pid != ausser and not p.get("test") and p.get("bild_ki")
            and p.get("status") not in ("verworfen", "ungueltig", "veraltet")
        ]
        kandidaten.sort(key=lambda k: k[0], reverse=True)
        return [b for _, b in kandidaten[:anzahl]]

    def speichern(self):
        self.ordner.mkdir(parents=True, exist_ok=True)
        tmp = self.datei.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.daten, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.datei)


def git_commit(ordner: Path, nachricht: str, push: bool = True):
    """Committet und pusht den Status-Checkout (nur in GitHub Actions)."""
    def g(*a, check=True):
        return subprocess.run(["git", "-C", str(ordner), *a], check=check,
                              capture_output=True, text=True)
    g("add", "-A")
    if g("diff", "--cached", "--quiet", check=False).returncode == 0:
        return
    g("commit", "-m", nachricht)
    if push:
        for _ in range(3):
            if g("push", "origin", "HEAD:redaktion", check=False).returncode == 0:
                return
            g("pull", "--rebase", "origin", "redaktion", check=False)
        raise RuntimeError("Push des Status-Branches fehlgeschlagen")
