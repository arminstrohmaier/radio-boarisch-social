"""Veroeffentlichung ueber die Meta Graph API (kostenlos).

Instagram (Content Publishing API):
  1. POST /{ig-user-id}/media          image_url, caption  -> Container-ID
  2. GET  /{container-id}?fields=status_code  bis FINISHED
  3. POST /{ig-user-id}/media_publish  creation_id         -> Media-ID
Facebook-Seite:
  POST /{page-id}/photos  url, message                    -> Post-ID

Beides mit einem Seiten-Zugriffstoken (Page Access Token) der Facebook-Seite,
mit der das Instagram-Business-/Creator-Konto verknuepft ist.
"""
from __future__ import annotations

import time

import requests


class MetaFehler(RuntimeError):
    pass


class Meta:
    def __init__(self, token: str, version: str = "v27.0", timeout: int = 60, warte=time.sleep):
        self._token = token
        self._basis = f"https://graph.facebook.com/{version}/"
        self._timeout = timeout
        self._warte = warte

    def _req(self, methode: str, pfad: str, token: str | None = None, **params):
        params["access_token"] = token or self._token
        try:
            if methode == "GET":
                r = requests.get(self._basis + pfad, params=params, timeout=self._timeout)
            else:
                r = requests.post(self._basis + pfad, data=params, timeout=self._timeout)
        except requests.RequestException as ex:
            raise MetaFehler(f"{pfad}: Netzwerkfehler {type(ex).__name__}") from None
        try:
            daten = r.json()
        except ValueError:
            raise MetaFehler(f"{pfad}: HTTP {r.status_code}") from None
        if "error" in daten:
            e = daten["error"]
            raise MetaFehler(f"{pfad}: {e.get('message')} (code {e.get('code')}/{e.get('error_subcode')})")
        return daten

    def instagram(self, ig_user_id: str, image_url: str, caption: str) -> dict:
        c = self._req("POST", f"{ig_user_id}/media", image_url=image_url, caption=caption)
        cid = c["id"]
        for _ in range(30):
            s = self._req("GET", cid, fields="status_code").get("status_code")
            if s == "FINISHED":
                break
            if s in ("ERROR", "EXPIRED"):
                raise MetaFehler(f"Instagram-Container {s}")
            self._warte(5)
        else:
            raise MetaFehler("Instagram-Container nicht rechtzeitig fertig")
        m = self._req("POST", f"{ig_user_id}/media_publish", creation_id=cid)
        mid = m["id"]
        link = ""
        try:
            link = self._req("GET", mid, fields="permalink").get("permalink", "")
        except MetaFehler:
            pass
        return {"id": mid, "link": link}

    def seiten_token(self, page_id: str) -> str:
        """Seiten-Token aus einem Nutzer- oder System-User-Token ableiten."""
        t = self._req("GET", page_id, fields="access_token").get("access_token")
        if not t:
            raise MetaFehler("kein access_token fuer die Seite (Admin-Rechte/Berechtigungen?)")
        return t

    def facebook(self, page_id: str, image_url: str, caption: str) -> dict:
        try:
            token = self.seiten_token(page_id)
        except MetaFehler:
            token = None  # ist vermutlich schon ein Seiten-Token
        r = self._req("POST", f"{page_id}/photos", token=token, url=image_url, message=caption,
                      published="true")
        pid = r.get("post_id") or r.get("id")
        return {"id": pid, "link": f"https://www.facebook.com/{pid}" if pid else ""}
