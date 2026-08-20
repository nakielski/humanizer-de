# humanizer-de

Skill zum Humanisieren deutscher Texte: erkennt und entfernt KI-typische Muster,
stilometrische Auffälligkeiten und Typografie-Fallen.

Privates Repository. Basiert konzeptionell auf
[blader/humanizer](https://github.com/blader/humanizer) (MIT), übertragen und
erweitert für die deutsche Sprache.

## Inhalt

| Datei | Zweck |
|---|---|
| `SKILL.md` | Der eigentliche Skill: 40 Muster in 7 Kategorien, Prozess, Beispiel |
| `scripts/analyse.py` | Stilometrie-Scanner: Satzlängen-CV, Füllwörter, Trikolon, Typografie |
| `references/wordlist.json` | Deutsche KI-Vokabular- und Floskel-Listen (12 Kategorien) |

## Schnellstart

```bash
python3 scripts/analyse.py textdatei.txt
cat brief.md | python3 scripts/analyse.py --json
```

Beispiel-Ausgabe:

```
Wörter: 412 | Sätze: 18
Satzlängen min/max: 6–34 Wörter
Variationskoeffizient Satzlängen: 0.312 (VERDÄCHTIG gleichförmig, Grenze 0.4)

Wort-/Floskelfunde:
  [floskeln_einleitung] In der heutigen Zeit x1
  [konnektoren_inflation] darüber hinaus x3
  ...
```

## Musterkatalog (Überblick)

- **A. Inhaltsmuster** — Bedeutungs-Aufblähung, Werbesprache, vage Autoritäten
- **B. Vokabular und Grammatik** — KI-Lieblingswörter, Kopula-Vermeidung, Trikolon
- **C. Struktur und Rhythmus** — Konnektoren-Inflation, gleichförmige Satzlängen
- **D. Typografie** — Gedankenstrich-Masse, US-Anführungszeichen, U+00A0
- **E. Kommunikation** — Chat-Reste, Wissenslücken-Disclaimer, Servilität
- **F. Seele** — Meinungslosigkeit, Detail-Armut, keine künstlichen Fehler
- **G. Tödliche Kombination** — Muster-Dichte entscheidet, nicht der Einzeltreffer

## Quellen

- [Wikipedia: Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte)
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (engl. Original)
- korrektur.de: Merkmale & Checkliste (CV-Grenzwert 0.4, Kansas-Studie, Cornell-Auswertung)
- contentconsultants.de: Typische Formulierungen und Muster
- ki-im-marketing.at: Strukturmerkmale

## Lizenz

MIT — siehe [LICENSE](LICENSE).
