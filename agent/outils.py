"""Les trois outils du portail sinistres.

Fonctions Python ORDINAIRES. Elles servent a deux usages :
  - la boucle a la main, avec les schemas JSON de OUTILS_SCHEMA
  - le graphe LangGraph, via tool() dans agent/graphe.py

On ne les ecrit qu'une fois.

chercher_police() est donnee comme exemple complet : lisez-la
d'abord, elle montre le patron a suivre pour les deux autres.
"""
from __future__ import annotations

import re
from typing import Optional

BASE_DOSSIERS = {
    "POL-4471": {"garanties": ["collision", "vol", "vandalisme"],
                 "avenants": ["RE-04"],
                 "franchises": {"collision": 500, "refoulement": 1000,
                                "vol_pieces": 250, "vandalisme": 500}},
    "POL-8802": {"garanties": ["collision"], "avenants": [],
                 "franchises": {"collision": 500}},
}

CLAUSES = {
    "refoulement": ("Clause 7.3.2 - Les dommages par refoulement d'egout "
                    "sont couverts uniquement si l'avenant RE-04 a ete "
                    "souscrit. Franchise 1000 $. Maximum 25000 $. "
                    "(police-auto-2026, p.12)"),
    "collision": ("Clause 7.3.1 - Dommages par collision couverts. "
                  "Franchise 500 $. (police-auto-2026, p.12)"),
    "vol": ("Clause 9.2 - Vol de pieces couvert, franchise 250 $. "
            "Rapport de police obligatoire sous 48 h. "
            "(police-auto-2026, p.18)"),
    "escalade": ("Procedure - Toute reclamation depassant 50000 $ ou "
                 "impliquant des blessures est escaladee au superviseur. "
                 "(procedure-interne-2026, p.3)"),
}


# ── EXEMPLE COMPLET - lisez-la avant d'ecrire les deux autres ──────────
def chercher_police(numero: str) -> dict:
    """Recupere garanties, avenants et franchises d'une police
    d'assurance automobile a partir de son numero (format POL-1234).
    A utiliser des qu'un numero de police est mentionne."""
    if not re.fullmatch(r"POL-\d{4}", numero or ""):
        raise ValueError("Numero mal forme, format attendu: POL-1234")
    if numero not in BASE_DOSSIERS:
        raise KeyError(f"Police {numero} introuvable, verifiez le numero.")
    return BASE_DOSSIERS[numero]


def rechercher_clause(sujet: str) -> str:
    """Retrouve la clause applicable a un type de sinistre.
    Sujets connus : refoulement, collision, vol, escalade."""
    sujet_nettoye = sujet.strip().lower()
    if sujet_nettoye not in CLAUSES:
        return ("Aucune clause trouvee pour ce sujet. Sujets connus : "
                + ", ".join(list(CLAUSES)))
    return CLAUSES[sujet_nettoye]


def calculer_indemnite(montant_dommages: float, franchise: float,
                       maximum: Optional[float] = None) -> dict:
    """Calcule le montant net a verser. TOUJOURS utiliser cet outil
    pour tout calcul monetaire, ne jamais calculer de tete."""
    if montant_dommages is None or montant_dommages < 0:
        raise ValueError("montant_dommages doit etre un nombre positif.")
    if franchise is None or franchise < 0:
        raise ValueError("franchise doit etre un nombre positif.")

    net = max(0.0, montant_dommages - franchise)
    plafonne = maximum is not None and net > maximum
    if plafonne:
        net = maximum

    return {"indemnite": net, "plafonne": plafonne}

# ── Schemas JSON pour l'API brute (bloc 1) ────────────────────────────
# Un dict par outil : name, description, input_schema.
# La description doit dire QUAND utiliser l'outil (et au besoin quand
# NE PAS l'utiliser) - c'est elle que Claude lit pour decider.
# Le premier est fait, sur le meme modele que chercher_police ci-dessus.
OUTILS_SCHEMA = [
    {
        "name": "chercher_police",
        "description": (
            "Recupere garanties, avenants et franchises d'une police "
            "d'assurance automobile a partir de son numero. A utiliser "
            "des qu'un numero de police (format POL-1234) est mentionne "
            "dans la question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "numero": {"type": "string",
                           "description": "Format POL-1234"},
            },
            "required": ["numero"],
        },
    },
    {
        "name": "rechercher_clause",
        "description": (
            "Retrouve le texte de la clause applicable a un type de "
            "sinistre, avec sa reference et sa page. A utiliser avant de "
            "citer une couverture, une franchise ou un plafond : ne "
            "jamais reciter une clause de memoire."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sujet": {
                    "type": "string",
                    "description": "Type de sinistre concerne.",
                    "enum": list(CLAUSES),
                },
            },
            "required": ["sujet"],
        },
    },
    {
        "name": "calculer_indemnite",
        "description": (
            "Calcule le montant net a verser une fois la franchise "
            "appliquee, et indique si le plafond de la garantie a ete "
            "atteint. TOUJOURS utiliser cet outil pour tout calcul "
            "monetaire, ne jamais calculer un montant de tete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "montant_dommages": {
                    "type": "number",
                    "description": "Montant total des dommages estimes, en dollars.",
                },
                "franchise": {
                    "type": "number",
                    "description": "Franchise applicable, en dollars.",
                },
                "maximum": {
                    "type": "number",
                    "description": "Plafond de la garantie, en dollars, si applicable.",
                },
            },
            "required": ["montant_dommages", "franchise"],
        },
    },
]

DISPATCH = {
    "chercher_police": chercher_police,
    "rechercher_clause": rechercher_clause,
    "calculer_indemnite": calculer_indemnite,
}

SYSTEM = (
    "Tu es un assistant d'analyse de sinistres pour OGI Assurance. "
    "Tu t'adresses a des courtiers internes.\n"
    "- Utilise les outils pour obtenir les faits. N'invente jamais une "
    "garantie ni un montant.\n"
    "- Pour tout calcul monetaire, utilise calculer_indemnite.\n"
    "- Cite toujours la clause et la page.\n"
    "- Si une information est absente, dis-le au lieu de supposer."
)
