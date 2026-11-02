# humanizer-de

Skill zum Humanisieren deutscher Texte: erkennt KI-typische Muster, Stilauffälligkeiten
und Typografie-Fallen und schreibt den Text um, ohne Fakten zu erfinden.

Basiert konzeptionell auf [blader/humanizer](https://github.com/blader/humanizer) (MIT),
übertragen und erweitert für die deutsche Sprache.

## Inhalt

| Datei | Zweck |
|---|---|
| `SKILL.md` | Der Skill: Grundregeln, Ablauf mit vier Modi, 48 Muster in 7 Kategorien mit Stärke-Stufen, Gesamtbeispiel |
| `scripts/analyse.py` | Scanner: Wendungen, Satzlängen, Strukturmuster, Typografie, Einschätzung, Fakten-Abgleich |
| `scripts/kalibrieren.py` | Misst den Scanner an einer eigenen Textsammlung, um Schwellen zu prüfen |
| `scripts/export_portabel.py` | Erzeugt eine Kopie nach Agent-Skills-Spezifikation (z. B. für Claude) |
| `references/wordlist.json` | Muster-Tabelle mit Stufen und Wortlisten je Muster |
| `tests/` | pytest-Suite: Katalogbeispiele gegen Skript, deutsche Sonderfälle, Konsistenz der SKILL.md |

## Schnellstart

```bash
python3 scripts/analyse.py text.md                 # Bericht
cat brief.md | python3 scripts/analyse.py --json   # JSON für Agenten
python3 scripts/analyse.py --diff alt.md neu.md    # Was ist neu, was fehlt?
python3 scripts/analyse.py --ohne-gedankenstriche text.md   # Hausregel: Exit 1 bei jedem Gedankenstrich
```

Ausgabe für das Vorher-Beispiel aus der SKILL.md (gekürzt):

```
Einschätzung: auffällig (starke Muster: A1, A5, B3, B9, C4, C7, E1, E3; schwache: B1, B2, B4, D1)
Umfang: 169 Wörter, 16 Sätze, Satzlänge 2 bis 21 Wörter
Variationskoeffizient: 0,582 (unauffällig, Grenze 0,3)

Starke Muster
  A1 Bedeutungs-Aufblähung: „Zeugnis für“ ×1; „Wendepunkt“ ×1
  A5 Vage Autoritäten: „Branchenbeobachter“ ×1
  B3 Negative Parallelismen: „Es geht nicht (nur) um …“ ×1
  ...
```

Der Fakten-Abgleich listet Zahlen, Namen, Zitate und Links, die in einer Überarbeitung
neu dazugekommen oder verloren gegangen sind. Damit lässt sich prüfen, dass beim
Umschreiben nichts erfunden wurde.

## Musterkatalog (Überblick)

Jedes Muster ist als *stark* (rechtfertigt allein eine Änderung) oder *schwach* (zählt nur
in Kombination) eingestuft.

- **A. Inhaltsmuster:** Bedeutungs-Aufblähung, Werbesprache, vage Autoritäten, Strohmann
- **B. Vokabular und Grammatik:** KI-Lieblingswörter, Kopula-Vermeidung, Antithesen, Trikolon, Lehnübersetzungen
- **C. Struktur und Rhythmus:** Konnektoren-Inflation, gleichförmige Satzlängen, Schablonen-Einstiege, dramatische Fragmente
- **D. Typografie:** Gedankenstrich-Masse, falsche Anführungszeichen, unsichtbare Zeichen, Emojis
- **E. Kommunikation:** Chat-Reste, Wissenslücken-Disclaimer, Servilität
- **F. Seele:** Meinungslosigkeit, Detail-Armut, keine künstlichen Fehler
- **G. Kombination:** Musterdichte entscheidet, nicht der Einzeltreffer

## Kalibrierung

Die Schwellen der schwachen Signale sind so gesetzt, dass jedes bei etwa 5 Prozent
menschlicher Texte anschlägt. Gemessen an 1.028 Nachrichtentexten aus
[10kGNAD](https://github.com/tblock/10kGNAD) (DER STANDARD, 2015/16), geprüft an 2.000
weiteren: 88 Prozent „unauffällig“, unter 1 Prozent „auffällig“. Gegen KI-Texte ist noch
nicht kalibriert. Dafür eigene Texte von vor Ende 2022 und aktuelle Modelltexte getrennt messen:

```bash
python3 scripts/kalibrieren.py meine-texte/
python3 scripts/kalibrieren.py ki-texte/
```

## Hermes und andere Agenten

`SKILL.md` folgt dem Hermes-Format (`version`, `author`, `platforms` auf oberster Ebene).
Die Agent-Skills-Spezifikation erlaubt dort nur `name`, `description`, `license`,
`compatibility`, `metadata` und `allowed-tools`. Für Claude und andere Agenten erzeugt
`python3 scripts/export_portabel.py` eine konforme Kopie in `dist/humanizer-de/`.

## Hausregeln

Feste Vorgaben des Nutzers (z. B. „keine Gedankenstriche“) gelten im Skill ohne Toleranz und
unabhängig von der Einschätzung. Für diese Regel prüft `--ohne-gedankenstriche` jede Zeile:
Halbgeviertstrich mit Leerzeichen, Geviertstrich und „ - “ als Ersatz. Bis- und Streckenstriche
(„12–14“, „Köln–Bonn“), Bindestriche in Wörtern, Listenmarken und Code bleiben unberührt.

Damit eine Hausregel auch greift, wenn ein Agent den Skill gerade nicht lädt, gehört sie
zusätzlich in seine dauerhafte Konfiguration (bei Hermes in die `SOUL.md` der Profile).

## Tests

```bash
python3 -m pytest tests
```

## Quellen

- [Wikipedia: Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte)
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (engl. Original)
- Desaire et al. (2023): *Distinguishing academic science writing from humans or ChatGPT with
  over 99% accuracy using off-the-shelf machine learning tools.* Cell Reports Physical Science.
  64 menschliche und 128 ChatGPT-Fachtexte (Science-Perspectives), 20 Merkmale, darunter
  Satzlängenvariation und Absatzstruktur; ganze Dokumente nahezu fehlerfrei, Absätze zu 92 Prozent.
  Die Studie nennt keine Richtung für Gedankenstriche; D1 ist Erfahrungswissen.
- Kobak et al. (2025): *Delving into LLM-assisted writing in biomedical publications through
  excess vocabulary.* Science Advances (doi:10.1126/sciadv.adt3813). Über 15 Millionen
  PubMed-Abstracts 2010 bis 2024; mindestens 13,5 Prozent der Abstracts von 2024 mit LLM bearbeitet.
- [blader/humanizer](https://github.com/blader/humanizer) (MIT, Siqi Chen): Nummerierung und
  Grundidee. Die aktuelle Fassung führt Synonym-Karussell (B5) und falsche Spannen (B6) nicht mehr
  und behandelt Gedankenstriche als schwaches Signal.
- korrektur.de, contentconsultants.de, ki-im-marketing.at: deutschsprachige Praxisbeobachtungen

## Lizenz

MIT, siehe [LICENSE](LICENSE).
