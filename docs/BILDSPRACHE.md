# Bildsprache von Radio Boarisch (KI-Bilder)

Verbindlich für jedes KI-Bild eines Beitrags. Grundlage: North Star §5, §8, §12 ·
Strategie §2, §4 · 06-hoererkommunikation §10.3 (Bildregel) und §10.4.
Bei Widerspruch gehen diese Dokumente vor; Änderungen entscheidet der Betreiber.

## 1. Worum es geht

Unsere Bilder zeigen **das Bayern von heute**, so wie es wirklich aussieht – nicht das Bayern
aus der Werbung. Sie sollen sich anfühlen wie ein Foto, das jemand von hier gemacht hat, der
genau hinschaut: ruhig, ehrlich, warm, ein bisschen rau.

Die Leitfragen des North Star gelten auch fürs Bild:

- **Ist es das Bayern von heute?** – Herkunft *und* Gegenwart im selben Bild.
- **Beweist es Bayern, statt es zu behaupten?** – Bayern erkennt man an echten Orten,
  Materialien, Bauweisen, Licht und Alltag, nicht an Symbolen.
- **Ist es echt oder konstruiert?** – lieber ein unscheinbarer, wahrer Moment als ein
  inszeniertes Postkartenmotiv.
- **Passt es zu „Klingt nach Dahoam."?** – vertraut, nicht folkloristisch.

| So ja | So nein |
|---|---|
| verwurzelt: Holz, Putz, Sandstein, Granit, Hopfengarten, Wirtshaussaal | verstaubt: Nostalgie-Filter, Sepia, „wie früher" |
| modern: LED-Licht, E-Bike, Solardach, Kartenterminal, Laptop am Mischpult | beliebig: Stockfoto, das überall sein könnte |
| bayerisch durch Ort, Bauweise, Landschaft, Licht | folkloristisch: Tracht, Dirndl, Lederhosen, Rauten, Blau-Weiß, Edelweiß, Enzian |
| Alltag, Vorbereitung, Ränder eines Ereignisses | touristisches Klischee: Neuschwanstein, Oktoberfest, Maßkrug-Prost |
| natürliches, ehrliches Licht, auch grau und nass | Kitsch: Sonnenuntergang, Alpenglühen, Märchenstimmung, Hochglanz |
| Menschen klein, von hinten, im Schatten | erkennbare Gesichter, Portraits, Kinder |

## 2. Warum wir so genau beschreiben müssen

ChatGPT ergänzt beim Bildermachen viel Kontext selbst. Ein Generator wie **Leonardo Lucid
Origin** (unser Modell über Cloudflare) tut das nicht:

1. **Er malt nur, was dasteht.** „Ein Dorfplatz" wird irgendein Dorfplatz in Europa. Erst
   „langer Marktplatz mit bunten Putzfassaden und gotischem Backsteinturm" wird Niederbayern.
2. **Er versteht keine Verneinung.** „no dirndl" erzeugt eher ein Dirndl, „ohne Schrift"
   eher Schrift. Verbotenes wird deshalb **nie genannt, auch nicht verneint**. Stattdessen
   beschreiben wir positiv, was da ist: „plain unmarked walls", „people seen from behind".
3. **Er versteht Englisch am besten.** Die Bausteine werden englisch geschrieben.
4. **Was zuerst steht, wiegt am meisten.** Darum baut der Automat den Prompt in fester
   Reihenfolge: Bildaufbau → Motiv → Umgebung → Gegenwart → Licht → Farbwelt → Region →
   Themenart → Hausstil → freie Fläche.
5. **Er kennt keine echten Personen und Gebäude zuverlässig** – und soll es auch nicht:
   Wir erfinden kein Foto eines echten Künstlers und täuschen keine echte Kirche vor.

## 3. Die Bausteine im Entwurf (`bild_ki`)

```json
"bild_ki": {
  "art": "brauchtum",
  "region": "niederbayern",
  "aufbau": "aufsicht",
  "lage": "oben",
  "motiv": "…",
  "umgebung": "…",
  "heute": "…",
  "licht": "…",
  "farbwelt": "…"
}
```

| Baustein | Was hinein gehört | Länge |
|---|---|---|
| `art` | Themenart, wählt den passenden Grundton (Liste in 4.) | Schlüssel |
| `region` | Regierungsbezirk des Themas, sonst `bayern` (Liste in 5.) | Schlüssel |
| `aufbau` | Bildaufbau aus dem Katalog (6.) – **nie derselbe wie im letzten Post** | Schlüssel |
| `lage` | wo der Bildtext hinkommt: `oben`, `unten`, `mitte`, `links`, `rechts`, z. B. `linksunten` | Schlüssel |
| `motiv` | **Das eine Hauptmotiv**, konkret und gegenständlich: was, wie viele, in welchem Zustand | 25–400 |
| `umgebung` | **Der Ort**, regionaltypisch genau: Bauweise, Material, Landschaft | 20–300 |
| `heute` | **Mindestens ein Gegenwartsdetail**, beiläufig: LED, E-Bike, Solardach, Smartphone, Kartenterminal | 15–250 |
| `licht` | Jahreszeit, Tageszeit, Wetter, Lichtquelle – passend zum Termin des Themas | 10–200 |
| `farbwelt` | 2–4 Farben, **eigene Farbwelt je Post** (nicht wie in den letzten 3 Posts) | 10–160 |

