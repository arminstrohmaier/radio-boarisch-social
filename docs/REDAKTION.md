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

## Ablauf

1. Regeln lesen (Google Doc, sonst diese Datei).
2. Bisher Gelaufenes ansehen, um Themen und Bilder nicht zu wiederholen:
   `git fetch origin redaktion && git worktree add /tmp/redaktion origin/redaktion`
   (`/tmp/redaktion/status.json`, Ordner `posts/`). Gibt es den Branch noch nicht: überspringen.
3. Thema finden (Websuche, aktuelle Woche, Bayern). Primärquelle suchen und öffnen. Prüfen, ob
   die Fakten dort wirklich stehen. Kein Thema mit Primärquelle gefunden → **keinen Entwurf
   anlegen** und kurz begründen. Lieber kein Post als ein schlechter.
4. Entwurf als `entwuerfe/<id>.json` anlegen. Format: siehe `docs/beispiel-entwurf.json` und
   Kopf von `automat/entwurf.py`. `id` = `JJJJ-MM-TT-stichwort` (heutiges Datum).
   Quellenzeile, Signatur, feste Hashtags und „Bild: KI-generiert.“ **nicht** selbst schreiben –
   der Automat hängt sie an. Ins Feld `recherche`: Auslöser, Primärquelle mit Datum,
   Quellenregister-Eintrag.
5. Prüfen: `pip install -q -r requirements.txt && python -m automat.pruefen entwuerfe/<id>.json --status /tmp/redaktion`
   (ohne `--status`, wenn es den Branch nicht gibt). Muss **OK** ergeben; Hinweise ernst nehmen.
6. Committen und pushen (Branch egal – der Automat holt Entwürfe von allen Branches).
   Commit-Nachricht: `Entwurf: <thema>`. Keine anderen Dateien ändern.

Der Automat schickt den Entwurf dann per Telegram an den Betreiber. Veröffentlicht wird nur nach
**Ja**. Claude veröffentlicht nie selbst.
