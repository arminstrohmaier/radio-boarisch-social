import json
from pathlib import Path

import pytest

from automat import entwurf as E, lauf
from automat.config import Settings
from automat.meta import MetaFehler
from automat.status import Status

ORIGINAL_VERALTET = lauf._veraltet


@pytest.fixture(autouse=True)
def nie_veraltet(monkeypatch):
    # Ablauftests sollen nicht vom heutigen Datum abhaengen
    monkeypatch.setattr(lauf, "_veraltet", lambda pid, heute=None: False)


BEISPIEL = {
    "id": "2026-11-12-christkindlmarkt-landshut",
    "thema": "Christkindlmarkt Landshut öffnet",
    "ernst": False,
    "hook": "🎄 Servus Landshut, da Christkindlmarkt sperrt auf!",
    "text": "📅 Ab 24. November auf der Freyung.\n🕯️ Täglich ab 11 Uhr.",
    "aufforderung": "👉 Wer geht hin? Schreibt's uns!",
    "bildtext": "Christkindlmarkt Landshut ab 24. November",
    "bild": "05_text-oben.jpg",
    "quelle": {"name": "Stadt Landshut", "url": "https://www.landshut.de/pm"},
    "hashtags": ["Landshut", "#Christkindlmarkt"],
    "recherche": "Ausloeser BR, Primaerquelle PM der Stadt.",
}


def test_caption_raster():
    c = E.caption(BEISPIEL)
    assert c.startswith("🎄 Servus Landshut")
    assert "Quelle: Stadt Landshut, https://www.landshut.de/pm" in c
    assert "Radio Boarisch · Klingt nach Dahoam." in c
    assert "#RadioBoarisch #KlingtNachDahoam #Landshut #Christkindlmarkt" in c
    assert c.endswith("Bild: KI-generiert.")
    assert E.pruefen(BEISPIEL).ok


def test_ernst_ohne_emoji_dialekt_hashtags():
    e = dict(BEISPIEL, ernst=True, hashtags=[], aufforderung="",
             hook="Der Volksmusikant X ist gestorben.", text="Er wurde 80 Jahre alt.")
    assert E.pruefen(e).ok
    c = E.caption(e)
    assert "#" not in c and not E.EMOJI_RE.search(c)
    e2 = dict(e, hook="Servus, traurige Nachricht 😢")
    f = E.pruefen(e2).fehler
    assert any("Emojis" in x for x in f) and any("Dialekt" in x for x in f)


@pytest.mark.parametrize("url", ["https://www.br.de/nachrichten/x", "https://dpa.de/y",
                                  "https://www.antenne.de/z"])
def test_ausloeser_nie_quelle(url):
    e = dict(BEISPIEL, quelle={"name": "x", "url": url})
    assert not E.pruefen(e).ok


def test_bild_nicht_wiederholen_und_existiert():
    assert not E.pruefen(BEISPIEL, ["05_text-oben.jpg"]).ok
    assert not E.pruefen(dict(BEISPIEL, bild="99_gibts-nicht.jpg")).ok


def test_keine_zusage_und_keine_eigene_quellenzeile():
    assert not E.pruefen(dict(BEISPIEL, text="Der Titel ist in unserer Rotation.")).ok
    assert not E.pruefen(dict(BEISPIEL, text="Quelle: irgendwas")).ok


# ------------------------------------------------------------ Ablauf mit Attrappen