Hausstil, Menschenregel und freie Textfläche setzt der Automat selbst dazu
(`automat/bildsprache.py`). Der fertige Prompt liegt nach dem Senden im Status-Branch unter
`posts/<id>/ki-prompt.txt`.

### Schreibregeln

- **Konkret statt allgemein.** Nicht „festive market", sondern „simple wooden stalls,
  shutters folded up, fir branches over the counter".
- **Zum Thema wahr.** Termin im November → Novemberlicht. Ort in Unterfranken → Weinberge,
  Sandstein. Ein Thema in der Oberpfalz bekommt keine Alpen.
- **Echte Orte nur andeuten.** Nicht „Landshuter Martinskirche", sondern „a tall Gothic brick
  church tower at the end of a long market square". Kein erkennbares Wahrzeichen nachbauen.
- **Echte Personen nie.** Bei Künstlern zeigen wir Instrument, Bühne, Proberaum – nicht die
  Person. Musiker höchstens als Silhouette von hinten.
- **Menschen nur, wenn sie das Bild brauchen** – klein, von hinten, Gesicht abgewandt,
  Alltagskleidung, nur Erwachsene. Bei `blaulicht` und `nachruf` setzt der Automat das Bild
  menschenleer (Betreiberentscheidung vom 11.11.2026).
- **Bei Nahaufnahmen (`detail`) nur Hände und Unterarme** – sonst malt der Generator das
  Gesicht halb mit ins Bild (so geschehen im Christkindlmarkt-Test). Der Automat setzt das
  beim Aufbau `detail` selbst dazu.
- **Den Moment am Rand wählen:** Aufbau, Vorbereitung, kurz vor Beginn, danach. Das wirkt
  echt und vermeidet Gedränge mit Gesichtern.
- **Nicht nennen, auch nicht verneint:** Dirndl, Lederhosen, Tracht/costume, Edelweiß,
  Enzian, Blau-Weiß, Rauten, Fahnen/Banner, Logos/Marken, Schrift/Schilder/Plakate/Etiketten,
  Kennzeichen, Gesichter/Portrait/Lächeln, Kinder, Neuschwanstein, Oktoberfest, postcard,
  picturesque, idyllic, romantic, fairytale – und keine Wörter wie *no, not, without*.
  Die Prüfung lehnt solche Entwürfe ab.
- **Vorsicht (Hinweis an den Betreiber):** Maßkrug, Brezn, Kühe, Schloss/Kloster,
  Maibaum (nur als geschälter Stamm, ohne Bemalung), Sonnenauf-/-untergang, golden hour,
  dramatic, vibrant, glowing.

### Bayerische Dinge genau benennen (Glossar)

Der Generator kennt bayerische Begriffe nicht oder verwechselt sie. Ein „beer garden" wird
schnell ein amerikanischer Picknicktisch (so geschehen im ersten Test). Darum beschreiben,
wie das Ding aussieht:

| Gemeint | So beschreiben |
|---|---|
| Bierzeltgarnitur | long narrow folding beer tables with separate folding benches, bare wooden tops on metal legs |
| Biergarten | gravel ground under old chestnut trees, rows of folding beer tables and benches |
| Wirtshaussaal | the hall of a village inn, wooden floorboards, plastered vaulted or beamed ceiling, small stage at one end |
| Gaststube | low wood-panelled room, scrubbed wooden tables, corner bench along the wall, tiled stove |
| Kachelofen | large tiled stove of glazed ceramic tiles with a bench around it |
| Christkindlmarkt-Bude | small wooden market stall with a pitched roof and folding shutters |
| Dult / Volksfest | fairground with a Ferris wheel, carousels and food stalls at the edge of town |
| Blaskapelle (ohne Personen) | tuba, flugelhorn, tenor horn, trumpets and a bass drum resting on chairs |
| Hopfengarten | very tall wooden poles about seven metres high, three times the height of a tractor, carrying a high grid of wires overhead; hop bines climbing up on strings (nach der Ernte: bare poles and slack strings) |
| Stadl | large old timber barn with weathered vertical boards |
| Zwiebelturm | baroque church tower with an onion-shaped dome |
| Maibaum | tall peeled spruce trunk, bare pale wood (ohne Bemalung und Schilder) |
| Sandsteinmauer (Franken) | walls of large rough-cut blocks of red sandstone masonry |
| Marktplatz (Niederbayern) | long street-like market square lined with colourful plastered facades |

### Dinge, die Schrift mitbringen

Manche Gegenstände malt der Generator fast immer mit Kritzelschrift: Tafeln, Speisekarten,
Bildschirme, Zeitungen, Bücher, Kartons, Schaufenster. Möglichst weglassen; Bildschirme
„closed" oder „switched off" beschreiben. Die Prüfung gibt dazu einen Hinweis.

### Straßen bringen Verkehrszeichen mit

