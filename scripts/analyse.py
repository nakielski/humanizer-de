#!/usr/bin/env python3
"""Muster- und Stilscanner für deutsche Texte (humanizer-de).

Aufruf:
    python3 analyse.py [--json] [--strict] [DATEI | -]
    python3 analyse.py --diff ORIGINAL NEU [--json] [--strict]
    python3 analyse.py --muster

Ohne DATEI (oder mit "-") liest das Skript von stdin.

Was gemessen wird:
- Wendungen aus references/wordlist.json, mit Wortgrenzen, Flexion und
  trennbaren Verben; überlappende Treffer zählen einmal
- Satzlängen und ihr Variationskoeffizient (Satztrennung mit Schutz für
  deutsche Abkürzungen und Ordinalzahlen; Überschriften, Listen, Tabellen,
  Code und Frontmatter zählen nicht als Sätze)
- Strukturmuster: Trikolon, Dreierlisten, gleiche Satzanfänge,
  Frage-Fragmente, gestapelte Relativierungen, Bindestrich-Komposita,
  Schablonen-Überschriften
- Typografie: Gedankenstriche (ohne Bis-Striche), Anführungszeichen,
  geschützte und unsichtbare Zeichen, Fettdruck, Emojis, Aufzählungszeichen
- --diff: Zahlen, Namen, Zitate und Links, die in einer Überarbeitung neu
  dazugekommen oder verloren gegangen sind

Das Ergebnis ist eine Hilfe, kein Urteil. Die Schwellen sind Faustregeln und
nicht an einem Korpus kalibriert; Katalog und Sprachgefühl entscheiden.
"""
import argparse
import json
import math
import re
import sys
from collections import OrderedDict
from pathlib import Path

__version__ = "0.3.0"

WORTLISTE = Path(__file__).resolve().parent.parent / "references" / "wordlist.json"

# Schwellen für schwache Signale. Kalibriert so, dass jedes Signal bei etwa
# 5 Prozent menschlicher Texte anschlägt (95. Perzentil bzw. 5. Perzentil beim
# CV), gemessen an 1.028 Nachrichtentexten aus 10kGNAD (DER STANDARD,
# 2015/16, also vor ChatGPT). Gegen KI-Texte ist noch nicht kalibriert.
CV_GRENZE = 0.3                 # menschlich: P5 = 0,30, Median 0,44
MIN_SAETZE_FUER_CV = 10
GEDANKENSTRICHE_PRO_1000 = 20   # menschlich: P95 = 20,3
KOMPOSITA_PRO_1000 = 25         # menschlich: P95 = 24,6
TRIKOLA_PRO_1000 = 10           # menschlich: P95 = 9,4
PLATZHALTER_PUNKT = "\x00"

# --------------------------------------------------------------------------
# Ein- und Ausgabe
# --------------------------------------------------------------------------


def utf8_streams():
    """Unter Windows lesen stdin/stdout sonst mit der Locale-Kodierung."""
    for strom in (sys.stdin, sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def lies_text(pfad):
    if not pfad or pfad == "-":
        return sys.stdin.read()
    datei = Path(pfad)
    if not datei.exists():
        raise SystemExit(f"Datei nicht gefunden: {pfad}")
    try:
        return datei.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        print(f"Hinweis: {pfad} ist kein UTF-8, lese als Windows-1252.", file=sys.stderr)
        return datei.read_text(encoding="cp1252")


def lade_wortliste(pfad=WORTLISTE):
    if not pfad.exists():
        raise SystemExit(f"Wortliste fehlt: {pfad}")
    with open(pfad, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Zerlegung: Markdown in Prosa, Überschriften, Listen trennen
# --------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n.*?\n(?:---|\.\.\.)[ \t]*(?:\n|\Z)", re.S)
CODEBLOCK_RE = re.compile(r"^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[ \t]*$", re.S | re.M)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s)>\]]+")
MD_LINK_RE = re.compile(r"!?\[([^\]\n]*)\]\([^)\n]*\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|\n]+)(?:\|([^\]\n]+))?\]\]")
HTML_RE = re.compile(r"</?[A-Za-z][^>\n]*>")
UEBERSCHRIFT_RE = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+(.*?)[ \t]*#*[ \t]*$")
LISTE_RE = re.compile(r"^([ \t]*)([-*+•·▪►‣◦–]|\d{1,3}[.)])[ \t]+(.*)$")
TABELLE_RE = re.compile(r"^[ \t]*\|")
TRENNER_RE = re.compile(r"^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$")
ZITATZEILE_RE = re.compile(r"^[ \t]*>[ \t]?")


