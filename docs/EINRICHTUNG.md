# Einrichtung der Halbautomatik (D-083)

Alles kostenlos: Telegram-Bot, GitHub Actions (öffentliches Repo), Meta Graph API.
**Secrets nie in einen Chat kopieren** – sie werden nur an den hier genannten Stellen eingetragen.

Wo GitHub-Secrets eingetragen werden (gilt für alle Schritte unten):

1. https://github.com/arminstrohmaier/radio-boarisch-social öffnen
2. oben **Settings** → links **Secrets and variables** → **Actions**
3. Reiter **Secrets** → grüner Knopf **New repository secret**
4. **Name** genau wie angegeben (Großbuchstaben), **Secret** = der Wert → **Add secret**

GitHub zeigt den Wert danach nie wieder an, auch nicht in den Protokollen.

---

## Teil A – Telegram (zuerst)

### A1. Bot anlegen (Handy oder Telegram Desktop)

1. In Telegram nach **@BotFather** suchen (blauer Haken) und öffnen → **Start**.
2. `/newbot` senden.
3. Name eingeben, z. B. `Radio Boarisch Automat`.
4. Benutzernamen eingeben, muss auf `bot` enden, z. B. `radioboarisch_automat_bot`
   (falls vergeben: anderen wählen).
5. BotFather antwortet mit einem **Token** (sieht aus wie `1234567890:AAH…`).
   Gedrückt halten → kopieren. **Nicht** weitergeben.

### A2. Token in GitHub eintragen

Secret anlegen (siehe oben): Name **`TELEGRAM_BOT_TOKEN`**, Wert = Token aus A1.

### A3. Chat-ID holen

1. In Telegram deinen neuen Bot öffnen (Link steht in der BotFather-Nachricht) → **Start** drücken
   (sendet `/start`).
2. Auf GitHub: Reiter **Actions** → links **Automat** → rechts **Run workflow** → **Run workflow**.
   (Sonst passiert es automatisch innerhalb von etwa 10 Minuten.)
3. Der Bot antwortet dir in Telegram: „Deine Chat-ID ist: 123456789“.
4. Secret anlegen: Name **`TELEGRAM_CHAT_ID`**, Wert = diese Zahl.

Ab jetzt reagiert der Bot nur noch auf diesen einen Chat. Knöpfe aus anderen Chats werden ignoriert.

### A4. Test

1. **Actions** → **Automat** → **Run workflow** → Haken bei **Testentwurf** → **Run workflow**.
2. Nach 1–2 Minuten kommt in Telegram ein Bild und darunter der Entwurf mit
   **✅ Ja, veröffentlichen** / **❌ Nein, verwerfen**. Der Test ist mit 🧪 markiert.
3. Einen Knopf drücken. Beim nächsten Durchlauf (spätestens ca. 10–15 Minuten, sofort mit
   **Run workflow**) kommt die Bestätigung. **Beim Test wird nie etwas veröffentlicht.**

> Hinweis: Die Knöpfe werden alle 10 Minuten abgefragt, nicht in Echtzeit. GitHub startet
> geplante Läufe manchmal ein paar Minuten später – das ist normal.

---

## Teil B – Meta (Instagram + Facebook)

Solange Teil B fehlt, gilt: Bei **Ja** schickt der Bot den Hinweis „bitte von Hand posten“
(wie in den Probeläufen, 06 §10.6). Es wird nichts automatisch veröffentlicht.

### B0. Voraussetzungen

- Das Instagram-Konto von Radio Boarisch ist ein **Professional-Konto** (Business oder Creator):
  Instagram-App → Profil → ☰ → *Konto-Typ und Tools* → *Zu professionellem Konto wechseln*.
- Es ist mit der **Facebook-Seite** von Radio Boarisch verknüpft:
  Facebook-Seite → *Einstellungen* → *Verknüpfte Konten* → *Instagram* → verbinden.
- Du bist Admin der Facebook-Seite.

### B1. Meta-App anlegen (einmalig, kostenlos)

1. https://developers.facebook.com → oben rechts **Loslegen** / **Meine Apps** (mit deinem
   Facebook-Konto anmelden, ggf. als Entwickler registrieren – kostenlos).
2. **App erstellen** → Name z. B. `Radio Boarisch Automat`.
3. Anwendungsfall wählen: **„Alles auf deiner Seite verwalten“** (Manage everything on your Page)
   und – falls angeboten – zusätzlich **„Nachrichten und Inhalte auf Instagram verwalten“**.
   (Heißt das Menü anders: Typ **Business** wählen.)
4. Die App bleibt im **Entwicklungsmodus**. Das reicht, weil nur auf deine eigene Seite und dein
   eigenes Instagram gepostet wird – keine App-Prüfung durch Meta nötig.

