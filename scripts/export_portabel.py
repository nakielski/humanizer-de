#!/usr/bin/env python3
"""Erzeugt eine Kopie des Skills nach der Agent-Skills-Spezifikation.

Hermes liest version, author und platforms auf oberster Ebene des
Frontmatters. Die Agent-Skills-Spezifikation (agentskills.io) und der
Validator von Claude erlauben dort nur name, description, license,
compatibility, metadata und allowed-tools. Dieses Skript lässt SKILL.md im
Repository unverändert (für Hermes) und schreibt eine portable Kopie:
version, author und platforms wandern als Zeichenketten unter metadata,
der Hermes-Block (metadata.hermes) entfällt. Der Inhalt unterhalb des
Frontmatters bleibt identisch.

Aufruf:
    python3 scripts/export_portabel.py [ZIEL]     (Standard: dist/humanizer-de)
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERLAUBT = ("name", "description", "license", "compatibility", "allowed-tools")
NACH_METADATA = ("version", "author", "platforms")


def teile_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit("SKILL.md hat kein Frontmatter.")
    return m.group(1), text[m.end():]


def bloecke(frontmatter):
    """Zerlegt das Frontmatter in Top-Level-Schlüssel mit ihren Zeilen."""
    ergebnis, aktuell = [], None
    for zeile in frontmatter.split("\n"):
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", zeile)
        if m:
            aktuell = [m.group(1), m.group(2), []]
            ergebnis.append(aktuell)
        elif aktuell is not None:
            aktuell[2].append(zeile)
    return ergebnis


def als_string(wert):
    wert = wert.strip()
    if wert.startswith("[") and wert.endswith("]"):
        wert = ", ".join(w.strip() for w in wert[1:-1].split(","))
    wert = wert.strip("\"'")
    return '"' + wert.replace('"', '\\"') + '"'


def portables_frontmatter(frontmatter):
    zeilen, metadata = [], []
    for schluessel, wert, unterzeilen in bloecke(frontmatter):
        if schluessel in ERLAUBT:
            zeilen.append(f"{schluessel}: {wert}".rstrip())
            zeilen.extend(unterzeilen)
        elif schluessel in NACH_METADATA:
            metadata.append(f"  {schluessel}: {als_string(wert)}")
        elif schluessel == "metadata":
            # Hermes-spezifischen Unterblock auslassen, andere Einträge behalten
            ueberspringen = False
            for u in unterzeilen:
                if re.match(r"^  [\w-]+:", u):
                    ueberspringen = u.strip().startswith("hermes:")
                if not ueberspringen and u.strip():
                    metadata.append(u)
    if metadata:
        zeilen.append("metadata:")
        zeilen.extend(metadata)
    return "\n".join(zeilen)


def exportiere(ziel):
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, rumpf = teile_frontmatter(text)
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    (ziel / "SKILL.md").write_text(f"---\n{portables_frontmatter(frontmatter)}\n---\n{rumpf}",
                                   encoding="utf-8")
    shutil.copy2(ROOT / "LICENSE", ziel / "LICENSE")
    ignorieren = shutil.ignore_patterns("__pycache__", "*.pyc", "export_portabel.py")
    shutil.copytree(ROOT / "scripts", ziel / "scripts", ignore=ignorieren)
    shutil.copytree(ROOT / "references", ziel / "references", ignore=ignorieren)
    return ziel


def main():
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "humanizer-de"
    pfad = exportiere(ziel.resolve())
    print(f"Portable Kopie geschrieben: {pfad}")


if __name__ == "__main__":
    main()
