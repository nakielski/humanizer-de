#!/usr/bin/env python3
"""Misst, wie analyse.py auf einer Textsammlung anschlägt.

Gedacht für die Kalibrierung: einmal mit eigenen Texten von vor Ende 2022
(sicher menschlich), einmal mit Texten aktueller Modelle zu ähnlichen Themen.
Gute Schwellen trennen die beiden Läufe; die aktuellen Werte in analyse.py
sind nur an menschlichen Nachrichtentexten gemessen.

Aufruf:
    python3 scripts/kalibrieren.py ORDNER            (*.md und *.txt, rekursiv)
    python3 scripts/kalibrieren.py DATEI.csv --spalte 2 --trenner ";"
    ... --json                                       (Ergebnis als JSON)
"""
import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse  # noqa: E402

PERZENTILE = (5, 25, 50, 75, 95)


def lade_texte(quelle, spalte, trenner):
    pfad = Path(quelle)
    if pfad.is_dir():
        dateien = sorted(p for p in pfad.rglob("*") if p.suffix.lower() in (".md", ".txt"))
        return [(str(p), analyse.lies_text(str(p))) for p in dateien]
    if pfad.suffix.lower() == ".csv":
        csv.field_size_limit(10 ** 8)
        with open(pfad, encoding="utf-8-sig", newline="") as f:
            zeilen = list(csv.reader(f, delimiter=trenner, quotechar="'" if trenner == ";" else '"'))
        return [(f"{pfad.name}:{i}", z[spalte - 1]) for i, z in enumerate(zeilen, 1) if len(z) >= spalte]
    return [(str(pfad), analyse.lies_text(str(pfad)))]


def perzentil(werte, p):
    if not werte:
        return None
    w = sorted(werte)
    return w[min(len(w) - 1, int(round(p / 100 * (len(w) - 1))))]


def kalibriere(texte):
    wortliste = analyse.lade_wortliste()
    stufen = collections.Counter()
    muster = collections.Counter()
    messwerte = {"cv": [], "gedankenstriche_pro_1000": [], "komposita_pro_1000": [], "trikola_pro_1000": []}
    for _, text in texte:
        b = analyse.analysiere(text, wortliste)
        stufen[b["einschaetzung"]["stufe"]] += 1
        for mid in {f["muster_id"] for f in b["funde"] if f["zaehlt"]}:
            muster[mid] += 1
        n = b["woerter"]
        if not n:
            continue
        if b["cv_satzlaengen"] is not None and b["saetze"] >= analyse.MIN_SAETZE_FUER_CV:
            messwerte["cv"].append(b["cv_satzlaengen"])
        roh = analyse.zerlege(text)["roh"]
        messwerte["gedankenstriche_pro_1000"].append(len(re.findall(r"(?<=[ \t])–(?=\s)", roh)) / n * 1000)
        for mid, schluessel in (("B11", "komposita_pro_1000"), ("B4", "trikola_pro_1000")):
            treffer = sum(f["anzahl"] for f in b["funde"] if f["muster_id"] == mid)
            messwerte[schluessel].append(treffer / n * 1000)
    anzahl = len(texte)
    return {
        "texte": anzahl,
        "stufen": {s: stufen[s] for s in ("unauffällig", "prüfen", "auffällig")},
        "anteil_je_muster": {mid: round(c / anzahl, 3) for mid, c in muster.most_common()} if anzahl else {},
        "perzentile": {name: {f"P{p}": (round(perzentil(w, p), 3) if w else None) for p in PERZENTILE}
                       for name, w in messwerte.items()},
        "aktuelle_schwellen": {
            "cv": analyse.CV_GRENZE,
            "gedankenstriche_pro_1000": analyse.GEDANKENSTRICHE_PRO_1000,
            "komposita_pro_1000": analyse.KOMPOSITA_PRO_1000,
            "trikola_pro_1000": analyse.TRIKOLA_PRO_1000,
        },
    }


def drucke(e):
    n = e["texte"] or 1
    print(f"Texte: {e['texte']}")
    for stufe, c in e["stufen"].items():
        print(f"  {stufe:12s} {c:5d}  ({c / n * 100:.1f} %)".replace(".", ","))
    print("\nAnteil der Texte, in denen ein Muster zählt:")
    for mid, anteil in e["anteil_je_muster"].items():
        print(f"  {mid:4s} {anteil * 100:5.1f} %".replace(".", ","))
    print("\nPerzentile (aktuelle Schwelle in Klammern):")
    for name, werte in e["perzentile"].items():
        teile = "  ".join(f"{p}={'–' if v is None else str(v).replace('.', ',')}" for p, v in werte.items())
        print(f"  {name:26s} {teile}  ({str(e['aktuelle_schwellen'][name]).replace('.', ',')})")


def main():
    analyse.utf8_streams()
    parser = argparse.ArgumentParser(description="Misst analyse.py an einer Textsammlung.")
    parser.add_argument("quelle", help="Ordner mit .md/.txt, eine CSV-Datei oder eine Textdatei")
    parser.add_argument("--spalte", type=int, default=1, help="CSV: Spalte mit dem Text (ab 1)")
    parser.add_argument("--trenner", default=",", help="CSV: Feldtrenner")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    ergebnis = kalibriere(lade_texte(args.quelle, args.spalte, args.trenner))
    if args.json:
        print(json.dumps(ergebnis, ensure_ascii=False, indent=2))
    else:
        drucke(ergebnis)


if __name__ == "__main__":
    main()
