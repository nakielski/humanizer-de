#!/usr/bin/env python3
"""Stilometrie- und Muster-Scanner für deutsche Texte.

Misst, was sich zählen lässt:
- Variationskoeffizient der Satzlängen (CV < 0.4 gilt als verdächtig gleichförmig)
- KI-Vokabular- und Füllwort-Dichte (Wortliste references/wordlist.json)
- Trikolon-Tendenz (Listen mit exakt drei Items, drei gleich strukturierte Aufzählungen)
- Typografie-Verdacht (Gedankenstrich-Dichte, US-Anführungszeichen, geschützte
  Leerzeichen, Doppelleerzeichen nach Punkt, Mittelpunkt-Bullets, Leerzeichen
  am Absatzanfang)

Aufruf:
    python3 analyse.py <datei>
    cat datei | python3 analyse.py
    python3 analyse.py --json <datei>

Das Skript ist eine Hilfe, kein Urteil: Der Musterkatalog in SKILL.md und das
eigenen Sprachgefühl entscheiden, die Zahlen liefern nur Anhaltspunkte.
"""
import json
import math
import re
import sys
from pathlib import Path

THRESHOLD_CV = 0.4
MIN_SAETZE_FUER_CV = 10  # darunter ist der CV nicht aussagekräftig

# Fallback-Wortliste, falls references/wordlist.json fehlt
FALLBACK = {
    "ki_vokabular": ["essenziell", "vielfältig", "nahtlos", "maßgeschneidert",
                     "umfassend", "ganzheitlich", "präzise", "strukturell"],
    "konnektoren_inflation": ["darüber hinaus", "außerdem", "zusätzlich",
                              "ferner", "des Weiteren", "nicht zuletzt"],
    "floskeln_einleitung": ["In der heutigen Zeit", "In einer Welt, in der",
                            "Immer mehr Menschen fragen sich"],
    "floskeln_fazit": ["Zusammenfassend lässt sich sagen",
                       "Abschließend lässt sich sagen",
                       "Insgesamt lässt sich festhalten"],
    "chat_reste": ["Ich hoffe, das hilft", "Natürlich!", "Gute Frage!",
                   "Sie haben völlig recht", "Lassen Sie mich wissen"],
    "wissensluecken": ["Stand meines letzten Wissens",
                       "Bis zu meinem letzten Update",
                       "basierend auf verfügbaren Informationen"],
    "negative_parallelismen": ["nicht nur", "sondern auch",
                               "Es geht nicht nur um"],
    "bedeutungs_aufblaehung": ["Zeugnis für", "steht als", "dient als",
                               "unterstreicht die Bedeutung", "Wendepunkt"],
    "kopula_vermeidung": ["dient als", "fungiert als", "stellt dar",
                          "zeichnet sich aus"],
}


def lade_wortliste():
    hier = Path(__file__).resolve().parent
    p = hier.parent / "references" / "wordlist.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return FALLBACK


def lies_text(pfad=None):
    if pfad and pfad != "-":
        return Path(pfad).read_text(encoding="utf-8")
    return sys.stdin.read()


def satzlängen(text):
    # Absätze respektieren, Markdown-Strukturen ignorieren
    saetze = re.split(r"(?<=[.!?])\s+", text)
    laengen = []
    for s in saetze:
        w = re.findall(r"[\wäöüßÄÖÜ']+", s)
        if len(w) >= 2:
            laengen.append(len(w))
    return laengen


def variationskoeffizient(laengen):
    if len(laengen) < 3:
        return None
    mittel = sum(laengen) / len(laengen)
    if mittel == 0:
        return None
    var = sum((x - mittel) ** 2 for x in laengen) / len(laengen)
    return math.sqrt(var) / mittel


def wortfunde(text, wortliste):
    funde = []
    t = " " + re.sub(r"\s+", " ", text) + " "
    t_lower = t.lower()
    for kategorie, woerter in wortliste.items():
        for w in woerter:
            n = t_lower.count(w.lower())
            if n:
                funde.append((kategorie, w, n))
    return funde