def ohne_code(text):
    """Frontmatter und Codeblöcke entfernen; der Rest bleibt unverändert."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = FRONTMATTER_RE.sub("", text, count=1)
    return CODEBLOCK_RE.sub("\n", text)


def entmarkiere(s):
    s = MD_LINK_RE.sub(r"\1", s)
    s = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), s)
    s = HTML_RE.sub("", s)
    s = re.sub(r"(\*\*|__)(.+?)\1", r"\2", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"\1", s)
    s = re.sub(r"(?<![\w_])_(?!\s)([^_\n]+?)(?<!\s)_(?![\w_])", r"\1", s)
    return s.strip()


def zerlege(text):
    """Teilt Markdown in Prosa-Absätze, Überschriften, Listenpunkte und Tabellen."""
    roh = ohne_code(text)
    roh = INLINE_CODE_RE.sub("", roh)
    roh = MD_LINK_RE.sub(r"\1", roh)
    roh = URL_RE.sub("", roh)
    roh = HTML_RE.sub("", roh)

    absaetze, ueberschriften, listen, tabellen = [], [], [], []
    aktuell = []
    letzte_liste = None  # (einrueckung, index des Listenblocks)
    listenblock = 0

    def absatz_ende():
        if aktuell:
            absaetze.append(entmarkiere(" ".join(aktuell)))
            aktuell.clear()

    for zeile in roh.split("\n"):
        inhalt = ZITATZEILE_RE.sub("", zeile)
        if not inhalt.strip() or TRENNER_RE.match(inhalt):
            absatz_ende()
            letzte_liste = None
            continue
        m = UEBERSCHRIFT_RE.match(inhalt)
        if m:
            absatz_ende()
            ueberschriften.append({"roh": m.group(1), "text": entmarkiere(m.group(1))})
            letzte_liste = None
            continue
        if TABELLE_RE.match(inhalt):
            absatz_ende()
            zellen = [entmarkiere(z) for z in inhalt.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", z.strip()) for z in zellen if z.strip()):
                tabellen.append(" ".join(z for z in zellen if z))
            continue
        m = LISTE_RE.match(inhalt)
        if m:
            absatz_ende()
            einrueckung = len(m.group(1).expandtabs(4))
            if letzte_liste is None:
                listenblock += 1
            listen.append({
                "roh": m.group(3), "text": entmarkiere(m.group(3)),
                "marker": m.group(2), "ebene": einrueckung, "block": listenblock,
            })
            letzte_liste = einrueckung
            continue
        if letzte_liste is not None and zeile.startswith((" ", "\t")) and listen:
            # Fortsetzungszeile eines Listenpunkts
            listen[-1]["text"] += " " + entmarkiere(inhalt)
            continue
        letzte_liste = None
        aktuell.append(inhalt.strip())
    absatz_ende()

    teile = absaetze + [u["text"] for u in ueberschriften] + [l["text"] for l in listen] + tabellen
    return {
        "roh": roh,
        "absaetze": [a for a in absaetze if a],
        "ueberschriften": ueberschriften,
        "listen": listen,
        "tabellen": tabellen,
        "volltext": "\n\n".join(t for t in teile if t),
    }


# --------------------------------------------------------------------------
# Sätze
# --------------------------------------------------------------------------

ABKUERZUNGEN = [
    "z. B.", "u. a.", "d. h.", "u. U.", "i. d. R.", "o. Ä.", "o. ä.", "u. v. m.", "z. T.",
    "s. o.", "s. u.", "v. a.", "m. E.", "z. Hd.", "e. V.", "i. A.", "i. V.", "u. Ä.", "z. Zt.",
    "bzw.", "ca.", "vgl.", "usw.", "etc.", "evtl.", "ggf.", "inkl.", "exkl.", "zzgl.", "bspw.",
    "sog.", "insb.", "insbes.", "einschl.", "allg.", "jew.", "lt.", "max.", "min.", "Min.",
    "Std.", "Nr.", "Dr.", "Prof.", "Hr.", "Fr.", "St.", "Str.", "Abs.", "Art.", "Bd.", "Bsp.",
    "S.", "Mio.", "Mrd.", "Tsd.", "Jh.", "Jhd.", "Tel.", "Kap.", "Abb.", "Tab.", "Anm.",
    "Hrsg.", "Aufl.", "geb.", "gest.", "Ziff.", "vs.", "dt.", "engl.", "ehem.", "Co.",
    "Jan.", "Feb.", "Apr.", "Aug.", "Sep.", "Sept.", "Okt.", "Nov.", "Dez.",
]


def _abk_regex():
    teile = []
    for abk in sorted(ABKUERZUNGEN, key=len, reverse=True):
        stuecke = [re.escape(s) for s in abk.replace(" ", "").split(".") if s]
        teile.append(r"\.\s?".join(stuecke) + r"\.")
    return re.compile(r"(?<![\w.])(?:" + "|".join(teile) + ")")


ABK_RE = _abk_regex()
# „Im 16. Jahrhundert“ ist eine Ordinalzahl, „… in Runde 3. Das Team …“ ein Satzende.
ORDINAL_RE = re.compile(r"(?<![\w.,])(\d{1,3})\.(?=[ \t]+([^\s.,;:!?]+))")
SATZANFANG_WOERTER = {
    "Der", "Die", "Das", "Den", "Dem", "Des", "Ein", "Eine", "Einen", "Einem", "Es", "Er", "Sie",
    "Wir", "Ich", "Du", "Ihr", "Man", "Dann", "Danach", "Und", "Aber", "Doch", "So", "Auch",
    "Im", "In", "Am", "An", "Bei", "Mit", "Nach", "Seit", "Für", "Zum", "Zur", "Dieser", "Diese",
    "Dieses", "Hier", "Da", "Wenn", "Als", "Damit", "Deshalb", "Daher", "Trotzdem", "Jetzt",
    "Heute", "Gestern", "Morgen", "Insgesamt", "Somit", "Also", "Nun", "Zudem", "Außerdem",
}
SATZGRENZE_RE = re.compile(r"[.!?…]+[\"“”»«’')\]]*(?=\s+[\"„“»«'(\[]?[A-ZÄÖÜ0-9])")
WORT_RE = re.compile(r"[^\W_]+(?:[-'’.,][^\W_]+)*")


def _schuetze(s):
    s = ABK_RE.sub(lambda m: m.group(0).replace(".", PLATZHALTER_PUNKT), s)
    return ORDINAL_RE.sub(
        lambda m: m.group(0) if m.group(2) in SATZANFANG_WOERTER else m.group(1) + PLATZHALTER_PUNKT, s)


def saetze_aus(absatz):
    geschuetzt = _schuetze(absatz)
    saetze, start = [], 0
    for m in SATZGRENZE_RE.finditer(geschuetzt):
        saetze.append(geschuetzt[start:m.end()])
        start = m.end()
    saetze.append(geschuetzt[start:])
    return [s.replace(PLATZHALTER_PUNKT, ".").strip() for s in saetze if s.strip()]


def woerter(text):
    return WORT_RE.findall(text)


def variationskoeffizient(laengen):
    if len(laengen) < 3:
        return None
    mittel = sum(laengen) / len(laengen)
    if mittel == 0:
        return None
    varianz = sum((x - mittel) ** 2 for x in laengen) / len(laengen)
    return math.sqrt(varianz) / mittel


# --------------------------------------------------------------------------
# Funde
# --------------------------------------------------------------------------

class Fund:
    def __init__(self, muster_id, kategorie, text, staerke, start=-1, ende=-1,
                 beispiel="", min_treffer=1):
        self.muster_id = muster_id
        self.kategorie = kategorie
        self.text = text
        self.staerke = staerke
        self.start = start
        self.ende = ende
        self.beispiel = beispiel
        self.min_treffer = min_treffer


def _kontext(text, start, ende, rand=30):
    a = max(0, start - rand)
    b = min(len(text), ende + rand)
    schnipsel = re.sub(r"\s+", " ", text[a:b]).strip()
    return ("…" if a > 0 else "") + schnipsel + ("…" if b < len(text) else "")


def _kompiliere(eintrag, kat_cs):
    if isinstance(eintrag, str):
        eintrag = {"phrase": eintrag}
    if "re" in eintrag:
        quelle = eintrag["re"]
        label = eintrag.get("label", quelle)
    else:
        phrase = eintrag["phrase"]
        label = eintrag.get("label", phrase.replace("*", ""))
        stuecke = []
        for wort in phrase.split():
            stern = wort.endswith("*")
            stuecke.append(re.escape(wort.rstrip("*")) + (r"\w*" if stern else ""))
        quelle = r"\s+".join(stuecke)
        if re.match(r"\w", phrase):
            quelle = r"\b" + quelle
        if re.search(r"\w$", phrase.rstrip("*")):
            quelle += r"\b"
    flags = re.M if (eintrag.get("cs") or kat_cs) else re.M | re.I
    return re.compile(quelle, flags), label, eintrag.get("staerke")


def wortlisten_funde(volltext, wortliste):
    muster = wortliste["muster"]
    kandidaten = []
    for name, kat in wortliste["kategorien"].items():
        mid = kat["muster_id"]
        staerke_kat = muster[mid]["staerke"]
        for eintrag in kat["eintraege"]:
            regex, label, staerke = _kompiliere(eintrag, kat.get("cs", False))
            if kat.get("satzanfang"):
                regex = re.compile(r"(?:^|(?<=[.!?:…])\s+)[\"„“»(]*(?P<t>" + regex.pattern + ")",
                                   regex.flags)
            for m in regex.finditer(volltext):
                s, e = m.span("t") if "t" in regex.groupindex else m.span()
                if e <= s:
                    continue
                kandidaten.append(Fund(mid, name, label, staerke or staerke_kat, s, e,
                                       _kontext(volltext, s, e), kat.get("min_treffer", 1)))
    # Überlappungen: starke vor schwachen, längere vor kürzeren
    rang = {"stark": 0, "schwach": 1}
    kandidaten.sort(key=lambda f: (rang[f.staerke], -(f.ende - f.start), f.start))
    belegt, angenommen = [], []
    for f in kandidaten:
        if any(f.start < e and s < f.ende for s, e in belegt):
            continue
        belegt.append((f.start, f.ende))
        angenommen.append(f)
    return angenommen


# --- Strukturmuster ---------------------------------------------------------

ELEMENT = r"(?!(?:weil|dass|da|wenn|ob|obwohl|damit|sodass|als|während|die|der|das|den|dem|deren|dessen|was|wo|wie|um|aber|sondern|denn|doch|bis|nachdem|bevor|falls|sofern|indem|sobald|solange|und|oder)\b)[^\W\d_][\w-]*(?:\s+[^\W\d_][\w-]*){0,2}"
TRIKOLON_UND_RE = re.compile(
    r"(?P<a>[^\W\d_][\w-]*),\s+(?P<b>" + ELEMENT + r"),?\s+(?:und|oder|sowie)\s+(?P<c>[^\W\d_][\w-]*)",
    re.I)
TRIKOLON_DOPPELPUNKT_RE = re.compile(
    r":\s*(?P<a>" + ELEMENT + r"),\s+(?P<b>" + ELEMENT + r"),\s+(?:(?:und|oder)\s+)?(?P<c>" + ELEMENT + r")\s*(?:[.!?]|$)",
    re.I)
RELATIVIERUNGEN_RE = re.compile(
    r"\b(?:möglicherweise|eventuell|unter\s+Umständen|gegebenenfalls|potenziell|potentiell|"
    r"tendenziell|gewissermaßen|in\s+gewisser\s+Weise|in\s+gewissem\s+(?:Maße|Umfang)|"
    r"gewisse[nmrs]?|vermutlich|womöglich|ein\s+Stück\s+weit|könnte[n]?|dürfte[n]?)\b",
    re.I)
KOMPOSITUM_RE = re.compile(r"(?<![\w-])[A-ZÄÖÜ][a-zäöüß]{2,}-[A-ZÄÖÜ][a-zäöüß]{2,}(?![\w-])")
ZWEITEILIG_RE = re.compile(r"^[^\W\d_][\w-]*(?:\s+[\w-]+)?\s+und\s+[^\W\d_][\w-]*(?:\s+[\w-]+)?$")
FAZIT_UEBERSCHRIFT_RE = re.compile(
    r"^(?:Fazit|Zusammenfassung|Schlussfolgerung(?:en)?|Schlussgedanken?|Abschließende\s+Gedanken)\b", re.I)
TITELWOERTER = {"Und", "Oder", "Der", "Die", "Das", "Des", "Dem", "Den", "Ein", "Eine", "Einer",
                "Im", "In", "Mit", "Für", "Von", "Vom", "Zu", "Zum", "Zur", "Auf", "Bei", "Aus",
                "Als", "Am", "An", "Über", "Unter", "Nach", "Vor", "Durch", "Ohne", "Um", "Gegen"}


def mindestzahl(absolut, pro_1000, anzahl_woerter):
    """Kleinste Trefferzahl, die sowohl absolut als auch in der Dichte über der Schwelle liegt."""
    return max(absolut, int(pro_1000 * anzahl_woerter / 1000) + 1)


def struktur_funde(z, saetze_je_absatz, anzahl_woerter):
    funde = []
    alle_saetze = [s for absatz in saetze_je_absatz for s in absatz] + [l["text"] for l in z["listen"]]

    # B4 Trikolon
    for satz in alle_saetze:
        belegt = []
        for regex in (TRIKOLON_DOPPELPUNKT_RE, TRIKOLON_UND_RE):
            for m in regex.finditer(satz):
                if any(m.start() < e and s < m.end() for s, e in belegt):
                    continue  # dieselbe Aufzählung nicht doppelt zählen
                belegt.append(m.span())
                funde.append(Fund("B4", "trikolon", "Dreiergruppe", "schwach", beispiel=m.group(0)[:80],
                                  min_treffer=mindestzahl(2, TRIKOLA_PRO_1000, anzahl_woerter)))

    # B11 Bindestrich-Komposita
    for m in KOMPOSITUM_RE.finditer(z["volltext"]):
        funde.append(Fund("B11", "bindestrich_komposita", "Bindestrich in gängigem Kompositum",
                          "schwach", beispiel=m.group(0),
                          min_treffer=mindestzahl(3, KOMPOSITA_PRO_1000, anzahl_woerter)))

    # B12 gestapelte Relativierungen
    for satz in alle_saetze:
        treffer = RELATIVIERUNGEN_RE.findall(satz)
        if len(treffer) >= 3:
            funde.append(Fund("B12", "relativierungen", "drei oder mehr Relativierungen in einem Satz",
                              "schwach", beispiel=satz[:80]))

    # C3 Listen mit genau drei Punkten (oberste Ebene)
    bloecke = OrderedDict()
    for l in z["listen"]:
        bloecke.setdefault(l["block"], []).append(l)
    for punkte in bloecke.values():
        oben = min(p["ebene"] for p in punkte)
        hauptpunkte = [p for p in punkte if p["ebene"] == oben]
        if len(hauptpunkte) == 3:
            funde.append(Fund("C3", "dreierliste", "Liste mit genau drei Punkten", "schwach",
                              beispiel=" | ".join(p["text"][:25] for p in hauptpunkte), min_treffer=2))

    # C4 Fazit-Überschrift, C6 zweiteilige Überschrift, D4a Großschreibung
    for u in z["ueberschriften"]:
        text = u["text"]
        if FAZIT_UEBERSCHRIFT_RE.match(text):
            funde.append(Fund("C4", "fazit_ueberschrift", "Überschrift „Fazit“", "schwach", beispiel=text))
        if ZWEITEILIG_RE.match(text):
            funde.append(Fund("C6", "zweiteilige_ueberschrift", "Überschrift „X und Y“", "schwach",
                              beispiel=text))
        buchstaben = [c for c in text if c.isalpha()]
        worte = text.split()
        if len(buchstaben) >= 8 and all(c.isupper() for c in buchstaben):
            funde.append(Fund("D4a", "versalien", "Überschrift in Versalien", "schwach", beispiel=text))
        elif any(w in TITELWOERTER for w in worte[1:]):
            funde.append(Fund("D4a", "titelschreibweise", "englische Titelschreibweise", "schwach",
                              beispiel=text))

    # C8 Frage-Fragment mit Kurzantwort, C10 gleiche Satzanfänge
    for saetze in saetze_je_absatz:
        for frage, antwort in zip(saetze, saetze[1:]):
            if (frage.endswith("?") and len(woerter(frage)) <= 3
                    and antwort.endswith((".", "!")) and len(woerter(antwort)) <= 6):
                funde.append(Fund("C8", "frage_fragment", "Frage-Fragment mit Kurzantwort", "stark",
                                  beispiel=f"{frage} {antwort}"))
    folge = [s for absatz in saetze_je_absatz for s in absatz]
    lauf, letzter = 1, None
    for satz in folge + [""]:
        anfang = " ".join(w.lower() for w in woerter(satz)[:2])
        if anfang and anfang == letzter:
            lauf += 1
            continue
        if lauf >= 3:
            funde.append(Fund("C10", "satzanfaenge", f"{lauf} Sätze in Folge beginnen mit „{letzter}“",
                              "schwach", beispiel=letzter))
        lauf, letzter = 1, anfang
    return funde


# --- Typografie --------------------------------------------------------------

EMOJI = "[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF☀-➿⭐⭕]"
EMOJI_ZEILENANFANG_RE = re.compile(r"^[ \t]*(?:#{1,6}[ \t]+|[-*+][ \t]+|\d{1,3}[.)][ \t]+)?(?:\*\*)?" + EMOJI, re.M)
AUFZAEHLUNGSZEICHEN_RE = re.compile(r"^[ \t]*[•·▪►‣◦][ \t]", re.M)
FETT_RE = re.compile(r"\*\*[^*\n]+?\*\*|__[^_\n]+?__")
FETTES_LABEL_RE = re.compile(r"^[ \t]*(?:[-*+]|\d{1,3}[.)])[ \t]+(?:\*\*|__)[^*_\n]+?(?:\*\*|__)", re.M)


def typografie_funde(z, anzahl_woerter, anzahl_saetze):
    roh = z["roh"]
    funde = []

    def fund(mid, kat, text, anzahl, beispiel="", zaehlt=True):
        for _ in range(anzahl):
            funde.append(Fund(mid, kat, text, "schwach", beispiel=beispiel,
                              min_treffer=1 if zaehlt else 10 ** 9))

    # D1 Gedankenstriche: Geviertstrich immer, Halbgeviertstrich nur mit Leerzeichen (keine Bis-Striche)
    n_gev = roh.count("—")
    n_halb = len(re.findall(r"(?<=[ \t])–(?=\s)", roh))
    if n_gev:
        fund("D1", "geviertstrich", "Geviertstrich (—)", n_gev)
    pro_1000 = n_halb / anzahl_woerter * 1000 if anzahl_woerter else 0
    if n_halb >= 2 and pro_1000 > GEDANKENSTRICHE_PRO_1000:
        fund("D1", "gedankenstrich", f"Gedankenstrich ( – ) gehäuft, {pro_1000:.1f} pro 1000 Wörter "
             f"(Grenze {GEDANKENSTRICHE_PRO_1000})".replace(".", ","), n_halb)

    # D2 Anführungszeichen
    # Gerade Zeichen tippt auch jeder Mensch im Texteditor; verdächtig ist erst die Mischung.
    n_gerade = roh.count('"')
    if n_gerade:
        gemischt_mit_deutschen = "„" in roh or "“" in roh
        fund("D2", "gerade_anfuehrung", 'gerade Anführungszeichen (")', 1,
             _kontext(roh, roh.index('"'), roh.index('"') + 1), zaehlt=gemischt_mit_deutschen)
    if "”" in roh:
        fund("D2", "englische_anfuehrung", "englische Anführungszeichen (“…”)", 1)
    n_gemischt = len(re.findall(r"„[^“”\"\n]{0,200}\"", roh))
    if n_gemischt:
        fund("D2", "gemischte_anfuehrung", 'gemischt: „…"', n_gemischt)

    # D3 geschützte und unsichtbare Zeichen, Leerzeichen-Reste
    for zeichen, name in ((" ", "geschütztes Leerzeichen U+00A0"),
                          (" ", "schmales geschütztes Leerzeichen U+202F")):
        if zeichen in roh:
            fund("D3", "sonderleerzeichen", name, roh.count(zeichen))
    n_unsichtbar = len(re.findall(r"[​‌‍⁠﻿]", roh))
    if n_unsichtbar:
        fund("D3", "unsichtbar", "unsichtbare Zeichen (U+200B u. ä.)", n_unsichtbar)
    n_doppelt = len(re.findall(r"[.!?] {2,}\S", roh))
    if n_doppelt:
        fund("D3", "doppelleerzeichen", "doppelte Leerzeichen nach Satzende", n_doppelt)
    zeilen = roh.split("\n")
    n_einzug = 0
    for i, zeile in enumerate(zeilen):
        absatzanfang = i == 0 or not zeilen[i - 1].strip()
        if absatzanfang and re.match(r"^ {1,3}[^\s\-*+•·▪►>|#\d]", zeile):
            n_einzug += 1
    if n_einzug:
        fund("D3", "einzug", "Leerzeichen am Absatzanfang", n_einzug)

    # D4 Fettdruck
    n_fett = len(FETT_RE.findall(roh))
    if n_fett >= 3 and n_fett >= 0.5 * max(1, anzahl_saetze):
        fund("D4", "fettdruck", f"Fettdruck in fast jedem Satz ({n_fett}×)", 1)
    n_labels = len(FETTES_LABEL_RE.findall(roh))
    if n_labels >= 3:
        fund("D4", "fette_labels", f"fette Labels in Listen ({n_labels}×)", 1)

    # D5 Emojis am Zeilenanfang, D6 Aufzählungszeichen aus Chat-Oberflächen
    n_emoji = len(EMOJI_ZEILENANFANG_RE.findall(roh))
    if n_emoji:
        for _ in range(n_emoji):
            funde.append(Fund("D5", "emoji", "Emoji am Zeilen- oder Überschriftenanfang", "stark"))
    n_bullet = len(AUFZAEHLUNGSZEICHEN_RE.findall(roh))
    if n_bullet:
        fund("D6", "aufzaehlungszeichen", "• oder · als Aufzählungszeichen", n_bullet)
    return funde


# --------------------------------------------------------------------------
# Bericht
# --------------------------------------------------------------------------

def zusammenfassen(funde, muster):
    """Fasst Einzelfunde je Muster und Text zusammen."""
    gruppen = OrderedDict()
    for f in funde:
        schluessel = (f.muster_id, f.kategorie, f.text, f.staerke)
        g = gruppen.setdefault(schluessel, {"anzahl": 0, "beispiel": f.beispiel, "min": f.min_treffer})
        g["anzahl"] += 1
    # min_treffer gilt für die ganze Kategorie
    je_kategorie = {}
    for (mid, kat, _, _), g in gruppen.items():
        je_kategorie[(mid, kat)] = je_kategorie.get((mid, kat), 0) + g["anzahl"]
    ergebnis = []
    for (mid, kat, text, staerke), g in gruppen.items():
        ergebnis.append({
            "muster_id": mid,
            "muster": muster.get(mid, {}).get("name", mid),
            "kategorie": kat,
            "text": text,
            "staerke": staerke,
            "anzahl": g["anzahl"],
            "beispiel": g["beispiel"],
            "zaehlt": je_kategorie[(mid, kat)] >= g["min"],
        })
    reihenfolge = list(muster)
    ergebnis.sort(key=lambda f: (f["staerke"] != "stark",
                                 reihenfolge.index(f["muster_id"]) if f["muster_id"] in reihenfolge else 99))
    return ergebnis


def einschaetzung(funde, woerter_gesamt):
    stark = sorted({f["muster_id"] for f in funde if f["zaehlt"] and f["staerke"] == "stark"})
    schwach = sorted({f["muster_id"] for f in funde if f["zaehlt"] and f["staerke"] == "schwach"} - set(stark))
    if len(stark) >= 2 or (stark and len(schwach) >= 2) or len(schwach) >= 4:
        stufe = "auffällig"
    elif stark or len(schwach) >= 2:
        stufe = "prüfen"
    else:
        stufe = "unauffällig"
    treffer = sum(f["anzahl"] for f in funde if f["zaehlt"])
    return {
        "stufe": stufe,
        "starke_muster": stark,
        "schwache_muster": schwach,
        "treffer_pro_1000_woerter": round(treffer / woerter_gesamt * 1000, 1) if woerter_gesamt else 0.0,
    }


def analysiere(text, wortliste=None):
    wortliste = wortliste or lade_wortliste()
    muster = wortliste["muster"]
    z = zerlege(text)
    saetze_je_absatz = [saetze_aus(a) for a in z["absaetze"]]
    laengen = [len(woerter(s)) for absatz in saetze_je_absatz for s in absatz if woerter(s)]
    anzahl_woerter = len(woerter(z["volltext"]))
    cv = variationskoeffizient(laengen)
    cv_verdaechtig = cv is not None and len(laengen) >= MIN_SAETZE_FUER_CV and cv < CV_GRENZE

    roh_funde = wortlisten_funde(z["volltext"], wortliste)
    roh_funde += struktur_funde(z, saetze_je_absatz, anzahl_woerter)
    roh_funde += typografie_funde(z, anzahl_woerter, len(laengen) + len(z["listen"]))
    if cv_verdaechtig:
        roh_funde.append(Fund("C2", "satzlaengen", f"Satzlängen gleichförmig (CV {cv:.2f})".replace(".", ","),
                              "schwach"))
    funde = zusammenfassen(roh_funde, muster)

    bericht = {
        "version": __version__,
        "einschaetzung": einschaetzung(funde, anzahl_woerter),
        "woerter": anzahl_woerter,
        "saetze": len(laengen),
        "satzlaengen_min_max": [min(laengen), max(laengen)] if laengen else [0, 0],
        "cv_satzlaengen": round(cv, 3) if cv is not None else None,
        "cv_verdaechtig": cv_verdaechtig,
        "funde": funde,
    }
    # Felder aus Version 0.2 für bestehende Auswertungen
    bericht["wortfunde"] = [{"kategorie": f["kategorie"], "wort": f["text"], "anzahl": f["anzahl"]}
                            for f in funde if f["kategorie"] in wortliste["kategorien"]]
    bericht["trikolon"] = [f"{f['text']}: {f['beispiel']}" for f in funde if f["muster_id"] in ("B4", "C3")]
    bericht["typografie"] = [f"{f['text']}: {f['anzahl']}" for f in funde if f["muster_id"].startswith("D")]
    return bericht


# --------------------------------------------------------------------------
# Fakten-Abgleich
# --------------------------------------------------------------------------

ZAHL_RE = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)*(?:\s?(?:%|Prozent))?")
ZITAT_RES = [re.compile(r"„([^“\"\n]{2,120})[“\"]"), re.compile(r"\"([^\"\n]{2,120})\""),
             re.compile(r"“([^”\n]{2,120})”"), re.compile(r"»([^«\n]{2,120})«")]
MAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
AKRONYM_RE = re.compile(r"(?<![\w-])[A-ZÄÖÜ]{2,}s?(?![\w])")
BINNENMAJUSKEL_RE = re.compile(r"\b[A-Z][a-z]+[A-Z][A-Za-z]*\b")
TITELNAME_RE = re.compile(r"\b(?:Dr|Prof|Hr|Fr|Herr|Frau)\.?\s+(?:[A-ZÄÖÜ]\.\s+)?([A-ZÄÖÜ][\wäöüß-]+)")
NAMENSPAAR_RE = re.compile(r"(?<=[a-zäöüß,] )([A-ZÄÖÜ][\wäöüß-]+ [A-ZÄÖÜ][\wäöüß-]+)")
STOPPWOERTER = TITELWOERTER | {"Ich", "Wir", "Sie", "Er", "Es", "Du", "Ihr", "Dies", "Diese", "Dieser"}


def fakten(text):
    t = ohne_code(text)
    gefunden = OrderedDict()

    def merke(art, anzeige, schluessel):
        gefunden.setdefault((art, schluessel), f"{anzeige} ({art})")

    for m in ZAHL_RE.finditer(t):
        roh = m.group(0)
        schl = re.sub(r"\.(?=\d{3}(?!\d))", "", roh).replace(" ", "").replace("Prozent", "%")
        merke("Zahl", roh, schl)
    for regex in ZITAT_RES:
        for m in regex.finditer(t):
            merke("Zitat", f"„{m.group(1).strip()}“", m.group(1).strip().lower())
    for m in URL_RE.finditer(t):
        merke("Link", m.group(0), m.group(0).rstrip(".,;").lower())
    for m in MAIL_RE.finditer(t):
        merke("Mail", m.group(0), m.group(0).lower())
    for m in AKRONYM_RE.finditer(t):
        merke("Name?", m.group(0), m.group(0))
    for m in BINNENMAJUSKEL_RE.finditer(t):
        merke("Name?", m.group(0), m.group(0).lower())
    for m in TITELNAME_RE.finditer(t):
        merke("Name", m.group(0), m.group(1).lower())
    for m in NAMENSPAAR_RE.finditer(t):
        erster, zweiter = m.group(1).split(" ")
        if erster not in STOPPWOERTER and zweiter not in STOPPWOERTER:
            merke("Name?", m.group(1), m.group(1).lower())
    return gefunden


def fakten_diff(original, neu):
    a, b = fakten(original), fakten(neu)
    schl_a = {k[1] for k in a}
    schl_b = {k[1] for k in b}
    return {
        "neu": [anzeige for (art, schl), anzeige in b.items() if schl not in schl_a],
        "verloren": [anzeige for (art, schl), anzeige in a.items() if schl not in schl_b],
    }


# --------------------------------------------------------------------------
# Ausgabe
# --------------------------------------------------------------------------

def zahl_de(x, stellen=3):
    return f"{x:.{stellen}f}".replace(".", ",")


def drucke_bericht(b):
    e = b["einschaetzung"]
    teile = []
    if e["starke_muster"]:
        teile.append("starke Muster: " + ", ".join(e["starke_muster"]))
    if e["schwache_muster"]:
        teile.append("schwache: " + ", ".join(e["schwache_muster"]))
    print(f"Einschätzung: {e['stufe']}" + (f" ({'; '.join(teile)})" if teile else ""))
    lmin, lmax = b["satzlaengen_min_max"]
    print(f"Umfang: {b['woerter']} Wörter, {b['saetze']} Sätze"
          + (f", Satzlänge {lmin} bis {lmax} Wörter" if b["saetze"] else ""))
    if b["cv_satzlaengen"] is not None:
        cv = zahl_de(b["cv_satzlaengen"])
        if b["saetze"] < MIN_SAETZE_FUER_CV:
            print(f"Variationskoeffizient: {cv} (zu wenige Sätze für eine Bewertung, mindestens {MIN_SAETZE_FUER_CV})")
        else:
            urteil = "gleichförmig" if b["cv_verdaechtig"] else "unauffällig"
            print(f"Variationskoeffizient: {cv} ({urteil}, Grenze {zahl_de(CV_GRENZE, 1)})")

    for staerke, titel in (("stark", "Starke Muster"), ("schwach", "Schwache Muster")):
        auswahl = [f for f in b["funde"] if f["staerke"] == staerke]
        if not auswahl:
            continue
        print(f"\n{titel}")
        je_muster = OrderedDict()
        for f in auswahl:
            je_muster.setdefault((f["muster_id"], f["muster"]), []).append(f)
        for (mid, name), liste in je_muster.items():
            details = "; ".join(
                (f"„{f['text']}“ ×{f['anzahl']}" if f["kategorie"] in WORTLISTEN_KATEGORIEN
                 else f"{f['text']}" + (f" ×{f['anzahl']}" if f["anzahl"] > 1 else ""))
                + ("" if f["zaehlt"] else " (unter Schwelle)")
                for f in liste)
            print(f"  {mid} {name}: {details}")
    if not b["funde"]:
        print("\nKeine Muster gefunden.")
    print("\nHinweis: Hilfe, kein Urteil. Schwellen sind Faustregeln (SKILL.md, C2 und G1).")


def drucke_diff(d):
    print("Fakten-Abgleich")
    print("\nNeu in der Überarbeitung (prüfen, ob vom Nutzer belegt):")
    print("\n".join(f"  {x}" for x in d["neu"]) or "  keine")
    print("\nVerloren gegangen (prüfen, ob ein Muster das Streichen rechtfertigt):")
    print("\n".join(f"  {x}" for x in d["verloren"]) or "  keine")
    print("\nHinweis: „Name?“ ist eine Heuristik. Ausgeschriebene Zahlen („zwei“) erkennt der Abgleich nicht.")


WORTLISTEN_KATEGORIEN = set()


def main(argv=None):
    utf8_streams()
    parser = argparse.ArgumentParser(
        description="Muster- und Stilscanner für deutsche Texte (humanizer-de).")
    parser.add_argument("datei", nargs="?", default="-", help="Textdatei; ohne Angabe oder mit - wird stdin gelesen")
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben")
    parser.add_argument("--strict", action="store_true",
                        help="Exit-Code 1, wenn die Einschätzung „auffällig“ ist (bei --diff: wenn neue Fakten auftauchen)")
    parser.add_argument("--diff", nargs=2, metavar=("ORIGINAL", "NEU"),
                        help="Zahlen, Namen, Zitate und Links zwischen zwei Fassungen vergleichen")
    parser.add_argument("--muster", action="store_true", help="Musterliste mit Stufen als JSON ausgeben")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)

    wortliste = lade_wortliste()
    WORTLISTEN_KATEGORIEN.update(wortliste["kategorien"])

    if args.muster:
        print(json.dumps(wortliste["muster"], ensure_ascii=False, indent=2))
        return 0

    if args.diff:
        d = fakten_diff(lies_text(args.diff[0]), lies_text(args.diff[1]))
        print(json.dumps(d, ensure_ascii=False, indent=2)) if args.json else drucke_diff(d)
        return 1 if args.strict and d["neu"] else 0

    bericht = analysiere(lies_text(args.datei), wortliste)
    if args.json:
        print(json.dumps(bericht, ensure_ascii=False, indent=2))
    else:
        drucke_bericht(bericht)
    return 1 if args.strict and bericht["einschaetzung"]["stufe"] == "auffällig" else 0


if __name__ == "__main__":
    sys.exit(main())
