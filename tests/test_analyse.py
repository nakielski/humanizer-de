"""Tests für scripts/analyse.py.

Teil 1 prüft das Skript gegen den Katalog in SKILL.md: Jedes Vorher-Beispiel
eines maschinell prüfbaren Musters muss sein Muster auslösen, jedes
Nachher-Beispiel darf es nicht. So bleiben Katalog und Skript synchron.

Teil 2 sind Regressionstests für deutsche Sonderfälle (Abkürzungen,
trennbare Verben, Wortgrenzen, Markdown, Typografie) und für --diff.
"""
import pytest

from conftest import analysiere, anzahl, ids, lauf

# Muster, die das Skript erkennen soll. Nicht enthalten sind Muster, die nur
# ein Mensch oder Modell beurteilen kann (z. B. B5, B7, C5, E4, F*, G*) und
# D3, dessen Katalogbeispiel das Sonderzeichen nur beschreibt (eigener Test).
MASCHINELL_PRUEFBAR = [
    "A1", "A2", "A3", "A4", "A5", "A6", "A7",
    "B1", "B2", "B3", "B4", "B6", "B8", "B9", "B10", "B11", "B12",
    "C1", "C3", "C4", "C6", "C7", "C8", "C9", "C10",
    "D1", "D2", "D4", "D4a", "D5", "D6",
    "E1", "E2", "E3", "E5", "E6",
]


# --- Teil 1: Katalog -------------------------------------------------------

@pytest.mark.parametrize("muster_id", MASCHINELL_PRUEFBAR)
def test_vorher_loest_muster_aus(muster_katalog, muster_id):
    assert muster_id in muster_katalog, f"{muster_id} fehlt in SKILL.md"
    vorher = muster_katalog[muster_id]["vorher"]
    assert vorher, f"{muster_id} hat kein Vorher-Beispiel"
    for text in vorher:
        assert muster_id in ids(analysiere(text)), f"{muster_id} nicht erkannt in: {text}"


@pytest.mark.parametrize("muster_id", MASCHINELL_PRUEFBAR)
def test_nachher_ist_frei_vom_muster(muster_katalog, muster_id):
    nachher = muster_katalog[muster_id]["nachher"]
    assert nachher, f"{muster_id} hat kein Nachher-Beispiel"
    for text in nachher:
        assert muster_id not in ids(analysiere(text)), f"{muster_id} fälschlich in: {text}"


# --- Teil 2: Wortgrenzen, Flexion, trennbare Verben -------------------------

@pytest.mark.parametrize("text", [
    "Der Haken wurde an der Wand befestigt.",
    "Die Fernerkundung lieferte neue Daten.",
    "Die Parteienlandschaft ist zersplittert.",
    "Unsere IT-Landschaft ist historisch gewachsen.",
    "Wir haben zusätzliche Kosten eingeplant.",
    "Einerseits ist das gut, andererseits teuer.",
    "Beide Jobs laufen gleichzeitig.",
    "Eingebettete Systeme brauchen wenig Strom.",
    "Der Prozess ist zustandsbehaftet.",
])
def test_keine_fehltreffer_bei_normalem_deutsch(text):
    assert ids(analysiere(text)) == set(), text


def test_flexion_wird_erkannt():
    bericht = analysiere("Die Lösung lässt sich nahtloser einbinden als gedacht.")
    assert "B1" in ids(bericht)


def test_trennbare_verben_werden_erkannt():
    text = ("Die Halle zeichnet sich durch flexible Grundrisse aus. "
            "Das Modell stellt eine starke Vereinfachung dar. "
            "Das Diagramm bildet die wichtigsten Prozesse ab.")
    assert anzahl(analysiere(text), "B2") == 3


def test_nebensatzform_trennbarer_verben():
    text = "Wir wissen, dass das Modell eine Vereinfachung darstellt."
    assert "B2" in ids(analysiere(text))


def test_ueberlappende_eintraege_zaehlen_einmal():
    bericht = analysiere("Es geht nicht nur um Geld, sondern auch um Zeit.")
    assert anzahl(bericht, "B3") == 1