Bei Straßenmotiven malt der Generator oft Verkehrsschilder dazu (so geschehen im
Blaulicht-Test, unleserlich). Lieber Feldweg, Nebenstraße, Brücke oder Ortsrand wählen und
„narrow country lane" statt „road" schreiben.

### Licht ohne Kitsch

„Low sun", „sun filtered through leaves" oder Gegenlicht erzeugen oft einen orangen
Lens-Flare (so geschehen im ersten Test). Lieber bedeckt, diffus, Dämmerung, Lampenlicht.

## 4. Themenarten (`art`)

| `art` | Grundton, den der Automat dazusetzt | Menschen |
|---|---|---|
| `musik` | echte Bühne oder Proberaum, Instrumente als Gegenstände, Kabel, Bühnenlicht | Silhouetten, von hinten |
| `veranstaltung` | das Ereignis an seinen Rändern: Aufbau, leere Bänke, Licht geht an | klein, von hinten |
| `brauchtum` | gelebter Brauch heute, erzählt über Hände, Material, Werkzeug, Vorbereitung | Alltagskleidung, von hinten |
| `kultur` | echter Spielort, Werkstatt, Ausstellung, zeitgemäß und benutzt | klein, von hinten |
| `meldung` | ruhige, neutrale, erkennbar bayerische Szene zum Thema | klein, von hinten |
| `sender` | Radio heute: kleines Studio, Küchentisch mit Radio, Kopfhörer, Mikrofon | – |
| `blaulicht` | ruhiger, neutraler Ort der Region, gewöhnlicher Tag, keine Einsatzszene | **keine** |
| `nachruf` | still, würdig: ein bedeutungsvoller Gegenstand oder ein vertrauter leerer Ort, gedämpfte Farben | **keine** |

## 5. Regionen (`region`)

Kurzer Charakter, den der Automat ergänzt. Das Konkrete gehört in `umgebung`.

| `region` | Charakter |
|---|---|
| `oberbayern` | Voralpenland, flache weite Dächer, weißer Putz, schlichte Holzbalkone |
| `niederbayern` | sanfte Hügel, Märkte mit langen Plätzen, bunte Putzfassaden, gotischer Backstein |
| `oberpfalz` | Fichtenwald, Granit, Weiher, schlichte Putzhäuser mit steilen Dächern |
| `oberfranken` | Fachwerk, Sandstein, Kalkfelsen, enge bewaldete Täler |
| `mittelfranken` | roter und gelber Sandstein, Fachwerk, Seenland, Heide |
| `unterfranken` | Weinberge in Terrassen, Barock-Sandstein, Fachwerk-Weindörfer |
| `schwaben` | weite Flussebenen, Putzbauten mit Treppengiebeln, grüne Allgäuer Hügel |
| `bayern` | nichts – nur wenn das Thema keinem Bezirk zugeordnet ist |

## 6. Bildaufbau (`aufbau`)

Jeder Post sieht anders aus als der vorige (06 §10.3). Darum wechselt der Aufbau.

| `aufbau` | Wirkung |
|---|---|
| `weite` | Totale, Motiv klein in großem Raum – Landschaft, Ortsbild |
| `mittel` | Halbtotale auf Augenhöhe – Standard für Orte und Dinge |
| `detail` | Nahaufnahme, Hintergrund weich – Hände, Material, Instrument |
| `rahmen` | durch Tür, Fenster oder Zweige hindurch – Nähe, Blick „von drinnen" |
| `diagonale` | Linie führt aus der Ecke ins Bild – Straße, Bankreihe, Ufer |
| `zentral` | symmetrisch, Fluchtpunkt in der Mitte – Bühne, Allee, Kirchenschiff |
| `aufsicht` | leicht von oben – Markt, Platz, Tisch |
| `untersicht` | knapp über dem Boden nach oben – Mikrofon, Baum, Turm |
| `gegenlicht` | Motiv vor dem Licht, weicher Kontrast – Stimmung, Nachruf |

## 7. Freie Fläche für den Bildtext (`lage`)

Der Bildtext kommt erst danach vom Automaten aufs Bild. Damit er lesbar ist, braucht das Bild
an dieser Stelle **Ruhe**: Himmel, Wand, Wasser, Wiese, Unschärfe. Das Motiv steht dann im
anderen Teil des Bildes. Der Automat schreibt die Fläche selbst in den Prompt.

## 8. Mustermotive

`docs/bildsprache-muster.json` enthält je Themenart ein vollständiges Beispiel
(Konzert, Volksfest, Christkindlmarkt, Theater, Landschaftsmeldung, Sender, Blaulicht,
Nachruf). Sie sind Vorlagen für den Aufbau eines Motivs, **nicht zum Kopieren**: Jedes Thema
bekommt sein eigenes, wahres Motiv.

## 9. Was der Betreiber sieht

In Telegram steht unter dem Bild: „Bild: eigenes KI-Bild (lucid-origin) · Themenart · Region ·
Aufbau". Gefällt das Bild nicht, **Nein** drücken – dann kommt kein Post. Scheitert die
Erzeugung, kommt automatisch ein Pool-Bild mit dem Grund. Die Caption endet immer mit
„Bild: KI-generiert."
