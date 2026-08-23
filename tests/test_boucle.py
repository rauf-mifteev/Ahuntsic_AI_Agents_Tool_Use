"""Partie 2 - la boucle a la main. Tests FOURNIS, ne pas modifier."""
import pytest

from agent.boucle import executer, repondre
from tests.doubles import ClientBrutDouble, ClientBrutBoucle


# ── executer ──
def test_executer_route_correctement():
    r = executer("calculer_indemnite",
                 {"montant_dommages": 8500, "franchise": 500})
    assert r["indemnite"] == 8000.0


def test_outil_inconnu_message_explicite():
    with pytest.raises(ValueError) as e:
        executer("outil_fantome", {})
    assert "chercher_police" in str(e.value)


# ── la boucle ──
def test_boucle_complete():
    trace = []
    texte = repondre("Dossier POL-4471, refoulement, dommages 18000 $.",
                     ClientBrutDouble(), trace=trace)
    assert [n for n, _ in trace] == ["chercher_police",
                                     "rechercher_clause",
                                     "calculer_indemnite"]
    assert "17000" in texte


def test_aucune_erreur_sur_le_chemin_nominal():
    trace = []
    repondre("Dossier POL-4471, refoulement, dommages 18000 $.",
             ClientBrutDouble(), trace=trace)
    assert all(not err for _, err in trace)


def test_erreur_outil_capturee_sans_planter():
    trace = []
    texte = repondre("Dossier POL-9999, collision, dommages 4000 $.",
                     ClientBrutDouble(), trace=trace)
    assert trace[0] == ("chercher_police", True)
    assert "verifier" in texte.lower()


def test_garde_fou_max_tours():
    trace = []
    texte = repondre("boucle", ClientBrutBoucle(), max_tours=3, trace=trace)
    assert texte == "Nombre maximum d'etapes atteint."
    assert len(trace) == 3


def test_la_trace_reste_optionnelle():
    texte = repondre("Dossier POL-4471, refoulement, dommages 18000 $.",
                     ClientBrutDouble())
    assert "17000" in texte