### B2. Zugriffstoken erzeugen

1. https://developers.facebook.com/tools/explorer öffnen (Graph API Explorer).
2. Rechts bei **Meta App** deine App wählen.
3. Bei **Benutzer oder Seite** → **User Token** → unter **Berechtigungen** diese hinzufügen:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `instagram_basic`, `instagram_content_publish`, `business_management`
4. **Generate Access Token** → im Facebook-Fenster deine Seite **und** dein Instagram-Konto
   auswählen → zustimmen.
5. Das Token im Feld oben kopieren → https://developers.facebook.com/tools/debug/accesstoken
   öffnen → einfügen → **Debug** → ganz unten **Extend Access Token** → das neue, lange Token
   kopieren (gilt 60 Tage).
6. Zurück im Graph API Explorer: das lange Token oben ins Feld **Access Token** einfügen und
   diese Abfrage ausführen (Feld neben **GET**):

   ```
   me/accounts?fields=name,id,access_token,instagram_business_account
   ```

   → **Submit**. In der Antwort bei deiner Seite stehen:
   - `access_token` → das **Seiten-Token** (läuft nicht ab, weil aus dem langen Token erzeugt)
   - `id` → die **Seiten-ID**
   - `instagram_business_account` → `id` → die **Instagram-ID**
7. Kontrolle: Seiten-Token im Access Token Debugger prüfen – bei **Läuft ab** muss **Nie** stehen.

### B3. In GitHub eintragen

| Name | Wert |
|---|---|
| `META_PAGE_TOKEN` | Seiten-Token (`access_token`) |
| `META_PAGE_ID` | Seiten-ID (`id`) |
| `META_IG_USER_ID` | Instagram-ID (`instagram_business_account.id`) |

Fehlt `META_PAGE_ID`, wird nur auf Instagram gepostet; fehlt `META_IG_USER_ID`, nur auf Facebook.

Optional (kein Secret): unter **Variables** → `META_API_VERSION`, z. B. `v27.0`. Nur nötig, wenn
Meta die voreingestellte Version abschaltet (der Bot meldet dann einen Fehler).

### B3a. Zugang prüfen (ohne zu posten)

**Actions** → **Automat** → **Run workflow** → Haken bei **Meta-Zugang pruefen** → **Run workflow**.
Nach 1–2 Minuten schickt dir der Bot in Telegram das Ergebnis: Token-Typ, Ablaufdatum („nie“),
Berechtigungen, Name der Seite, Instagram-Konto. Der Token selbst wird nirgends angezeigt.
Ein schon vorhandener Token, der nicht abläuft (Seiten-Token oder System-User-Token aus dem
Business-Manager), funktioniert auch – die Prüfung zeigt, ob er passt.

### B4. Erster echter Post

Der nächste Entwurf, den du mit **Ja** freigibst, wird veröffentlicht. Der Bot antwortet mit den
Links zu Instagram und Facebook. Bei einem Fehler kommt die Meldung mit **🔁 Nochmal versuchen**;
ein Kanal, der schon geklappt hat, wird dabei nicht doppelt gepostet.

**KI-Label:** Die Caption endet immer mit „Bild: KI-generiert.“ Das Instagram-eigene KI-Label
lässt sich über die Schnittstelle nicht setzen (06 §10.3: nur „wenn die App es anbietet“).

---

## Wenn etwas nicht geht

- **Actions** → **Automat** → letzten Lauf öffnen → **Durchlauf** zeigt, was passiert ist.
  Tokens erscheinen dort nie.
- Token neu erzeugt? Einfach das Secret mit gleichem Namen überschreiben (**Update secret**).
- Bot hängt? In Telegram `/status` an den Bot schicken – er listet die offenen Entwürfe.
- GitHub schaltet geplante Abläufe nach 60 Tagen ohne Aktivität im Repo ab. Dann im Reiter
  **Actions** den Workflow **Automat** wieder aktivieren (**Enable workflow**).

---

## Teil C – Taktgeber: nicht mehr nötig

Der Automat läuft seit 11.11.2026 als Kette von Dauerläufen: Jeder Lauf lauscht bis zu
340 Minuten auf Telegram (Klicks werden in Sekunden verarbeitet) und startet am Ende selbst
seinen Nachfolger. Ein externer Taktgeber (cron-job.org) wird nicht gebraucht.

Kontrolle: **Actions** → **Automat** – dort sollte immer ein Lauf „in progress“ sein.
Reißt die Kette ab (z. B. nach einem Fehler), startet die stündliche Claude-Runde sie neu.
Von Hand: **Run workflow** → bei **dauer** `340` eintragen → **Run workflow**.