class FakeTG:
    def __init__(self):
        self.gesendet, self.queue, self.msg_id, self.entfernt, self.acks = [], [], 100, [], []

    def updates(self, offset):
        self.acks.append(offset)
        return [u for u in self.queue if offset is None or u["update_id"] >= offset]

    def foto(self, chat, pfad, caption=""):
        assert Path(pfad).is_file()
        self.msg_id += 1
        self.gesendet.append(("foto", chat, caption))
        return {"message_id": self.msg_id}

    def text(self, chat, text, knoepfe=None, antwort_auf=None):
        self.msg_id += 1
        self.gesendet.append(("text", chat, text, knoepfe))
        return {"message_id": self.msg_id}

    def knoepfe_weg(self, chat, mid):
        self.entfernt.append(mid)

    def callback_antwort(self, cid, text=""):
        pass

    def klick(self, uid, data, chat="42", msg=102):
        self.queue.append({"update_id": uid, "callback_query": {
            "id": f"cb{uid}", "data": data, "from": {"id": int(chat)},
            "message": {"message_id": msg, "chat": {"id": int(chat)}}}})


class FakeMeta:
    def __init__(self, fehler_fb=False):
        self.calls, self.fehler_fb = [], fehler_fb

    def instagram(self, ig, url, cap):
        self.calls.append(("ig", ig, url, cap))
        return {"id": "ig1", "link": "https://instagram.com/p/x"}

    def facebook(self, page, url, cap):
        self.calls.append(("fb", page, url, cap))
        if self.fehler_fb:
            raise MetaFehler("kaputt")
        return {"id": "1_2", "link": "https://facebook.com/1_2"}


def settings(meta=True):
    return Settings("tok", "42", "mt" if meta else "", "page" if meta else "",
                    "igu" if meta else "", "v24.0", "https://raw.example/redaktion")


def einmal(st, tg, meta, s, entwuerfe=()):
    lauf.importieren(st, [("claude/x", f"entwuerfe/{e['id']}.json", e) for e in entwuerfe], tg, s.telegram_chat_id)
    lauf.senden(st, tg, s.telegram_chat_id)
    lauf.antworten(st, tg, s.telegram_chat_id)
    lauf.posten(st, s, tg, meta, lambda m: None)


def test_ja_veroeffentlicht(tmp_path):
    st, tg, meta, s = Status(tmp_path), FakeTG(), FakeMeta(), settings()
    einmal(st, tg, meta, s, [BEISPIEL])
    pid = BEISPIEL["id"]
    p = st.posts[pid]
    assert p["status"] == "gesendet" and st.bild(pid).is_file()
    knoepfe = tg.gesendet[1][3]
    assert knoepfe[0][0]["callback_data"] == f"ja:{p['key']}"
    assert not meta.calls  # ohne Antwort passiert nichts
    einmal(st, tg, meta, s, [BEISPIEL])  # erneuter Lauf: nichts doppelt
    assert sum(1 for g in tg.gesendet if g[0] == "foto") == 1 and not meta.calls

    tg.klick(1, f"ja:{p['key']}")
    einmal(st, tg, meta, s, [BEISPIEL])
    assert p["status"] == "veroeffentlicht"
    assert [c[0] for c in meta.calls] == ["ig", "fb"]
    assert meta.calls[0][2] == f"https://raw.example/redaktion/posts/{pid}/bild.jpg"
    assert meta.calls[0][3] == E.caption(BEISPIEL)
    # doppelter Klick / naechster Lauf veroeffentlicht nicht nochmal
    tg.klick(2, f"ja:{p['key']}")
    einmal(st, tg, meta, s)
    assert len(meta.calls) == 2


def test_nein_verwirft(tmp_path):
    st, tg, meta, s = Status(tmp_path), FakeTG(), FakeMeta(), settings()
    einmal(st, tg, meta, s, [BEISPIEL])
    tg.klick(1, f"nein:{st.posts[BEISPIEL['id']]['key']}")
    einmal(st, tg, meta, s)
    assert st.posts[BEISPIEL["id"]]["status"] == "verworfen" and not meta.calls


def test_fremder_chat_wird_ignoriert(tmp_path):
    st, tg, meta, s = Status(tmp_path), FakeTG(), FakeMeta(), settings()
    einmal(st, tg, meta, s, [BEISPIEL])
    tg.klick(1, f"ja:{st.posts[BEISPIEL['id']]['key']}", chat="999")
    einmal(st, tg, meta, s)
    assert st.posts[BEISPIEL["id"]]["status"] == "gesendet" and not meta.calls


