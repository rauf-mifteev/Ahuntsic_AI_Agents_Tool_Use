"""Partie 3 - le graphe LangGraph (version allegee, seance 1h30).

Tests FOURNIS. La memoire/checkpointing (threads) et l'evaluateur
de trajectoire sont retires de cette version - ce sont de bons
sujets pour une seance suivante, une fois la boucle de base solide.
"""
import pytest

pytest.importorskip("langgraph")

from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import AIMessage

try:
    from agent.graphe import EtatAgent, OUTILS_LC, construire_agent
except ImportError:
    pytest.skip("agent/graphe.py pas encore ecrit (partie 3)",
                allow_module_level=True)

from tests.doubles import ModeleBoucle, ModeleDouble


def entree(question):
    return {"messages": [HumanMessage(content=question)],
            "dossier": None, "tours": 0}


# ── les outils emballes ──
def test_trois_outils_langchain():
    assert len(OUTILS_LC) == 3


def test_les_docstrings_deviennent_les_descriptions():
    par_nom = {o.name: o for o in OUTILS_LC}
    assert "POL-1234" in par_nom["chercher_police"].description
    assert "TOUJOURS" in par_nom["calculer_indemnite"].description


def test_un_outil_reste_appelable():
    par_nom = {o.name: o for o in OUTILS_LC}
    r = par_nom["calculer_indemnite"].invoke(
        {"montant_dommages": 8500, "franchise": 500})
    assert r["indemnite"] == 8000.0


# ── l'agent complet ──
def test_le_compteur_de_tours_avance():
    s = construire_agent(ModeleDouble()).invoke(
        entree("Dossier POL-4471, refoulement, dommages 18000 $."))
    assert s["tours"] >= 4


def test_sequence_des_outils():
    s = construire_agent(ModeleDouble()).invoke(
        entree("Dossier POL-4471, refoulement, dommages 18000 $."))
    outils = [m.name for m in s["messages"] if isinstance(m, ToolMessage)]
    assert outils == ["chercher_police", "rechercher_clause",
                      "calculer_indemnite"]


def test_reponse_finale_contient_le_calcul():
    s = construire_agent(ModeleDouble()).invoke(
        entree("Dossier POL-4471, refoulement, dommages 18000 $."))
    assert "17000" in s["messages"][-1].content


def test_erreur_outil_ne_fait_pas_planter():
    s = construire_agent(ModeleDouble()).invoke(
        entree("Dossier POL-9999, collision, dommages 4000 $."))
    tm = [m for m in s["messages"] if isinstance(m, ToolMessage)]
    assert len(tm) == 1
    assert "introuvable" in tm[0].content.lower()
    assert "verifier" in s["messages"][-1].content.lower()


def test_garde_fou_produit_un_message_propre():
    app = construire_agent(ModeleBoucle(), max_tours=4)
    s = app.invoke(entree("boucle"), {"recursion_limit": 100})
    assert "maximum" in s["messages"][-1].content.lower()
    assert s["tours"] <= 5


# ── demo optionnelle (non notee) ──
# Comprendre le reducteur add_messages sans dependre du code des
# etudiants - a lancer manuellement en classe si le temps le permet.
def _demo_add_messages_concatene():
    g = StateGraph(EtatAgent)
    g.add_node("n1", lambda e: {"messages": [AIMessage(content="a")]})
    g.add_node("n2", lambda e: {"messages": [AIMessage(content="b")]})
    g.add_edge(START, "n1")
    g.add_edge("n1", "n2")
    g.add_edge("n2", END)
    res = g.compile().invoke(entree("x"))
    assert len(res["messages"]) == 3
