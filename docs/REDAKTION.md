# Redaktionsauftrag für Claude (R9, Instagram/Facebook)

Diese Anweisung liest die geplante Claude-Sitzung, die dreimal pro Woche einen Entwurf anlegt.

## Verbindliche Regeln

Maßgeblich ist **06-hoererkommunikation, Abschnitte 6, 7 und 10** (Google Doc
„06-hoererkommunikation“, ID `1JC7bsYUItT6OwEVf9MoYc5ic-CQuAYevYkban9NV14s`).
Ist der Google-Drive-Zugang verfügbar, das Dokument **zuerst lesen** – es geht dieser Datei vor.
Kurzfassung (Stand V1.2, 28.10.2026, mit Betreiberentscheidungen bis 10.11.2026):

- **Themen:** Bayern mit Bezug zu Musik, Brauchtum, Veranstaltungen, Kultur; Sendermaterial;
  Blaulicht aus Bayern; gelegentlich interessante, nicht polarisierende Meldungen aus Bayern;
  Nachrufe auf bayerische Persönlichkeiten. **Keine Tagespolitik, nichts Polarisierendes.**
- **Quellen:** dpa, BR, Antenne Bayern u. a. sind **nur Auslöser, nie Quelle**. Grundlage ist
  ausschließlich eine **Primärquelle** (Pressemitteilung von Veranstalter, Behörde oder Künstler,
  presseportal.de). Ohne Primärquelle fällt das Thema aus. Quellenregister in der Anlage des
  Dokuments beachten (Standard: nur Tatsachen, eigene Worte, kein Foto, Primärquelle genannt).
- **Nur reales Material, keine unbelegten Zahlen**, keine übernommenen Formulierungen.
- **Keine Zusagen** (06 §7): kein Airplay, keine Rotation, kein Interview usw. Einen Künstler zu
  nennen ist erlaubt.
- **Blaulicht:** keine Namen, keine erkennbaren Personen, keine Minderjährigen, keine
  Verdachtsberichterstattung, keine Opferdetails.
- **Todesfälle und ernste Meldungen** (`"ernst": true`): nur bestätigte Tatsachen, keine
  Spekulation, ernster Ton, **ohne Dialekt, ohne Emojis, ohne Hashtags**.
- **Ton sonst lebendig:** eine Zeile, ein Emoji als Gliederung; bayerische Anrede und Wendungen
  („Servus“, „grias eich“), lesbar, kein künstlicher Dialekt; kurze Aufforderung am Schluss.
  Keine Superlative über das eigene Programm, keine Ausrufezeichenketten.
- **Keine Musik, keine Fremdbilder.** Bild nur aus `pool/`; Dateiname nennt die freie Textfläche.
  Bild passend zur Stimmung wählen und **nicht** eines der zuletzt genutzten.
- **Takt:** 3 Posts pro Woche. Pro Lauf **genau ein** Entwurf.

## Ablauf in zwei Stufen (Betreiberentscheidung vom 10.11.2026)

Gemeinsam für beide Stufen:
- Regeln lesen (Google Doc, sonst diese Datei).
- Status holen: `git fetch origin redaktion && git worktree add --detach /tmp/redaktion origin/redaktion`
  (`/tmp/redaktion/status.json`: bisherige Posts, Bilder, Themen). Ist der Branch nicht da: überspringen.
- Committen und pushen auf den Arbeitsbranch (der Automat holt Dateien von allen Branches).
  Keine anderen Dateien ändern, nie nach main, nie selbst veröffentlichen.

### Stufe 1 – Themenlauf (Mo/Mi/Fr früh, außerdem auf Anforderung per /themen)

1. **Drei** verschiedene, aktuelle Themen aus Bayern nach §10.2 suchen. Nicht dieselben wie in
   den letzten Posts oder Themenvorschlägen (`status.json`).
2. Für jedes Thema eine **Primärquelle** finden und kurz öffnen, um zu sehen, dass es sie gibt
   und dass das Thema dort steht. Noch **nicht** ausrecherchieren oder formulieren.
   Ohne Primärquelle fällt ein Thema weg. Findest du weniger als drei, schick weniger; findest du
   keins, lege nichts an und begründe kurz.
3. `themen/<JJJJ-MM-TT>-themen.json` anlegen (gibt es die Datei für heute schon:
   `…-themen-2.json`, `…-themen-3.json` usw., `id` entsprechend) (Format: Kopf von `automat/themen.py`):
   je Thema `titel` (kurz), `worum` (ein bis zwei Sätze), `quelle` {name, url}, `ernst` (true/false).
4. Committen („Themen: <Datum>“) und pushen. Der Automat schickt die Themen per Telegram mit den
   Knöpfen 1 / 2 / 3 / Keins.

### Stündliche Runde (6:37–22:37 Uhr)

`python -m automat.offen --status /tmp/redaktion` ausführen. Ausgabe `[]`: **nichts zu tun,
sofort beenden** (keine Recherche, kein Commit, keine lange Antwort). Sonst je Eintrag:
- `"art": "themenlauf"` → der Betreiber hat per `/themen` Vorschläge angefordert: **Stufe 1** ausführen.
- `"art": "entwurf"` → **Stufe 2** für das gewählte Thema.

### Stufe 2 – Entwurf zum gewählten Thema

1. Zum gewählten Thema den vollständigen Entwurf schreiben: Primärquelle gründlich lesen,
   Fakten dort prüfen, Entwurf nach Raster.
2. `entwuerfe/<JJJJ-MM-TT>-<stichwort>.json` anlegen (Format: `docs/beispiel-entwurf.json`) und
   das Feld **`"thema_ref"`** genau so übernehmen, wie `automat.offen` es ausgibt
   (z. B. `"2026-11-11-themen#2"`). `id` mit dem heutigen Datum.
   Quellenzeile, Signatur, feste Hashtags und „Bild: KI-generiert.“ **nicht** selbst schreiben.
   Ins Feld `recherche`: Auslöser, Primärquelle mit Datum, Quellenregister-Eintrag.
   Hält das Thema der Prüfung nicht stand (Quelle nicht belastbar, Regelverstoß): keinen Entwurf,
   stattdessen kurz begründen – der Betreiber bekommt dann beim nächsten Themenlauf neue Vorschläge.
3. Prüfen: `python -m automat.pruefen entwuerfe/<id>.json --status /tmp/redaktion` muss **OK** sein.
4. Committen („Entwurf: <thema>“) und pushen. Der Automat schickt den Entwurf per Telegram mit
   Ja/Nein. Veröffentlicht wird nur nach **Ja**.
