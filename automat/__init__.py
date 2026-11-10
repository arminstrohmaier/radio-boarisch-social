"""Halbautomatik fuer Instagram und Facebook von Radio Boarisch (D-083).

Ablauf: Claude legt einen Entwurf an (entwuerfe/<id>.json) -> der Automat
rendert das Bild, schickt Bild und Caption per Telegram mit Ja/Nein-Button
an den Betreiber -> bei "Ja" Veroeffentlichung ueber die Meta Graph API,
bei "Nein" verworfen, ohne Antwort passiert nichts.
"""