def test_ohne_meta_manuell(tmp_path):
    st, tg, s = Status(tmp_path), FakeTG(), settings(meta=False)
    einmal(st, tg, None, s, [BEISPIEL])
    tg.klick(1, f"ja:{st.posts[BEISPIEL['id']]['key']}")
    einmal(st, tg, None, s)
    assert st.posts[BEISPIEL["id"]]["status"] == "freigegeben_manuell"


def test_teilfehler_und_nochmal(tmp_path):
    st, tg, meta, s = Status(tmp_path), FakeTG(), FakeMeta(fehler_fb=True), settings()
    einmal(st, tg, meta, s, [BEISPIEL])
    key = st.posts[BEISPIEL["id"]]["key"]
    tg.klick(1, f"ja:{key}")
    einmal(st, tg, meta, s)
    assert st.posts[BEISPIEL["id"]]["status"] == "teilweise"
    meta.fehler_fb = False
    tg.klick(2, f"nochmal:{key}")
    einmal(st, tg, meta, s)
    assert st.posts[BEISPIEL["id"]]["status"] == "veroeffentlicht"
    assert [c[0] for c in meta.calls] == ["ig", "fb", "fb"]  # Instagram nicht doppelt


def test_ungueltig_wird_nicht_gesendet(tmp_path):
    st, tg, meta, s = Status(tmp_path), FakeTG(), FakeMeta(), settings()
    einmal(st, tg, meta, s, [dict(BEISPIEL, quelle={"name": "BR", "url": "https://br.de/x"})])
    assert st.posts[BEISPIEL["id"]]["status"] == "ungueltig"
    assert not any(g[0] == "foto" for g in tg.gesendet)


def test_testentwurf_veroeffentlicht_nie(tmp_path):
    st, tg, meta, s = Status(tmp_path), FakeTG(), FakeMeta(), settings()
    pid = lauf.testentwurf(st)
    einmal(st, tg, meta, s)
    tg.klick(1, f"ja:{st.posts[pid]['key']}")
    einmal(st, tg, meta, s)
    assert st.posts[pid]["status"] == "test_ok" and not meta.calls


def test_veraltet(tmp_path):
    from datetime import date
    assert ORIGINAL_VERALTET("2026-11-01-x", date(2026, 11, 10))
    assert not ORIGINAL_VERALTET("2026-11-08-x", date(2026, 11, 10))
    lauf._veraltet = ORIGINAL_VERALTET
    st, tg = Status(tmp_path), FakeTG()
    lauf.importieren(st, [("b", "entwuerfe/a.json", dict(BEISPIEL, id="2020-01-01-alt"))], tg, "42")
    assert st.posts["2020-01-01-alt"]["status"] == "veraltet" and not tg.gesendet


def test_beispieldatei_ist_gueltig():
    e = json.loads((Path(__file__).parent.parent / "docs" / "beispiel-entwurf.json").read_text())
    assert E.pruefen(e).ok


def test_metacheck_mit_attrappe():
    from automat import metacheck

    class M:
        def _req(self, methode, pfad, **p):
            if pfad == "debug_token":
                return {"data": {"is_valid": True, "type": "PAGE", "expires_at": 0,
                                 "scopes": sorted(metacheck.NOETIG_IG | metacheck.NOETIG_FB)}}
            if pfad == "page":
                return {"name": "Radio Boarisch", "instagram_business_account": {"id": "igu"}}
            if pfad == "igu":
                return {"username": "radioboarisch"}
            if pfad.endswith("content_publishing_limit"):
                return {"data": [{"quota_usage": 0, "config": {"quota_total": 100}}]}
            raise AssertionError(pfad)

    ok, z = metacheck.pruefen(settings(), M())
    assert ok, z
    assert "mt" not in "\n".join(z)  # Token nie in der Ausgabe
