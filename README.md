# Portail Sinistres — Tool Use & Agents IA


Le lien vers le dépôt GitHub : **https://github.com/rauf-mifteev/Ahuntsic_AI_Agents_Tool_Use**

## Aperçu du projet

Ce projet a été réalisé dans le cadre du cours de l'Intelligence Artificielle 3 (420‐318‐AH) au Collège Ahuntsic. Il construit un agent d'analyse de sinistres pour un assureur automobile fictif (OGI Assurance), qui répond aux courtiers en consultant des polices, des clauses de garantie, et en calculant des indemnités — sans jamais inventer un montant ou une couverture.

L'agent est implémenté **deux fois**, avec le même comportement :

1. Une **boucle tool use écrite à la main**, avec uniquement le **SDK Anthropic** (aucun framework).
2. Le même comportement **reconstruit avec LangGraph**, un framework d'agent (état, nœud outils,
   routeur).

Les 28 tests fournis fonctionnent **sans aucun appel API réel**, grâce à un double de modèle
déterministe (`tests/doubles.py`).

## Structure du TP

| Partie | Fichier | `pytest -q` affiche |
|---|---|---|
| Départ | — | 20 failed, 8 passed |
| Partie 1 | `agent/outils.py` | 13 passed (sur `test_outils.py`) |
| Partie 2 — Tool Use | `agent/boucle.py` | 20 passed (sur `test_outils.py` + `test_boucle.py`) |
| Partie 3 — Agent | `agent/graphe.py` | 28 passed (suite complète) |

## Fichiers du projet

| Fichier | Rôle |
|---|---|
| `agent/outils.py` | Les trois outils Python (`chercher_police`, `rechercher_clause`, `calculer_indemnite`) et leurs schémas JSON. |
| `agent/boucle.py` | La boucle tool use écrite à la main (API Anthropic brute). |
| `agent/graphe.py` | Le même agent reconstruit avec LangGraph. |
| `tests/` | Les 28 tests fournis (`test_outils.py`, `test_boucle.py`, `test_graphe.py`) et le double de modèle déterministe (`doubles.py`). |
| `pytest.ini` | Configuration pytest (chemins des tests, `pythonpath`). |
| `TP01_tooluse_agents.ipynb` | Le notebook complet, exécutable de bout en bout. |

## Prérequis

- Google Colab (ou Python 3.10+ en local).
- [pytest](https://pytest.org/), [anthropic](https://pypi.org/project/anthropic/),
  [langgraph](https://pypi.org/project/langgraph/),
  [langchain-anthropic](https://pypi.org/project/langchain-anthropic/),
  [langchain-core](https://pypi.org/project/langchain-core/), `typing_extensions`.
- Une clé API Anthropic (`ANTHROPIC_API_KEY`) — **optionnelle**, utile uniquement pour la cellule
  d'essai contre le vrai Claude. Les 28 tests passent sans aucune clé.

## Exécution

### Sur Google Colab

Ouvrir `TP01_tooluse_agents_simplifie_solved.ipynb` et exécuter les cellules dans l'ordre.
Pour activer la cellule optionnelle d'appel API réel, ajouter `ANTHROPIC_API_KEY` dans les
secrets Colab (icône clé à gauche) avant de l'exécuter.

### En local

```bash
pip install pytest anthropic langgraph langchain-anthropic langchain-core typing_extensions
pytest -q
```

Sortie attendue : `28 passed`.

## Synthèse

**Partie 1 — les outils.** `chercher_police` étant fournie comme patron, `rechercher_clause` et
`calculer_indemnite` suivent la même structure : valider les entrées, chercher dans un
dictionnaire, renvoyer un résultat simple. Le point le plus facile à rater est
`test_indemnite_jamais_negative` : sans `max(0.0, ...)`, un montant de dommages inférieur à la
franchise produirait une indemnité négative, ce qui n'a pas de sens pour un versement.

**Partie 2 — la boucle à la main.** La difficulté n'est pas algorithmique mais dans le respect
strict du contrat de l'API : le `tool_use_id` doit faire l'aller-retour exact entre la demande et
le résultat, et le résultat repart en rôle `"user"` (pas `"assistant"`), ce qui n'est pas
intuitif au premier abord. Le garde-fou `max_tours` a été vérifié contre `ClientBrutBoucle`, qui
redemande volontairement le même outil à l'infini — sans lui, cette boucle ne s'arrêterait jamais.

**Partie 3 — LangGraph.** Le plus instructif ici est de voir le même comportement se redécouper
en nœuds indépendants : `noeud_agent` ne fait qu'appeler le modèle, `noeud_outils` ne fait
qu'exécuter les outils, `router` ne fait que décider de la suite. Aucune de ces responsabilités
ne se chevauche, ce qui rend chaque nœud testable isolément — contrairement à la boucle à la
main où tout est imbriqué dans une seule fonction.

**Défi commun aux parties 2 et 3.** La gestion d'erreur ne doit jamais faire planter l'appelant.
Dans les deux cas, une exception levée par un outil (police introuvable, par exemple) est
capturée et transformée en un message que Claude peut lire et interpréter — c'est ce qui permet
au système de répondre « vérifiez le numéro » au lieu de planter.