def test_konnektoren_nur_am_satzanfang():
    bericht = analysiere("Wir planen außerdem einen Workshop. Das Team ist zusätzlich motiviert.")
    assert "C1" not in ids(bericht)


# --- Trikolon ---------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Die Lösung ist schnell, sicher und zuverlässig.",
    "Wir bieten inspirierende Keynotes, spannende Panels und intensive Workshops.",
    "Gut sind sie bei Boilerplate: Konfiguration, Test-Gerüste, Wiederholungs-Refactorings.",
])
def test_trikolon_mitten_im_satz(text):
    assert "B4" in ids(analysiere(text))


def test_zwei_elemente_sind_kein_trikolon():
    assert "B4" not in ids(analysiere("Wir bieten Keynotes und Panels."))


# --- Satztrennung und Markdown ----------------------------------------------

def test_abkuerzungen_und_ordinalzahlen_trennen_keine_saetze():
    text = ("Das gilt z. B. für Konfigurationen, u. a. bei Tests. "
            "Im 16. Jahrhundert entstand der Ort. "
            "Dr. Meier prüft das bzw. sein Team.")
    assert analysiere(text)["saetze"] == 3


def test_markdown_ueberschriften_und_listen_sind_keine_saetze():
    text = ("## Wie der Import läuft\n\n"
            "- Konfiguration laden\n- Daten prüfen\n- Export schreiben\n- Log ablegen\n\n"
            "Danach ist der Lauf fertig.")
    bericht = analysiere(text)
    assert bericht["saetze"] == 1
    assert bericht["satzlaengen_min_max"] == [5, 5]


def test_frontmatter_codebloecke_und_links_werden_ignoriert():
    text = ('---\ndescription: "Eine nahtlose, ganzheitliche Lösung"\n---\n\n'
            "Der Text ist kurz.\n\n```json\n{\"a\": \"nahtlos\"}\n```\n\n"
            "Siehe `\"x\"` und [die Doku](https://example.com/Test-Gerüste-Projekt-Ordner).")
    bericht = analysiere(text)
    assert ids(bericht) == set(), bericht["funde"]


# --- Variationskoeffizient --------------------------------------------------

def test_cv_gleichfoermige_saetze_sind_verdaechtig():
    text = " ".join(f"Das Team prüft heute die Daten in Runde {i}." for i in range(12))
    bericht = analysiere(text)
    assert bericht["cv_verdaechtig"] is True
    assert "C2" in ids(bericht)


def test_cv_unter_zehn_saetzen_keine_bewertung():
    text = "Kurz. Das ist ein deutlich längerer Satz mit vielen Wörtern darin. Ende."
    assert analysiere(text)["cv_verdaechtig"] is False


# --- Typografie -------------------------------------------------------------

def test_bis_striche_sind_keine_gedankenstriche():
    bericht = analysiere("Siehe Seite 12–14, Strecke Köln–Bonn, geöffnet 10–20 Uhr.")
    assert "D1" not in ids(bericht)


@pytest.mark.parametrize("text", [
    "Er sagte “so geht das” und ging.",
    "Er sagte „so geht das\" und ging.",
    'Er sagte "so geht das" und ging.',
])
def test_falsche_anfuehrungszeichen(text):
    assert "D2" in ids(analysiere(text))


def test_deutsche_anfuehrungszeichen_sind_ok():
    assert "D2" not in ids(analysiere("Er sagte „so geht das“ und ging. Das war’s."))


@pytest.mark.parametrize("text", [
    "Die Auslastung liegt bei 87 %.",
    "Das gilt z. B. hier.",
    "Ein unsichtbares​Zeichen.",
    "Erster Satz.  Zweiter Satz.",
    "Absatz eins.\n\n Absatz zwei beginnt mit Leerzeichen.",
])
def test_sonderzeichen_und_leerzeichen(text):
    assert "D3" in ids(analysiere(text))


