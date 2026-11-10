# radio-boarisch-social
Redaktionsautomat fuer Instagram und Facebook von Radio Boarisch (Klingt nach Dahoam)

## Halbautomatik (D-083, LOP 127)

```
Claude (geplante Sitzung, 3x/Woche)      GitHub Actions "Automat" (alle 10 Min.)          Betreiber
  recherchiert nach 06 §10        ──►  Entwurf pruefen, Bild aus pool/ mit Bildtext  ──►  Telegram:
  entwuerfe/<id>.json pushen            rendern, per Telegram schicken                    ✅ Ja / ❌ Nein
                                        Ja   ──► Meta Graph API: Instagram + Facebook  ◄──┘
                                        Nein ──► verworfen
                                        keine Antwort ──► nichts passiert
```

- `automat/` – Code (Pruefung, Bild, Telegram, Meta, Ablauf)
- `pool/` – Bilder; Dateiname nennt die freie Textflaeche
- `docs/EINRICHTUNG.md` – **Schritt-fuer-Schritt: Telegram-Bot und Meta-Zugang einrichten**
- `docs/REDAKTION.md` – Auftrag fuer die Claude-Entwurfssitzung
- `docs/beispiel-entwurf.json` – Formatvorlage (erfundene Daten)
- Branch `redaktion` – Zustand des Automaten und gerenderte Bilder (wird vom Automaten gepflegt)

Lokal pruefen: `pip install -r requirements.txt pytest && python -m pytest -q`
Einen Entwurf pruefen: `python -m automat.pruefen entwuerfe/<id>.json --bild /tmp/vorschau.jpg`
