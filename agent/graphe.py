"""Le meme agent, reconstruit en LangGraph.

Le graphe et le cablage (add_node / add_edge) sont deja ecrits en bas
du fichier. Ce qu'il reste a faire : emballer les deux outils
manquants, puis remplir le corps des trois fonctions-noeuds.
"""
from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict, Annotated

from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from agent.outils import (
    chercher_police as _chercher_police,
    rechercher_clause as _rechercher_clause,
    calculer_indemnite as _calculer_indemnite,
)


# ── EXEMPLE COMPLET - le patron pour les deux outils suivants ─────────
@tool
def chercher_police(numero: str) -> dict:
    """Recupere garanties, avenants et franchises d'une police
    d'assurance automobile a partir de son numero (format POL-1234).
    A utiliser des qu'un numero de police est mentionne."""
    return _chercher_police(numero)


@tool
def rechercher_clause(sujet: str) -> str:
    """Retrouve la clause applicable a un type de sinistre.
    Sujets connus : refoulement, collision, vol, escalade."""
    return _rechercher_clause(sujet)


@tool
def calculer_indemnite(montant_dommages: float, franchise: float,
                        maximum: Optional[float] = None) -> dict:
    """Calcule le montant net a verser. TOUJOURS utiliser cet outil
    pour tout calcul monetaire, ne jamais calculer de tete."""
    return _calculer_indemnite(montant_dommages, franchise, maximum)


OUTILS_LC = [chercher_police, rechercher_clause, calculer_indemnite]
_PAR_NOM = {o.name: o for o in OUTILS_LC}


# ── Donne : l'etat partage entre les noeuds ────────────────────────
class EtatAgent(TypedDict):
    messages: Annotated[list, add_messages]
    dossier: str | None
    tours: int


def construire_agent(modele, max_tours: int = 5, checkpointer=None):
    lie = modele.bind_tools(OUTILS_LC)

    def noeud_agent(etat):
        """Appelle le modele avec l'historique de messages et incremente
        le compteur de tours."""
        rep = lie.invoke(etat["messages"])
        return {"messages": [rep], "tours": etat.get("tours", 0) + 1}

    def noeud_outils(etat):
        """Execute chaque appel d'outil demande par le dernier message,
        et renvoie un ToolMessage par appel. Une exception est capturee
        et renvoyee comme contenu du message plutot que de faire planter
        le noeud (chercher_police() y ajoute deja le mot "verifiez")."""
        dernier = etat["messages"][-1]
        resultats = []
        for appel in dernier.tool_calls:
            outil = _PAR_NOM[appel["name"]]
            try:
                sortie = outil.invoke(appel["args"])
            except Exception as exc:
                sortie = str(exc)
            resultats.append(ToolMessage(content=str(sortie),
                                         tool_call_id=appel["id"],
                                         name=appel["name"]))
        return {"messages": resultats}

    # ── Donne ────────────────────────────────────────────────────
    def noeud_limite(etat):
        return {"messages": [AIMessage(
            content="Nombre maximum d'etapes atteint.")]}

    def router(etat) -> str:
        """Decide du prochain noeud : le garde-fou l'emporte, sinon on
        route vers les outils si Claude en a demande, sinon on arrete."""
        if etat.get("tours", 0) >= max_tours:
            return "limite"
        dernier = etat["messages"][-1]
        if getattr(dernier, "tool_calls", None):
            return "outils"
        return END

    # ── Donne : le cablage du graphe ─────────────────────────────
    g = StateGraph(EtatAgent)
    g.add_node("agent", noeud_agent)
    g.add_node("outils", noeud_outils)
    g.add_node("limite", noeud_limite)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", router,
                             {"outils": "outils", "limite": "limite",
                              END: END})
    g.add_edge("outils", "agent")
    g.add_edge("limite", END)
    return g.compile(checkpointer=checkpointer)
