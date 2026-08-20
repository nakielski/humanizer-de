---
name: humanizer-de
version: 0.2.0
description: Deutsche Texte menschlich klingen lassen: erkennt und entfernt KI-typische Muster, stilometrische Auffälligkeiten und Typografie-Fallen.
license: MIT
compatible-environments: [claude-code, claude-code-action, opencode, hermes]
keywords: [humanisieren, menschelei, ki-texte, de-ai, deutsche-texte, prose, editing]
---

# Humanizer DE

Deutsche Texte so überarbeiten, dass sie wie von einem Menschen geschrieben klingen. Der Skill erkennt KI-typische Muster in deutschen Texten und ersetzt sie durch natürliche Sprache.

**Kernidee:** Sprachmodelle raten statistisch, was als Nächstes kommt. Das Ergebnis driftet zur wahrscheinlichsten Fortsetzung, und daraus entstehen fast alle Muster unten. Wer die Muster kennt, kann sie gezielt brechen.

Grundlagen sind die deutsche Wikipedia-Seite „Anzeichen für KI-generierte Inhalte" (angepasste Übersetzung von „Wikipedia:Signs of AI writing", gepflegt von WikiProject AI Cleanup), Auswertungen deutschsprachiger Lektorate (korrektur.de, contentconsultants.de) sowie stilometrische Studien (Universität Kansas; Cornell-Auswertung von 14 Millionen Peer-Reviews). Quellen im Einzelnen siehe Attribution unten.

## Wann dieser Skill geladen wird

- Der Nutzer will einen Text „humanisieren", „ent-KI-en", „menschlicher formulieren" oder „ChatGPT-Spuren entfernen"
- Ein deutscher Text soll vor dem Veröffentlichen geprüft werden, ob er KI-Tells zeigt
- Die eigene KI-gestützte Ausgabe (Mail, Blogpost, LinkedIn-Post, Doku, Bewerbung) soll vor dem Absenden natürlich klingen
- Der Nutzer liefert eine Schreibprobe und bittet, den Text in seinem Stil zu überarbeiten

## Arbeitsweise

Der Text kommt inline, als Datei (mit read_file laden) oder mit einer Schreibprobe zur Stil-Anpassung.

1. **Scan.** Text gegen alle Muster unten durchgehen. Fundstellen zählen und benennen.
2. **Stil messen.** scripts/analyse.py ausführen: Satzlängen-Streuung, Füllwörter, Trikolon-Tendenz, Typografie-Verdacht. Ergebnisse in die Überarbeitung einfließen lassen.
3. **Umfeld prüfen.** Konnektoren-Dichte, Absatzsymmetrie, Einleitungs- und Fazit-Floskeln, Listenform.
4. **Umschreiben.** Jede Fundstelle überarbeiten, Bedeutung bewahren, Ton beibehalten.
5. **Stimme kalibrieren.** Bei Schreibprobe: Rhythmus, Wortschatz und Satzzeichen der Probe nachbilden. Ohne Probe: Details, klare Meinung, Ich-Form wo es passt.
6. **Anti-KI-Durchgang.** Frage: „Was lässt diesen Text noch KI-generiert wirken?" Verbleibende Tells benennen, nochmal überarbeiten.
7. **Ergebnis zeigen.** Umschreibung immer vorlegen; bei Dateien zusätzlich die geänderten Stellen (patch statt Komplett-Rewrite, wo möglich).

## MUSTERKATALOG

40 Muster in sieben Kategorien (A bis G). Nummerierung angelehnt an das englische Original (blader/humanizer), Beispiele komplett auf Deutsch und praxisnah.

### A. Inhaltsmuster

**A1. Bedeutungs-Aufblähung.** Wörter: „ist ein Zeugnis für", „steht als", „dient als", „spielt eine wichtige Rolle", „unterstreicht die Bedeutung", „Wendepunkt", „Schlüsselmoment", „tief verwurzelt", „hinterlässt bleibenden Eindruck", „fasziniert weiterhin", „festigt". KI bläht Belangloses zu Bedeutungsschwerem auf.
> Vorher: Das Statistische Institut wurde 1989 gegründet und markiert einen Wendepunkt in der Geschichte der Regionalstatistik.
> Nachher: Das Statistische Institut wurde 1989 gegründet, um Regionalstatistiken unabhängig vom Bundesamt zu erheben.