def trikolon_funde(text):
    funde = []
    # Aufzählungen: "a, b und c" mit ähnlicher Wortzahl
    for m in re.finditer(
        r"([A-ZÄÖÜ]?[\wäöüß-]+(?:\s+[\wäöüß-]+)*),\s*"
        r"([A-ZÄÖÜ]?[\wäöüß-]+(?:\s+[\wäöüß-]+)*),?\s+und\s+"
        r"([A-ZÄÖÜ]?[\wäöüß-]+(?:\s+[\wäöüß-]+)*)",
        text,
    ):
        teile = [len(m.group(i).split()) for i in (1, 2, 3)]
        if max(teile) - min(teile) <= 1 and min(teile) >= 1:
            funde.append(m.group(0)[:60])
    # Bullet-Listen mit exakt drei Punkten
    bloecke = re.split(r"\n\s*\n", text)
    for block in bloecke:
        items = re.findall(r"^\s*[-*•]\s+(.+)$", block, re.M)
        if len(items) == 3:
            funde.append("3er-Liste: " + " | ".join(i[:25] for i in items))
    return funde


def typografie_funde(text):
    funde = []
    n_em = len(re.findall(r"—", text))
    n_halb = len(re.findall(r"–", text))
    woerter = len(re.findall(r"\w+", text))
    if n_em:
        funde.append(f"em-dash (—): {n_em}")
    pro_mille = (n_halb / woerter * 1000) if woerter else 0
    if pro_mille > 5:
        funde.append(f"Halbgeviertstrich (–): {n_halb} ({pro_mille:.1f} pro 1000 Wörter, Grenze 5)")
    if re.search(r'\"', text):
        funde.append("gerade US-Anführungszeichen (\")")
    if "•" in text:
        funde.append("Mittelpunkt-Bullet (•)")
    n_nbsp = len(re.findall(r"\u00a0", text))
    if n_nbsp:
        funde.append(f"geschütztes Leerzeichen U+00A0: {n_nbsp}")
    n_narrow = len(re.findall(r"\u202f", text))
    if n_narrow:
        funde.append(f"schmales Leerzeichen U+202F: {n_narrow}")
    n_double = len(re.findall(r"\.  +\w", text))
    if n_double:
        funde.append(f"Doppelleerzeichen nach Punkt: {n_double}")
    # Leerzeichen am Absatzanfang
    n_indent = len(re.findall(r"(?m)^ +\S", text))
    if n_indent:
        funde.append(f"Leerzeichen am Absatzanfang: {n_indent}")
    return funde


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    pfad = args[0] if args else None

    text = lies_text(pfad)
    wortliste = lade_wortliste()
    laengen = satzlängen(text)
    cv = variationskoeffizient(laengen)

    bericht = {
        "woerter": len(re.findall(r"\w+", text)),
        "saetze": len(laengen),
        "satzlaengen_min_max": [min(laengen), max(laengen)] if laengen else [0, 0],
        "cv_satzlaengen": round(cv, 3) if cv is not None else None,
        "cv_verdaechtig": (cv is not None and len(laengen) >= MIN_SAETZE_FUER_CV
                           and cv < THRESHOLD_CV),
        "wortfunde": [
            {"kategorie": k, "wort": w, "anzahl": n}
            for k, w, n in wortfunde(text, wortliste)
        ],
        "trikolon": trikolon_funde(text),
        "typografie": typografie_funde(text),
    }

    if as_json:
        print(json.dumps(bericht, ensure_ascii=False, indent=2))
        return

    print(f"Wörter: {bericht['woerter']} | Sätze: {bericht['saetze']}")
    if bericht["satzlaengen_min_max"] != [0, 0]:
        print(f"Satzlängen min/max: {bericht['satzlaengen_min_max'][0]}–"
              f"{bericht['satzlaengen_min_max'][1]} Wörter")
    if cv is not None:
        if len(laengen) < MIN_SAETZE_FUER_CV:
            print(f"Variationskoeffizient Satzlängen: {cv:.3f} "
                  f"(zu wenige Sätze für eine Bewertung, min. {MIN_SAETZE_FUER_CV})")
        else:
            marker = "VERDÄCHTIG gleichförmig" if bericht["cv_verdaechtig"] else "ok"
            print(f"Variationskoeffizient Satzlängen: {cv:.3f} ({marker}, Grenze {THRESHOLD_CV})")
    if bericht["wortfunde"]:
        print("\nWort-/Floskelfunde:")
        for f in bericht["wortfunde"]:
            print(f"  [{f['kategorie']}] {f['wort']} x{f['anzahl']}")
    if bericht["trikolon"]:
        print("\nTrikolon-Tendenz:")
        for t in bericht["trikolon"]:
            print(f"  {t}")
    if bericht["typografie"]:
        print("Typografie-Verdacht:")
        for t in bericht["typografie"]:
            print(f"  {t}")
    if not (bericht["wortfunde"] or bericht["trikolon"] or bericht["typografie"]):
        print("\nKeine Auffälligkeiten in Wortlisten, Trikolon oder Typografie.")


if __name__ == "__main__":
    main()