def test_eingerueckte_unterlisten_sind_kein_leerzeichenfund():
    text = "- Punkt\n  - Unterpunkt\n  - Noch einer\n\nNormaler Satz."
    assert "D3" not in ids(analysiere(text))


@pytest.mark.parametrize("text", ["• Erster Punkt\n• Zweiter", "· Erster Punkt\n· Zweiter"])
def test_aufzaehlungszeichen_reste(text):
    assert "D6" in ids(analysiere(text))


# --- Einschätzung (G1) ------------------------------------------------------

def test_einschaetzung_menschlicher_text_unauffaellig():
    text = ("Gestern habe ich den Server neu aufgesetzt. Das hat länger gedauert als "
            "gedacht, weil das Backup nicht vollständig war. Am Ende lief alles wieder.")
    assert analysiere(text)["einschaetzung"]["stufe"] == "unauffällig"


def test_einschaetzung_ki_text_auffaellig(muster_katalog):
    text = ("Gute Frage! In der heutigen schnelllebigen digitalen Welt spielt KI eine "
            "entscheidende Rolle. Es geht nicht nur um Technik, sondern um Haltung. "
            "Ich hoffe, das hilft!")
    assert analysiere(text)["einschaetzung"]["stufe"] == "auffällig"


def test_strict_setzt_exitcode():
    code, _, _ = lauf("--strict", "-", text="Gute Frage! Ich hoffe, das hilft! Tauchen wir ein.")
    assert code == 1
    code, _, _ = lauf("--strict", "-", text="Der Server läuft wieder.")
    assert code == 0


def test_leere_eingabe_stuerzt_nicht_ab():
    bericht = analysiere("")
    assert bericht["woerter"] == 0
    assert bericht["einschaetzung"]["stufe"] == "unauffällig"


def test_json_bleibt_rueckwaertskompatibel():
    bericht = analysiere("Darüber hinaus ist das nahtlos.")
    for schluessel in ("woerter", "saetze", "satzlaengen_min_max", "cv_satzlaengen",
                       "cv_verdaechtig", "wortfunde", "trikolon", "typografie"):
        assert schluessel in bericht


# --- Fakten-Abgleich (--diff) -----------------------------------------------

def _diff(alt, neu, tmp_path):
    import json
    a = tmp_path / "alt.md"
    b = tmp_path / "neu.md"
    a.write_text(alt, encoding="utf-8")
    b.write_text(neu, encoding="utf-8")
    code, out, err = lauf("--json", "--diff", str(a), str(b))
    assert code in (0, 1), err
    return json.loads(out)


def test_diff_findet_erfundene_zahlen_und_namen(tmp_path):
    ergebnis = _diff("Das Tool spart Zeit.",
                     "Das Tool spart 40 Minuten pro Ticket, sagt Dr. Meier.", tmp_path)
    neu = " ".join(ergebnis["neu"])
    assert "40" in neu and "Meier" in neu
    assert ergebnis["verloren"] == []


def test_diff_findet_verlorene_fakten(tmp_path):
    ergebnis = _diff("Seit 2015 wurden 400 Wohnungen genehmigt, laut „Stadtanzeiger“.",
                     "Es wurden Wohnungen genehmigt.", tmp_path)
    verloren = " ".join(ergebnis["verloren"])
    assert "2015" in verloren and "400" in verloren and "Stadtanzeiger" in verloren


def test_diff_ignoriert_umformulierung_ohne_neue_fakten(tmp_path):
    ergebnis = _diff("Im März 2024 gab sie der Zeitung ein Interview zur KI-Regulierung.",
                     "Zur KI-Regulierung gab sie im März 2024 ein Interview.", tmp_path)
    assert ergebnis["neu"] == []


def test_diff_normalisiert_tausenderpunkte(tmp_path):
    ergebnis = _diff("Benötigt würden 2.000 Wohnungen.", "Benötigt würden 2000 Wohnungen.", tmp_path)
    assert ergebnis["neu"] == [] and ergebnis["verloren"] == []