**A2. Notabilitäts-Behauptung.** Wörter: „unabhängige Berichterstattung", „überregionale Medien", „führender Experte", „aktive Social-Media-Präsenz". Behauptete Bedeutung statt belegter.
> Vorher: Ihre Ansichten wurden von der NYT, der BBC und dem Guardian zitiert. Sie unterhält einen aktiven YouTube-Kanal mit über 100.000 Abonnenten.
> Nachher: In einem Zeit-Interview von 2024 sagte sie, KI-Regulierung solle Ergebnisse statt Methoden prüfen.

**A3. Oberflächliche Partizipial-Anhängsel.** Wörter: „…, was … unterstreicht", „…, wodurch … gewährleistet wird", „…, das … widerspiegelt", „…, der … hervorhebt". Angeklebte Schein-Analyse. Deutsche Partizipialkonstruktionen (Partizip I) sind im menschlichen Deutsch seltener als englische -ing-Formen.
> Vorher: Die Farbpalette blau-gold-grün spiegelt die landschaftliche Vielfalt der Region wider, was die tiefe Verbindung der Gemeinde zu ihrer Umwelt unterstreicht.
> Nachher: Die Farben blau, gold und grün sind nicht zufällig gewählt. Der Architekt sagte, sie sollen an die Küste erinnern.

**A4. Werbesprache.** Wörter: „reiches kulturelles Erbe", „reiche Geschichte", „atemberaubend", „beeindruckende natürliche Schönheit", „unbedingt besuchen", „bleibendes Vermächtnis", „eingebettet", „im Herzen von", „beeindruckende Vielfalt". LLMs halten keinen neutralen Ton, besonders bei Kulturerbe-Themen.
> Vorher: Eingebettet in die atemberaubende Landschaft der Dolomiten, beeindruckt der Ort mit einem reichen kulturellen Erbe und einer beeindruckenden Vielfalt an Sehenswürdigkeiten.
> Nachher: Der Ort liegt in den Dolomiten und hat ein Heimatmuseum sowie zwei Kirchen aus dem 16. Jahrhundert.

**A5. Vage Autoritäten.** Wörter: „Branchenberichte", „Beobachter führen an", „einige Kritiker argumentieren", „viele Experten sind sich einig". Meinung wird einer ungenannten Autorität zugeschrieben.
> Vorher: Viele Experten sind sich einig, dass der Fluss eine entscheidende Rolle im Ökosystem spielt.
> Nachher: Eine Untersuchung der Universität Rostock von 2019 zählt im Fluss vier endemische Fischarten.

**A6. Herausforderungen-und-Zukunft-Floskeln.** Wörter: „Trotz dieser Erfolge …", „steht vor mehreren Herausforderungen", „Vermächtnis", „Zukunftsaussichten". Formelhafter Herausforderungen-Abschnitt.
> Vorher: Trotz der wirtschaftlichen Stärken steht der Stadtteil vor Herausforderungen, bleibt aber ein integraler Bestandteil der urbanen Entwicklung.
> Nachher: Der Wohnungsmarkt ist angespannt: Die Stadt hat seit 2015 nur 400 neue Wohnungen genehmigt, bei 2.000 Bedarf.

### B. Vokabular und Grammatik

**B1. KI-Lieblingsvokabular.** Häufige Wörter: „essenziell", „vielfältig", „nahtlos", „maßgeschneidert", „umfassend", „ganzheitlich", „eintauchen" (figurativ), „präzise" (als Füll-Adjektiv), „strukturell", „Robustheit", „Landschaft" (im übertragenen Sinn), „nahtlos integriert". Diese Wörter treten seit 2023 deutlich häufiger auf und koinzidieren oft. Sie klingen überzeugt, wo ein Mensch abwägen würde.
> Vorher: Die Plattform bietet eine umfassende und ganzheitliche Lösung, die sich nahtlos integrieren lässt.
> Nachher: Die Plattform deckt alles ab: Import, Prüfung, Export. Sie lässt sich in eine bestehende CI-Pipeline einhängen.

**B2. Kopula-Vermeidung.** Wörter: „dient als", „stellt … dar", „bildet … ab", „fungiert als", „zeichnet sich aus durch". Vermeidung von schlichtem „ist".
> Vorher: Die Halle dient als Ausstellungsort für moderne Kunst und zeichnet sich durch flexible Grundrisse aus.
> Nachher: Die Halle ist ein Ausstellungsort für moderne Kunst. Die Grundrisse sind flexibel.

