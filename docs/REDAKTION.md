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
- **Keine Musik, keine Fremdbilder.** Jeder Beitrag bekommt ein **eigenes KI-Bild**
  (Betreiberentscheidung 11.11.2026, Leonardo Lucid Origin über Cloudflare).
  **Vor jedem Entwurf `docs/BILDSPRACHE.md` lesen** – sie ist für das Bild verbindlich.
  Das Bild wird im Feld `bild_ki` in Bausteinen beschrieben (art, region, aufbau, lage, motiv,
  umgebung, heute, licht, farbwelt; englisch, konkret, zum Thema wahr, Verbotenes nie nennen,
  auch nicht verneint). Vorlagen für den Aufbau: `docs/bildsprache-muster.json`.
  Aufbau und Farbwelt der letzten Posts stehen in `status.json` (`bild_ki`) – nicht wiederholen.
  **Zusätzlich Pflicht:** `bild` aus `pool/` als Rückfall, falls die Erzeugung scheitert
  (Dateiname nennt die freie Textfläche; nicht eines der zuletzt genutzten).
  Bei eigenem Foto des Betreibers kein `bild_ki`.
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
- `"art": "hinweis"` → der Betreiber hat Stichwörter oder einen Link geschickt: **Hinweis** (unten).

### Hinweis des Betreibers (Stichwörter oder Link per Telegram)

1. Den Hinweis als **Auslöser** behandeln, nie als Quelle – auch wenn es ein Link ist. Worum geht
   es? Gehört es nach §10.2 überhaupt zu den erlaubten Themen?
2. Die **Primärquelle** suchen und öffnen. Erst dann weiter wie in **Stufe 2**: vollständiger
   Entwurf, im Feld **`"hinweis_ref"`** genau die Kennung aus `automat.offen`.
3. Gibt es keine Primärquelle, ist das Thema nicht erlaubt oder nicht belegbar: **keinen Entwurf**,
   sondern `rueckmeldungen/<JJJJ-MM-TT>-<stichwort>.json` anlegen:
   `{"id": "<dateiname ohne .json>", "hinweis_ref": "<kennung>", "text": "zwei, drei Sätze: was gefunden, warum kein Entwurf"}`.
   Der Automat schickt das per Telegram. Committen („Rückmeldung: …“) und pushen.
   Ist der Hinweis offensichtlich kein Themenhinweis (z. B. „danke“), kurze Rückmeldung genauso.
4. **Mit Foto** (`automat.offen` zeigt `eigenes_foto` und `bild_feld`): das Foto mit dem
   Read-Werkzeug **ansehen**. Verwenden, wenn es zum Thema passt und keine Regel verletzt:
   keine erkennbaren Personen (Gesichter), keine Kinder, keine Kennzeichen, bei Blaulicht gar
   keine Menschen, keine fremden Logos oder Plakate im Vordergrund. Dann im Entwurf
   `"bild": "<bild_feld>"` und `"bildtext_lage"` (freie Fläche im Foto: `oben`, `unten`, `mitte`,
   `linksunten` …). `bildtext` darf leer sein, wenn Text das Foto stören würde. Die Caption
   endet dann automatisch mit „Bild: Radio Boarisch.“ statt der KI-Zeile.
   Passt das Foto nicht oder verletzt es eine Regel: Pool-Bild nehmen und in `recherche`
   begründen, warum das Foto nicht verwendet wurde.

### Stufe 2 – Entwurf zum gewählten Thema

1. Zum gewählten Thema den vollständigen Entwurf schreiben: Primärquelle gründlich lesen,
   Fakten dort prüfen, Entwurf nach Raster.
2. `entwuerfe/<JJJJ-MM-TT>-<stichwort>.json` anlegen (Format: `docs/beispiel-entwurf.json`) und
   das Feld **`"thema_ref"`** genau so übernehmen, wie `automat.offen` es ausgibt
   (z. B. `"2026-11-11-themen#2"`). `id` mit dem heutigen Datum.
   Quellenzeile, Signatur, feste Hashtags und „Bild: KI-generiert.“ **nicht** selbst schreiben.
   `bild_ki` nach `docs/BILDSPRACHE.md`, `bild` als Pool-Rückfall (siehe oben).
   Ins Feld `recherche`: Auslöser, Primärquelle mit Datum, Quellenregister-Eintrag.
   **Hashtags** (Betreiberentscheidung 10.11.2026): zusätzlich zu den festen **bis zu 10**, nur
   passende – Ort, Landkreis/Region (z. B. #Landshut #Niederbayern), Thema, Anlass, ggf. der
   offizielle Hashtag des Veranstalters. Keine Allerwelts-Tags (#love #instagood), keine
   Wiederholungen. Ernste Meldungen: keine.
   **Verlinken** (`erwaehnungen`, max. 5): offizielle Konten von Veranstalter, Verein, Behörde,
   Künstler, Ort. Nur, wenn das Instagram-Konto **auf der eigenen Website der Organisation**
   verlinkt ist – diese Seite kommt in `beleg`. Nicht raten. Ohne belegtes Konto nur `name`
   (erscheint dann auf beiden Kanälen als Text). **Nie Privatpersonen, nie Minderjährige**, bei
   Blaulicht höchstens die Behörde.
   Hält das Thema der Prüfung nicht stand (Quelle nicht belastbar, Regelverstoß): keinen Entwurf,
   stattdessen kurz begründen – der Betreiber bekommt dann beim nächsten Themenlauf neue Vorschläge.
3. Prüfen: `python -m automat.pruefen entwuerfe/<id>.json --status /tmp/redaktion` muss **OK** sein.
4. Committen („Entwurf: <thema>“) und pushen. Der Automat schickt den Entwurf per Telegram mit
   Ja/Nein. Veröffentlicht wird nur nach **Ja**.
