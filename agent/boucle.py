"""La boucle tool use ecrite a la main.

Aucune bibliotheque d'agent : uniquement le SDK anthropic.
C'est ce que LangGraph remplacera dans agent/graphe.py.
"""
from __future__ import annotations

from agent.outils import DISPATCH, OUTILS_SCHEMA, SYSTEM

MAX_TOURS = 5


# ── EXEMPLE COMPLET ─────────────────────────────────────────────────
def executer(nom: str, args: dict):
    """Route vers la bonne fonction Python."""
    fonction = DISPATCH.get(nom)
    if fonction is None:
        raise ValueError(f"Outil inconnu: {nom}. "
                          f"Disponibles: {list(DISPATCH)}")
    return fonction(**args)


def repondre(question: str, client, modele: str = "claude-haiku-4-5",
             max_tours: int = MAX_TOURS, trace: list | None = None) -> str:
    """Boucle complete. trace, si fourni, recoit (nom_outil, erreur)."""
    messages = [{"role": "user", "content": question}]

    for _ in range(max_tours):
        # demande a Claude la prochaine action (texte final ou appel d'outil)
        rep = client.messages.create(
            model=modele, max_tokens=1024, system=SYSTEM,
            tools=OUTILS_SCHEMA, messages=messages)

        # la reponse de Claude rejoint l'historique telle quelle
        messages.append({"role": "assistant", "content": rep.content})

        # pas d'outil demande : Claude a fini, on renvoie son texte
        if rep.stop_reason != "tool_use":
            return "".join(b.text for b in rep.content
                           if b.type == "text")

        # sinon, executer chaque outil demande dans ce tour
        resultats = []
        for b in rep.content:
            if b.type != "tool_use":
                continue
            try:
                resultat, erreur = executer(b.name, b.input), False
            except Exception as exc:
                resultat, erreur = str(exc), True

            if trace is not None:
                trace.append((b.name, erreur))

            resultats.append({"type": "tool_result",
                              "tool_use_id": b.id,
                              "content": str(resultat),
                              "is_error": erreur})

        # tous les resultats de ce tour repartent en UN SEUL message,
        # en role "user" (c'est la regle de l'API, meme si contre-intuitif)
        messages.append({"role": "user", "content": resultats})

    # la boucle s'est terminee sans reponse finale : le garde-fou
    return "Nombre maximum d'etapes atteint."