**B3. Negative Parallelismen.** „Es ist nicht nur …, es ist …" / „nicht nur …, sondern auch" in gehäufter Form. Aus dem Englischen übernommene Antithesen-Rhetorik: „Das ist nicht smart. Das ist öde."
> Vorher: Es geht nicht nur um Automatisierung, sondern um einen Paradigmenwechsel.
> Nachher: Automatisierung spart hier etwa zwei Stunden pro Woche. Ein Paradigmenwechsel ist das nicht.

**B4. Trikolon (Dreierregel).** LLMs zwingen Ideen in Dreiergruppen: drei Adjektive, drei Aufzählungen, drei Tipps. Im Deutschen oft als „sowohl … als auch … und".
> Vorher: Das Event bietet inspirierende Keynotes, spannende Panels und intensive Networking-Möglichkeiten.
> Nachher: Das Event hat Vorträge am Vormittag, Panels am Nachmittag. Dazwischen ist Zeit für Gespräche.

**B5. Synonym-Karussell.** Dasselbe Konzept wird in aufeinanderfolgenden Sätzen durchsynonymisiert: Protagonist/Hauptfigur/zentrale Figur/Held. Menschen wiederholen das passende Wort; KI variiert künstlich.
> Vorher: Der Protagonist wächst an seinen Aufgaben. Die Hauptfigur erhält Unterstützung von der Mentorin. Die zentrale Figur scheitert trotzdem.
> Nachher: Der Protagonist wächst an seinen Aufgaben, erhält Unterstützung von der Mentorin und scheitert trotzdem.

**B6. Falsche Spannen.** „von … bis …" ohne echte Skala: „von der Fehleranalyse bis zur Prozessoptimierung". Wenn X und Y nicht auf einer gemeinsamen Skala liegen, ist es ein echtes Spannen-Muster.
> Vorher: Die Reise führte von den Anfängen des Handwerks bis zur Moderne, von traditionellen Techniken bis zu digitalen Werkzeugen.
> Nachher: Das Buch beginnt mit den Zünften des 15. Jahrhunderts und endet mit CAD-Software der Gegenwart.

**B7. Passiv und subjektlose Fragmente.** „Eine Konfigurationsdatei wird nicht benötigt." Passiv ohne Akteur wirkt bürokratisch; im Deutschen fällt das schneller auf als im Englischen.
> Vorher: Eine Konfigurationsdatei wird nicht benötigt. Die Ergebnisse werden automatisch gespeichert.
> Nachher: Du brauchst keine Konfigurationsdatei. Das Tool speichert die Ergebnisse selbst.

**B8. Ausgeschriebene Abkürzungen.** KI schreibt „zum Beispiel", „unter anderem", „beziehungsweise", „das heißt" aus, wo erfahrene Schreiber z. B., u. a., bzw., d. h. setzen (korrektur.de). Umgekehrt gilt: Wer nie abkürzt, wirkt wie ein Modell. Abkürzen, wo es im Kontext üblich ist — aber nicht mechanisch überall.
> Vorher: Das gilt zum Beispiel für Konfigurationen, aber auch für Tests, insbesondere bei Integrationstests, das heißt bei mehreren Komponenten.
> Nachher: Das gilt z. B. für Konfigurationen und Tests, insbesondere Integrationstests mit mehreren Komponenten.

**B9. Autoritäts-Tropen.** „Die eigentliche Frage ist …", „Im Kern geht es um …", „Im Grunde genommen …", „tiefgreifend". Feierlicher Anschein von Tiefe, der danach nur Gewöhnliches wiederholt.
> Vorher: Die eigentliche Frage ist, ob Teams mitziehen. Im Kern geht es um Bereitschaft zur Veränderung.
> Nachher: Die Frage ist, ob die Teams mitziehen. Das hängt davon ab, ob sie ihre Gewohnheiten ändern wollen.

### C. Struktur und Rhythmus

**C1. Konnektoren-Inflation.** „darüber hinaus", „außerdem", „zusätzlich", „ferner", „des Weiteren", „nicht zuletzt". In akademischen Texten üblich, in KI-Texten mechanisch übermäßig. Der wichtigste Satzverbinder des Deutschen ist das vorangestellte Verb.
> Vorher: Das Tool beschleunigt die Prüfung. Darüber hinaus reduziert es Fehler. Außerdem spart es Kosten. Ferner verbessert es die Nachvollziehbarkeit.
> Nachher: Das Tool beschleunigt die Prüfung, reduziert Fehler und spart Kosten. Die Nachvollziehbarkeit leidet allerdings.

