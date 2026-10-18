"""Konsistenzprüfungen für SKILL.md, references/wordlist.json und den Export.

Ein Skill, der KI-Tells entfernt, darf sie in seinen eigenen Beispielen nicht
vormachen: Modelle übernehmen Beispiele stärker als Regeln.
"""
import json
import re
import subprocess
import sys

import pytest

from conftest import ROOT, SKILL_MD, lauf

TEXT = SKILL_MD.read_text(encoding="utf-8")
WORTLISTE = ROOT / "references" / "wordlist.json"


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "Frontmatter fehlt"
    return m.group(1)


def top_level_keys(fm):
    return {m.group(1) for m in re.finditer(r"^([A-Za-z_-]+):", fm, re.M)}


# --- Typografie im Skill selbst ---------------------------------------------
# Vorher-Beispiele dürfen Tells enthalten, die Definitionen von D1 und D2
# müssen die falschen Zeichen zeigen. Alles andere muss sauber sein.

def _eigener_text():
    return "\n".join(z for z in TEXT.splitlines()
                     if not z.startswith(("> Vorher", "**D1.", "**D2.")))


def test_keine_gemischten_anfuehrungszeichen():
    gemischt = re.findall(r"„[^“\"\n]{0,200}\"", _eigener_text())
    assert gemischt == [], f"{len(gemischt)} Stellen mit „…\": {gemischt[:3]}"


def test_deutsche_anfuehrungszeichen_sind_geschlossen():
    text = _eigener_text()
    assert text.count("„") == text.count("“")


def test_kein_geviertstrich_im_eigenen_text():
    zeilen = [z for z in _eigener_text().splitlines() if "—" in z]
    assert zeilen == []


def test_beispiel_aenderungen_stehen_im_vorher():
    """Die Änderungsliste darf nur Wendungen nennen, die im Vorher vorkommen."""
    vorher = TEXT.split("**Vorher (KI-klingend):**", 1)[1].split("**Rückfrage", 1)[0]
    aenderungen = TEXT.split("**Änderungen:**", 1)[1].split("## ", 1)[0]
    zitate = re.findall(r"„([^“]+)“", aenderungen)
    assert zitate
    fehlend = [z for z in zitate if z not in vorher]
    assert fehlend == [], fehlend


# --- Katalog: Stufen und Wortliste ------------------------------------------

def test_jedes_muster_a_bis_e_hat_eine_stufe(muster_katalog):
    ohne = [mid for mid, m in muster_katalog.items() if mid[0] in "ABCDE" and not m["stufe"]]
    assert ohne == []


def test_stufen_stimmen_mit_skript_ueberein(muster_katalog):
    code, out, err = lauf("--muster")
    assert code == 0, err
    skript = json.loads(out)
    for mid, info in skript.items():
        assert mid in muster_katalog, f"Skript kennt {mid}, SKILL.md nicht"
        assert info["staerke"] == muster_katalog[mid]["stufe"], mid


def test_wortliste_ist_gueltig_und_verweist_auf_bekannte_muster(muster_katalog):
    daten = json.loads(WORTLISTE.read_text(encoding="utf-8"))
    for name, kat in daten["kategorien"].items():
        assert kat["muster_id"] in muster_katalog, f"{name}: {kat['muster_id']} unbekannt"
        assert kat["eintraege"], f"{name} ist leer"


def test_musterzahl_in_beschreibung_stimmt(muster_katalog):
    zahl = len(muster_katalog)
    assert f"{zahl} Muster" in TEXT, f"SKILL.md nennt nicht {zahl} Muster"


# --- Frontmatter: Hermes und portabler Export -------------------------------

def test_hermes_felder_vorhanden():
    keys = top_level_keys(frontmatter(TEXT))
    assert {"name", "description", "version", "author", "license", "platforms"} <= keys
    assert "hermes:" in frontmatter(TEXT)


def test_beschreibung_traegt_kern_in_den_ersten_57_zeichen():
    desc = re.search(r'^description: "(.*)"$', frontmatter(TEXT), re.M).group(1)
    anfang = desc[:57].lower()
    assert "ki" in anfang and "deutsch" in anfang, desc[:57]


def test_kalibrieren_misst_ordner(tmp_path):
    (tmp_path / "a.md").write_text("Gestern lief der Server wieder. Das Backup war vollständig.",
                                   encoding="utf-8")
    (tmp_path / "b.txt").write_text("Gute Frage! Ich hoffe, das hilft! Tauchen wir ein.", encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "kalibrieren.py"),
                           str(tmp_path), "--json"], capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    ergebnis = json.loads(proc.stdout)
    assert ergebnis["texte"] == 2
    assert ergebnis["stufen"]["unauffällig"] == 1 and ergebnis["stufen"]["auffällig"] == 1


def test_export_ist_spec_konform(tmp_path):
    ziel = tmp_path / "humanizer-de"
    proc = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "export_portabel.py"),
                           str(ziel)], capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    exportiert = (ziel / "SKILL.md").read_text(encoding="utf-8")
    keys = top_level_keys(frontmatter(exportiert))
    erlaubt = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
    assert keys <= erlaubt, keys - erlaubt
    assert (ziel / "scripts" / "analyse.py").exists()
    assert (ziel / "references" / "wordlist.json").exists()
    # Inhalt unterhalb des Frontmatters bleibt identisch
    assert exportiert.split("\n---\n", 1)[1] == TEXT.split("\n---\n", 1)[1]
