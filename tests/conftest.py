"""Gemeinsame Helfer für die Tests von scripts/analyse.py und SKILL.md.

Die Tests rufen das Skript über die Kommandozeile auf (--json), damit sie
genau das prüfen, was auch ein Agent sieht. Mit der Umgebungsvariable
ANALYSE_SCRIPT lässt sich ein anderes Skript testen (z. B. eine alte Version
zum Vergleich).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "SKILL.md"
SCRIPT = Path(os.environ.get("ANALYSE_SCRIPT", ROOT / "scripts" / "analyse.py"))

KOPF_RE = re.compile(
    r"^\*\*(?P<id>[A-G]\d+a?)\. (?P<name>[^*]+?)\.\*\*\s*(?:\((?P<stufe>stark|schwach)\))?",
    re.M,
)
BEISPIEL_RE = re.compile(r"^> (?P<art>Vorher|Nachher)(?: \([^)]*\))?:\s*(?P<text>.+)$", re.M)


def lauf(*args, text=None):
    """Führt analyse.py aus und gibt (returncode, stdout) zurück."""
    proc = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *args],
        input=text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout, proc.stderr


def analysiere(text, *args):
    code, out, err = lauf("--json", *args, "-", text=text)
    assert code in (0, 1), f"Skript fehlgeschlagen ({code}): {err}"
    return json.loads(out)


def ids(bericht):
    """Alle Muster-IDs, die das Skript gefunden hat (unabhängig von Schwellen)."""
    return {f["muster_id"] for f in bericht["funde"]}


def anzahl(bericht, muster_id):
    return sum(f["anzahl"] for f in bericht["funde"] if f["muster_id"] == muster_id)


def katalog():
    """Liest die Muster aus SKILL.md: {id: {name, stufe, vorher: [...], nachher: [...]}}."""
    text = SKILL_MD.read_text(encoding="utf-8")
    koepfe = list(KOPF_RE.finditer(text))
    muster = {}
    for i, m in enumerate(koepfe):
        ende = koepfe[i + 1].start() if i + 1 < len(koepfe) else len(text)
        block = text[m.start():ende]
        # Block endet spätestens beim nächsten Abschnitt
        abschnitt = re.search(r"^#{2,3} ", block, re.M)
        if abschnitt:
            block = block[:abschnitt.start()]
        beispiele = {"Vorher": [], "Nachher": []}
        for b in BEISPIEL_RE.finditer(block):
            beispiele[b.group("art")].append(b.group("text").strip())
        muster[m.group("id")] = {
            "name": m.group("name"),
            "stufe": m.group("stufe"),
            "vorher": beispiele["Vorher"],
            "nachher": beispiele["Nachher"],
        }
    return muster


@pytest.fixture(scope="session")
def muster_katalog():
    return katalog()
