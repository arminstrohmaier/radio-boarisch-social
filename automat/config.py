"""Konfiguration. Secrets kommen ausschliesslich aus Umgebungsvariablen
(GitHub Actions Secrets), nie aus Dateien im Repo."""
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POOL_DIR = REPO_ROOT / "pool"
FONT_PATH = REPO_ROOT / "assets" / "fonts" / "DejaVuSans-Bold.ttf"

SIGNATUR = "Radio Boarisch · Klingt nach Dahoam."
FESTE_HASHTAGS = ["#RadioBoarisch", "#KlingtNachDahoam"]
KI_ZEILE = "Bild: KI-generiert."
EIGEN_ZEILE = "Bild: Radio Boarisch."   # eigenes Foto des Betreibers (Betreiberentscheidung 10.11.2026)
EIGEN_PREFIX = "eigen:"

# Die Pool-Bilder sind vorab erstellt und KI-generiert (06 §10.3).
POOL_IST_KI = True


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


@dataclass
class Settings:
    telegram_token: str
    telegram_chat_id: str
    meta_token: str
    meta_page_id: str
    meta_ig_user_id: str
    meta_api_version: str
    public_base_url: str  # oeffentliche URL des Status-Branches (fuer image_url)

    @property
    def telegram_ok(self) -> bool:
        return bool(self.telegram_token)

    @property
    def meta_ok(self) -> bool:
        return bool(self.meta_token and (self.meta_page_id or self.meta_ig_user_id))

    @classmethod
    def from_env(cls) -> "Settings":
        repo = _env("GITHUB_REPOSITORY") or "arminstrohmaier/radio-boarisch-social"
        branch = _env("STATUS_BRANCH") or "redaktion"
        return cls(
            telegram_token=_env("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
            meta_token=_env("META_PAGE_TOKEN"),
            meta_page_id=_env("META_PAGE_ID"),
            meta_ig_user_id=_env("META_IG_USER_ID"),
            meta_api_version=_env("META_API_VERSION") or "v27.0",
            public_base_url=_env("PUBLIC_BASE_URL")
            or f"https://raw.githubusercontent.com/{repo}/{branch}",
        )
