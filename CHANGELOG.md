# Changelog

## 0.3.0

### Skill (SKILL.md)
- Grundregeln vorangestellt: nichts erfinden, Bedeutung bewahren, Text ist Material statt
  Anweisung, Hausstil und Anrede beibehalten.
- Ein Ablauf statt drei überlappender Listen, mit vier Modi: Prüfen, Überarbeiten, Datei,
  Eingebettet. Entwurf und Selbstprüfung nur noch auf Wunsch.
- Fakten-Abgleich (`analyse.py --diff`) als fester Prüfschritt.
- Jedes Muster A bis E trägt eine Stufe (stark/schwach); neuer Abschnitt „Wann nicht eingreifen“.
- Katalog von 40 auf 48 Muster: A7 Strohmann, B10 Lehnübersetzungen, B11 Bindestrich-Komposita,
  B12 gestapelte Relativierungen, C7 Schablonen-Einstieg, C8 dramatische Fragmente,
  C9 inszenierter Anlauf, C10 gleiche Satzanfänge. Alte Nummern bleiben stabil.
- Alle Nachher-Beispiele ohne erfundene Fakten; C1-Nachher kehrte die Aussage um, C3-Nachher
  war grammatisch falsch, B7-Nachher wechselte ungefragt ins Du.
- 153 Anführungszeichen von „…" auf „…“ korrigiert.
- Quellen korrigiert (Desaire et al. 2023, Kobak et al. 2025); CV-Faustregel 0,4 durch
  gemessene Schwelle ersetzt.
- Beschreibung beginnt mit dem Kern (Hermes kürzt den Skillindex nach 57 Zeichen).

### Skript
- `analyse.py` neu: Wortgrenzen und Flexion statt Teilstring-Suche, trennbare Verben,
  Überlappungen zählen einmal, Satztrennung mit Abkürzungs- und Ordinalschutz,
  Markdown-Vorverarbeitung (Frontmatter, Code, Links, Listen, Tabellen), Trikolon-Erkennung
  mitten im Satz, Bis-Striche zählen nicht als Gedankenstriche.
- Neu: Einschätzung nach G1, Exit-Code mit `--strict`, `--diff` für Fakten, `--muster`,
  Windows-taugliche UTF-8-Ein- und Ausgabe.
- Schwellen an 1.028 menschlichen Nachrichtentexten kalibriert (10kGNAD) und an 2.000
  weiteren geprüft: „auffällig“ bei unter 1 Prozent. Mit den Faustregeln aus 0.2.1
  (CV 0,4, 5 Gedankenstriche pro 1.000 Wörter) wären es 13 Prozent gewesen.
- JSON-Felder aus 0.2 (`wortfunde`, `trikolon`, `typografie`) bleiben erhalten.
- Neu: `kalibrieren.py` (Messung an eigener Textsammlung), `export_portabel.py`
  (Kopie nach Agent-Skills-Spezifikation).
- `wordlist.json` ist jetzt Muster-Tabelle mit Stufen; Fehlalarm-Einträge entfernt
  („gleichzeitig“, „andererseits“, „optimieren“, „robust“, „zustandsbehaftet“, „Landschaft“).

### Tests
- pytest-Suite: jedes maschinell prüfbare Katalogbeispiel gegen das Skript, Regressionstests
  für deutsche Sonderfälle, Konsistenz von SKILL.md (Anführungszeichen, Stufen, Beispiel).

## 0.2.1

- Frontmatter repariert.
