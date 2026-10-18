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

## Tests

```bash
python3 -m pytest tests
```

## Quellen

- [Wikipedia: Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte)
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (engl. Original)
- Desaire et al. (2023), Cell Reports Physical Science: Stilmerkmale von ChatGPT-Fachtexten
- Kobak et al. (2025), Science Advances: Stilwörter in über 15 Millionen PubMed-Abstracts
- korrektur.de, contentconsultants.de, ki-im-marketing.at: deutschsprachige Praxisbeobachtungen

## Lizenz

MIT, siehe [LICENSE](LICENSE).