**C2. Gleichförmige Satzlängen.** Menschen variieren zwischen 5 und 40 Wörtern pro Satz, Modelle pendeln zuverlässig zwischen 15 und 25. Variationskoeffizient der Satzlängen unter 0,4 gilt als verdächtig (Studie Universität Kansas: 94 Prozent Genauigkeit allein mit Satzlänge, Wortvielfalt, Punktdichte).
> Vorher: Das Team stellte die Architektur vor. Die Architektur umfasst drei Ebenen. Jede Ebene hat klare Aufgaben. Die Aufgaben sind dokumentiert.
> Nachher: Das Team stellte die Architektur vor. Drei Ebenen, jede mit klaren, dokumentierten Aufgaben.

**C3. Absatz- und Listensymmetrie.** Einleitung mit drei Sätzen, drei Hauptpunkte mit je drei Unterpunkten, dreigliedriges Fazit („Drei-Drei-Drei-Architektur"). Bullet-Listen mit exakt gleich langen Items. Listen mit exakt drei Punkten auffällig oft.
> Vorher: Drei Gründe für die Migration: Erstens … Zweitens … Drittens …
> Nachher: Der Hauptgrund für die Migration ist der Support-Ende-Termin. Ein Nebenaspekt ist die Lizenzkosten.

**C4. Mini-Fazits.** Ein „Zusammenfassend"-Absatz pro Sektion. Sieben Sektionen, sieben Mini-Fazits, schreibt selten jemand freiwillig. KI-Texte enden auffällig oft mit einem Abschnitt „Fazit".
> Vorher: Zusammenfassend lässt sich sagen, dass die Migration gelungen ist.
> Nachher: Die Migration ist nach vier Monaten abgeschlossen. Offen ist noch die Anbindung des Warenwirtschaftssystems.

**C5. Fragmentierte Absätze.** Jeder Abschnitt behandelt exakt ein Thema, beginnt und endet sauber, aber ohne Übergänge. Der Lesefluss wirkt fragmentiert, Verknüpfungen fehlen.
> Vorher: [Drei Absätze, je in sich geschlossen, ohne Verweis aufeinander]
> Nachher: [Absätze, die aufeinander Bezug nehmen: „Anders als beim Ansatz aus dem vorigen Abschnitt …"]

**C6. Zweiteilige Schablonen-Überschriften.** „Anforderungen und Herausforderungen", „Funktionsweise und Anwendung", „Geschichte und Bedeutung". KI erzeugt gehäuft zweiteilige Überschriften, die ein Thema paarig ordnen, wo menschliche Gliederung eher beim konkreten Inhalt bleibt (Wikipedia DE).
> Vorher: ## Funktionsweise und Anwendung
> Nachher: ## Wie der Import läuft

### D. Typografie und Formatierung

**D1. Gedankenstriche.** KI nutzt typografische Gedankenstriche (–) und em-dashes (—) deutlich häufiger als Menschen. Im Deutschen ist der Halbgeviertstrich korrekt, aber die Masse ist das Tell. Ein Gedanke – wie dieser – pausiert. Komma, Punkt oder Klammer sind meist die bessere Wahl.
> Vorher: Die Lösung – einmal installiert – läuft auf allen Systemen – ohne Ausnahme.
> Nachher: Die Lösung läuft nach der Installation auf allen Systemen, ohne Ausnahme.

**D2. Amerikanische Anführungszeichen.** KI setzt "..." statt deutscher „...". Auch U+2019 als Apostroph statt geradem ' ist ein Hinweis. Immer prüfen: „deutsche" Anführungszeichen unten-auf.
> Vorher: Er sagte "das Projekt läuft" ohne Zögern.
> Nachher: Er sagte „das Projekt läuft", ohne Zögern.

**D3. Geschützte und Sonderzeichen.** U+00A0 (geschütztes Leerzeichen), U+202F (schmales Leerzeichen), U+00B7 (Mittelpunkt-Bullet •), doppelte Leerzeichen nach Punkten (US-Stil). Menschen tippen diese Zeichen praktisch nie bewusst. Auch: Leerzeichen am Absatzanfang (Copy-Paste-Rest aus Chat-Oberflächen).
> Vorher: Die Auslastung liegt bei 87 % – Tendenz steigend (mit U+00A0 vor %).
> Nachher: Die Auslastung liegt bei 87 Prozent, Tendenz steigend. (Oder: normales Leerzeichen, wenn bewusst gesetzt.)

**D4. Fett-Mechanik.** Mechanisch gesetzter **Fettdruck** für Schlüsselbegriffe in jedem Satz. Menschen setzen Fettdruck sparsamer und unsystematischer.
> Vorher: Die Plattform bietet **nahtlose Integration**, **umfassende Analysen** und **maßgeschneiderte Dashboards**.
> Nachher: Die Plattform bietet Integration, Analysen und Dashboards, die sich konfigurieren lassen.

**D4a. Großschreibung in Überschriften.** Durchgehend große Schrift (ALLES IN GROSSBUCHSTABEN) oder englische Titelschreibweise („Die Strategischen Verhandlungen Und Die Globalen Partnerschaften") in Überschriften. Deutsche Überschriften bleiben in normaler Groß-/Kleinschreibung.
> Vorher: ## REST APIS IM VERGLEICH
> Nachher: ## REST-APIs im Vergleich

**D5. Emojis.** Emojis vor Überschriften oder Listenpunkten: 🚀 **Startphase:** … In deutschen Texten jenseits von Social Media unüblich und stark verräterisch.
> Vorher: 🚀 **Neu:** Die neue Version ist da!
> Nachher: Die neue Version ist da.

**D6. Aufzählungszeichen-Reste.** Listen kopiert aus Chat-Oberflächen behalten oft • oder – als Bullet statt Markdown-Strich.
> Vorher: • Erster Punkt
> Nachher: - Erster Punkt

### E. Kommunikation und Meta

**E1. Chat-Reste.** „Ich hoffe, das hilft", „Natürlich!", „Sicherlich!", „Möchtest du, dass …", „Lassen Sie mich wissen", „Hier ist eine Übersicht". Reste aus dem Dialog mit dem Bot, als Inhalt eingefügt.
> Vorher: Hier ist eine Übersicht über die Französische Revolution. Ich hoffe, das hilft! Sagen Sie Bescheid, wenn ich etwas vertiefen soll.
> Nachher: Die Französische Revolution begann 1789 mit einer Staatskrise und Missernten.

**E2. Wissenslücken-Disclaimer.** „Stand [Datum]", „Bis zu meinem letzten Update", „Während spezifische Details rar sind …", „basierend auf verfügbaren Informationen". Reste des Chatbot-Disclaimers.
> Vorher: Während spezifische Details zur Gründung rar sind, scheint das Unternehmen in den 1990ern entstanden zu sein.
> Nachher: Gegründet wurde das Unternehmen 1994, laut Handelsregister.

**E3. Servilität.** „Gute Frage!", „Sie haben völlig recht!", „Das ist ein exzellenter Punkt". Menschen loben den Fragesteller selten in eigenen Texten.
> Vorher: Gute Frage! Sie haben völlig recht, das ist ein komplexes Thema.
> Nachher: Das Thema ist komplex, weil drei Regularien zusammenkommen.

**E4. Genus-Vermeidung.** KI weicht auf „die Person", „das Individuum", „die Fachkraft" aus, wo ein Mensch „er", „sie" oder „man" schreibt. Übertrieben konsistente Gender-Sternchen (Mitarbeiter\*innen in jedem Satz) wirken maschinell, wenn sie im restlichen Text nicht vorkommen.
> Vorher: Die Fachkraft prüft die Daten, die Person entscheidet, das Individuum verantwortet.
> Nachher: Sie prüft die Daten, entscheidet und verantwortet das Ergebnis.

**E5. Pfadfinder-Ansagen.** „Tauchen wir ein …", „Schauen wir uns das genauer an …", „Hier ist, was Sie wissen müssen". Die Ankündigung ersetzt das Tun und verleiht Tutorial-Luft.
> Vorher: Tauchen wir ein in die Welt der Container-Netzwerke. Hier ist, was Sie wissen müssen.
> Nachher: Container-Netzwerke haben drei Ebenen: Bridge, Overlay und Macvlan. Die unterscheiden sich so.

**E6. Zuspruch-Kicker.** „Und das ist okay.", „Da ist nichts falsch dran.", „Du bist nicht allein damit." Ungefragte Beruhigung am Absatzende, als müsste der Leser getröstet werden.
> Vorher: Vielleicht haben Sie noch keine Testumgebung. Und das ist okay. Da ist nichts falsch dran.
> Nachher: Viele Teams starten ohne Testumgebung und bauen eine, wenn die ersten Regressionen Zeit kosten.

### F. Seele und Haltung

**F1. Meinungslosigkeit.** Nur neutrales Berichten, keine Position. Menschen haben einen Standpunkt und reagieren auf Fakten.
> Vorher: Die Ergebnisse sind interessant. Einige Studien zeigen positive Effekte, andere nicht.
> Nachher: Ich halte die Ergebnisse für überschätzt. Die Kontrollgruppen waren zu klein, um irgendwas zu beweisen.

**F2. Unsicherheits-Vermeidung.** Keine Ambivalenz, keine gemischten Gefühle, keine halbfertigen Gedanken. „Beeindruckend, aber auch etwas unheimlich" wirkt menschlicher als reine Zustimmung.
> Vorher: Die Technologie ist beeindruckend und vielversprechend.
> Nachher: Die Technologie funktioniert gut. Wie gut, weiß ich nach zwei Wochen nicht zu sagen.

**F3. Detail-Armut.** Pauschale Aussagen ohne konkrete Zahl, Namen, Szene. Ein Satz mit „insgesamt etwa zwei Stunden pro Woche" überzeugt mehr als „erhebliche Zeitersparnis".
> Vorher: Das Tool spart erhebliche Zeit.
> Nachher: Vorher 40 Minuten pro Ticket, jetzt 12.

**F4. Keine künstlichen Fehler.** Kleine Unebenheiten entstehen von selbst; gezielt eingebaute „menschliche Fehler" (absichtliche Tippfehler, gestreute Nachlässigkeiten) sind selbst wieder ein Muster und kontraproduktiv. Der Weg zur Natürlichkeit ist Umschreibung, nicht Simulation.
> Nicht tun: absichtliche Tippfehler streuen.

### G. Tödliche Kombination

**G1. Tödliche Kombination.** Kein einzelnes Muster macht einen Text KI-verdächtig. Zwei oder drei Muster zusammen (etwa Gedankenstrich-Masse + Dreier-Adjektive + „nicht nur …, sondern auch") und der Text ist als KI identifiziert. Der Scan zählt Muster-Dichte, nicht einzelne Treffer.

**G2. Register-Konsistenz.** Kein Muster wirkt isoliert — der Kontext entscheidet, was auffällt. Ein Bewerbungsschreiben verträgt andere Konnektoren als ein Chat-Posting. Wer alle Muster mechanisch herausstreicht, produziert stimmlosen Durchschnitt statt natürliche Sprache. Der Katalog beschreibt Tells, keine Verbote: Ein Gedankenstrich bleibt erlaubt, „außerdem" bleibt erlaubt — Häufung und Monotonie sind das Problem. Bei jedem Streichen prüfen: Passt die Alternative zum Register des Textes und zur Stimme des Autors (falls Schreibprobe vorliegt)?

## STIL-KALIBRIERUNG (optional)

Wenn der Nutzer eine Schreibprobe liefert (eigene frühere Texte), zuerst analysieren:

1. **Probe lesen.** Auffälligkeiten notieren: Satzlängen-Muster (kurz-knackig? lang-schwingend? gemischt?), Wortwahl (umgangssprachlich? sachlich? dazwischen?), Absatz-Einstiege (direkt rein? erst Kontext?), Satzzeichen-Gewohnheiten (viele Kommas? Einschübe? Semikolons?), wiederkehrende Wendungen, Übergänge (explizite Konnektoren oder harter Themenwechsel?).
2. **Stimme in der Umschreibung nachbilden.** Muster-Entfernung ist nur die Hälfte; die andere Hälfte ist die Übernahme der Proben-Muster. Kurze Sätze in der Probe: keine langen produzieren. „Sachen" und „Dinge" in der Probe: nicht zu „Elemente" und „Komponenten" aufwerten.
3. **Ohne Probe** gilt die Standard-Vorgabe: Details, klare Meinung, Ich-Form wo passend, variierter Rhythmus.

Übergabe der Probe: inline in der Nachricht oder als Dateipfad.

## PERSÖNLICHKEIT UND SEELE

Muster-freier Text allein reicht nicht. Glattgebügelter, stimmloser Text ist genauso verdächtig wie Slop. Guter Text hat einen Menschen dahinter.

**Anzeichen seelenloser Texte** (auch wenn technisch sauber): gleich lange Sätze, keine Meinung, nur neutrales Berichten, keine Ambivalenz, keine Ich-Form wo sie passen würde, kein Humor, keine Kante, liest sich wie eine Pressemitteilung.

**Stimme einbringen:**
- **Meinung haben.** Fakten berichten, dann darauf reagieren. „Ich weiß ehrlich gesagt nicht, was ich davon halten soll" ist menschlicher als eine neutrale Pro/Contra-Liste.
- **Rhythmus variieren.** Kurze, punchige Sätze. Dann wieder längere, die sich Zeit lassen. Mischen.
- **Ambivalenz zulassen.** Menschen haben gemischte Gefühle. „Beeindruckend, aber auch etwas unheimlich" schlägt „beeindruckend".
- **Ich-Form wo es passt.** „Ich komme immer wieder zurück auf …" oder „Das ist mir aufgefallen …" zeigt einen denkenden Menschen.
- **Unordnung zulassen.** Perfekte Struktur wirkt algorithmisch. Abschweifungen, Einschübe, halbfertige Gedanken sind menschlich.
- **Gefühle konkret machen.** Statt „das ist besorgniserregend": „etwas unheimlich ist schon, dass Agenten um 3 Uhr nachts arbeiten, während niemand hinschaut".

## PROZESS

1. Text vollständig lesen (bei Datei: read_file).
2. Alle Muster-Vorkommen identifizieren (Katalog oben + analyse.py).
3. Problemstellen umschreiben.
4. Sicherstellen, dass das Ergebnis: natürlich klingt, wenn man es laut vorliest; natürlich variierte Satzstrukturen hat; konkrete Details statt vager Behauptungen nutzt; den Ton des Kontexts hält; einfache Konstruktionen (ist/hat) nutzt, wo angebracht.
5. Entwurf vorlegen.
6. Selbstprüfung: „Was lässt diesen Text noch KI-generiert wirken?" Verbleibende Tells kurz benennen.
7. Finalisierung: nochmal überarbeiten, finale Fassung zeigen.
8. Bei Datei-Herkunft: Änderungen mit patch (gezielt) oder write_file (Komplett-Rewrite) anwenden und dem Nutzer zeigen, was sich geändert hat.

## OUTPUT-FORMAT

1. Entwurf der Umschreibung
2. „Was lässt diesen Text noch KI-generiert wirken?" (kurze Bullets)
3. Finale Fassung
4. Kurze Änderungsübersicht (optional)

## BEISPIEL

**Vorher (KI-klingend):**
> Gute Frage! Hier ist ein Text zum Thema. Ich hoffe, das hilft!
>
> In der heutigen schnelllebigen digitalen Welt spielt künstliche Intelligenz eine immer größere Rolle – und das aus gutem Grund. KI-gestütztes Coden ist ein Zeugnis für das transformative Potenzial großer Sprachmodelle und markiert einen Wendepunkt in der Evolution der Softwareentwicklung. Diese bahnbrechenden Werkzeuge – eingebettet an der Schnittstelle von Forschung und Praxis – formen die Art, wie Ingenieure denken, iterieren und liefern, neu.
>
> Im Kern ist das Wertversprechen klar: Prozesse straffen, Zusammenarbeit verbessern, Alignment fördern. Es geht nicht nur um Autocomplete – es geht darum, Kreativität im Maßstab freizusetzen. Das Tool dient als Katalysator. Der Assistent fungiert als Partner. Das System steht als Fundament für Innovation.
>
> Branchenbeobachter haben festgestellt, dass die Adoption beschleunigt – von Hobby-Experimenten bis zu unternehmensweiten Rollouts. Darüber hinaus unterstreicht die Fähigkeit, Dokumentation, Tests und Refactorings zu generieren, das fein abgestimmte Zusammenspiel von Automatisierung und menschlichem Urteilsvermögen.
>
> Zusammenfassend lässt sich sagen: Die Zukunft sieht rosig aus. Aufregende Zeiten liegen vor uns. Lassen Sie mich wissen, wenn ich etwas vertiefen soll!

**Entwurf (nach erstem Durchgang):**
> KI-Coding-Assistenten beschleunigen manche Aufgaben deutlich. Eine Google-Studie von 2024 zeigte: einfache Funktionen 55 Prozent schneller abgeschlossen. Bei Debugging und Architektur-Entscheidungen: kein messbarer Unterschied.
>
> Gut sind die Werkzeuge bei Boilerplate: Konfiguration, Test-Gerüste, Wiederholungs-Refactorings. Schlecht sind sie darin zu wissen, wann sie falsch liegen. Mir ist es passiert, dass Vorschläge kompilierten, Lint bestanden und trotzdem am Ziel vorbeischossen, weil ich nicht mehr hingesehen habe.
>
> Die Produktivitäts-Storys sind schwer zu überprüfen. „30 Prozent Annahmequote" sagt nichts über Korrektheit, und Korrektheit sagt nichts über Wert.
>
> Das heißt nicht, dass die Werkzeuge nutzlos sind. Es heißt, dass es Werkzeuge sind. Wer keine Tests hat, kann nicht unterscheiden, ob der Vorschlag stimmt.

**Was lässt diesen Text noch KI-generiert wirken?**
- Der Rhythmus ist noch zu ordentlich (saubere Kontraste, gleichmäßig getaktete Absätze).
- Die Schlusszeile klingt leicht nach Merksatz statt nach Mensch.

**Final (nach Selbstprüfung):**
> KI-Coding-Assistenten machen dich bei den langweiligen Teilen schneller. Bei allem anderen? Eher nicht.
>
> Gut sind sie bei Boilerplate: Konfiguration, Test-Gerüste, Wiederholungs-Refactorings. Sie sind aber auch gut darin, überzeugend zu klingen und danebenzuliegen. Ich habe Vorschläge akzeptiert, die kompilierten, Lint bestanden und trotzdem das Problem verfehlten, weil ich nicht mehr hingeschaut habe.
>
> Die Produktivitäts-Storys sind rutschig. GitHub sagt, Copilot-Nutzer akzeptierten „30 Prozent der Vorschläge". Aber Akzeptanz ist keine Korrektheit, und Korrektheit ist kein Wert. Wer keine Tests hat, rät im Grunde nur.

**Änderungen:**
- Chat-Reste entfernt („Gute Frage!", „Ich hoffe, das hilft!")
- Bedeutungs-Aufblähung entfernt („Zeugnis", „Wendepunkt", „Evolution")
- Werbesprache entfernt („bahnbrechend", „eingebettet")
- Vage Autoritäten entfernt („Branchenbeobachter")
- Partizipial-Anhängsel entfernt („unterstreicht", „widerspiegelnd")
- Negative Parallelismen entfernt („Es geht nicht nur um …")
- Trikolon entfernt („Katalysator/Partner/Fundament", „Dokumentation, Tests und Refactorings")
- Gedankenstrich-Masse auf Komma/ Punkt reduziert
- Konnektoren-Inflation entfernt („Darüber hinaus")
- Fazit-Floskel ersetzt durch konkrete Aussage

## ANALYSE-SKRIPT

scripts/analyse.py misst, was sich zählen lässt:
- Variationskoeffizient der Satzlängen (Schwellwert 0,4)
- Füllwort- und KI-Vokabular-Dichte (Wortliste references/wordlist.json)
- Trikolon-Tendenz (Listen mit exakt drei Items; drei gleich strukturierte Aufzählungen)
- Typografie-Verdacht (Gedankenstrich-Dichte, US-Anführungszeichen, U+00A0/U+202F, Doppelleerzeichen, •-Bullets, Leerzeichen am Absatzanfang)

Aufruf: python3 scripts/analyse.py <datei> (oder Text via stdin). Das Skript ist eine Hilfe, kein Urteil: Die Muster im Katalog und das eigene Sprachgefühl entscheiden, der Score liefert nur Anhaltspunkte.

## ATTRIBUTION

Basiert auf [blader/humanizer](https://github.com/blader/humanizer) (MIT, Siqi Chen), der selbst auf [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) fußt. Deutsche Grundlage: [Wikipedia: Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte) (angepasste Übersetzung, Stand September 2025).

Ergänzt um deutschsprachige Erkenntnisse: korrektur.de (Merkmale-Checkliste 2026, Variationskoeffizient 0,4, Kansas-Studie 94 Prozent, Cornell-Auswertung 14 Millionen Peer-Reviews, JMIR-Studie zu erfundenen Referenzen), contentconsultants.de (Floskel-Katalog, Gedankenstrich- und Dreier-Adjektiv-Muster), ki-im-marketing.at (Strukturmerkmale). Nummerierung teilweise angelehnt an das englische Original, Beispiele und Formulierungen komplett neu auf Deutsch. Lizenziert unter MIT, siehe LICENSE.
