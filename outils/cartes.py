#!/usr/bin/env python3
"""Écrit les cartes des boîtes en HTML statique, à partir de membres.json.

Les pages lisent aussi membres.json en JavaScript, mais les robots qui n'exécutent pas
le JavaScript (ceux des IA, souvent Bing) ne voient que le HTML. Ce script recopie donc
la liste dans le HTML de index.html et de manifeste.html, entre les marqueurs
<!-- cartes:debut --> et <!-- cartes:fin -->, avec le même rendu que le JavaScript.
Il écrit aussi la fiche Organization de New Health et ses membres (données structurées
schema.org) dans index.html, entre <!-- jsonld:debut --> et <!-- jsonld:fin -->.

À lancer depuis la racine du dépôt après chaque changement de membres.json :
    python3 outils/cartes.py
"""
import html
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
MOIS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def e(texte):
    return html.escape(texte or "", quote=True)


def logo(b):
    if b.get("logo"):
        return f'<div class="logo"><img src="{e(b["logo"])}" alt="{e(b["nom"])}" loading="lazy"></div>'
    return f'<div class="logo"><span class="txt">{e(b["nom"])}</span></div>'


def carte_accueil(b):
    corps = logo(b) + f'<span class="v">{e(b.get("verticale"))}</span><p>{e(b.get("phrase"))}</p>'
    if b.get("fondateurs"):
        corps += f'<div class="who">{e(b["fondateurs"])}</div>'
    if b.get("site"):
        return f'<a class="co" href="{e(b["site"])}" target="_blank" rel="noopener">{corps}</a>'
    return f'<article class="co">{corps}</article>'


def ligne_manifeste(b):
    milieu = f'<div class="v">{e(b.get("verticale"))}</div>'
    if b.get("fondateurs"):
        milieu += f'<div class="who">{e(b["fondateurs"])}</div>'
    m = re.match(r"^(\d{4})-(\d{2})", b.get("depuis") or "")
    depuis = f"Since {MOIS[int(m.group(2)) - 1]} {m.group(1)}" if m else ""
    return f'<li>{logo(b)}<div>{milieu}</div><span class="since">{e(depuis)}</span></li>'


def jsonld_organisation(boites):
    """La fiche Organization de New Health, avec ses membres, pour les moteurs de recherche."""
    U = "https://joinnewhealth.eu/"
    org = {
        "@context": "https://schema.org", "@type": "Organization", "@id": U + "#org",
        "name": "New Health", "url": U, "logo": U + "icon.png",
        "description": ("New Health is a network of digital health startups that look after everyday "
                        "health issues (sleep, digestion, skin, hormones, energy, mood) and stay with "
                        "people over time. Launched in Paris on 25 November 2026."),
        "member": [{k: v for k, v in (("@type", "Organization"), ("name", b["nom"]), ("url", b.get("site")),
                                       ("description", b.get("phrase"))) if v} for b in boites],
    }
    texte = json.dumps(org, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return ['<script type="application/ld+json">'] + texte.split("\n") + ["</script>"]


CASE_VIDE = ('<a class="co slot" href="#rejoindre"><span class="v">Your vertical</span>'
             '<span class="txt">Your company?</span>'
             '<p>If it meets the five criteria, it belongs here.</p></a>')


def remplacer(fichier, contenu, retrait, marque="cartes"):
    chemin = RACINE / fichier
    texte = chemin.read_text(encoding="utf-8")
    motif = re.compile(r"(<!-- %s:debut -->)(.*?)([ \t]*<!-- %s:fin -->)" % (marque, marque), re.S)
    if len(motif.findall(texte)) != 1:
        sys.exit(f"{fichier} : il faut exactement une paire de marqueurs {marque}:debut / {marque}:fin")
    lignes = "\n".join(retrait + ligne for ligne in contenu)
    neuf = motif.sub(lambda m: m.group(1) + "\n" + lignes + "\n" + m.group(3), texte)
    if neuf != texte:
        chemin.write_text(neuf, encoding="utf-8")
    return neuf != texte


def main():
    boites = json.loads((RACINE / "membres.json").read_text(encoding="utf-8")).get("boites", [])
    accueil = [carte_accueil(b) for b in boites] + [CASE_VIDE]
    manifeste = [ligne_manifeste(b) for b in boites] or ['<li class="wait">The list will be published with the manifesto.</li>']
    for fichier, contenu, retrait in (("index.html", accueil, "      "), ("manifeste.html", manifeste, "      ")):
        print(fichier, "mis à jour" if remplacer(fichier, contenu, retrait) else "déjà à jour")
    print("index.html (données structurées)",
          "mis à jour" if remplacer("index.html", jsonld_organisation(boites), "", "jsonld") else "déjà à jour")


if __name__ == "__main__":
    main()
