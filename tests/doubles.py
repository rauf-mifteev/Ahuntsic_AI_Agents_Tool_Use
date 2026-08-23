"""Doubles de test - fournis, ne pas modifier.

Simulent Claude de facon deterministe, pour la boucle a la main
(API brute) et pour LangGraph (messages LangChain).
"""
import re


# ═══════════ Double pour l'API brute (bloc 1) ═══════════
class _Bloc:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Rep:
    def __init__(self, stop_reason, content):
        self.stop_reason = stop_reason
        self.content = content


class ClientBrutDouble:
    """Rejoue un scenario tool use realiste sur l'API brute."""

    def __init__(self):
        self.tour = 0

    class _M:
        def __init__(self, outer):
            self.outer = outer

        def create(self, model=None, max_tokens=None, system=None,
                   tools=None, messages=None, **kw):
            self.outer.tour += 1
            humain = " ".join(
                m["content"] for m in messages
                if m["role"] == "user" and isinstance(m["content"], str)
            ).lower()
            deja = []
            for m in messages:
                if m["role"] == "assistant" and not isinstance(m["content"], str):
                    deja += [b.name for b in m["content"]
                             if getattr(b, "type", "") == "tool_use"]
            erreurs = any(
                bloc.get("is_error")
                for m in messages
                if m["role"] == "user" and isinstance(m["content"], list)
                for bloc in m["content"])

            if erreurs:
                return _Rep("end_turn", [_Bloc(
                    type="text",
                    text="Le numero de police est introuvable. "
                         "Pouvez-vous le verifier ?")])

            if "chercher_police" not in deja:
                num = re.search(r"pol-\w{4}", humain)
                num = num.group(0).upper() if num else "POL-0000"
                return _Rep("tool_use", [
                    _Bloc(type="text", text="Je consulte la police."),
                    _Bloc(type="tool_use", id="t1", name="chercher_police",
                          input={"numero": num})])

            if "rechercher_clause" not in deja:
                return _Rep("tool_use", [
                    _Bloc(type="tool_use", id="t2",
                          name="rechercher_clause",
                          input={"sujet": "refoulement"})])

            if "calculer_indemnite" not in deja:
                return _Rep("tool_use", [
                    _Bloc(type="tool_use", id="t3",
                          name="calculer_indemnite",
                          input={"montant_dommages": 18000,
                                 "franchise": 1000, "maximum": 25000})])

            return _Rep("end_turn", [_Bloc(
                type="text",
                text="Indemnite : 17000 $ apres franchise de 1000 $ "
                     "(clause 7.3.2, p.12).")])

    @property
    def messages(self):
        return ClientBrutDouble._M(self)


class ClientBrutBoucle:
    """Redemande indefiniment le meme outil : teste le garde-fou."""

    class _M:
        def create(self, **kw):
            return _Rep("tool_use", [
                _Bloc(type="tool_use", id="x", name="rechercher_clause",
                      input={"sujet": "collision"})])

    @property
    def messages(self):
        return ClientBrutBoucle._M()


# ═══════════ Double pour LangGraph (blocs 3 a 6) ═══════════
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


class ModeleDouble:
    """Mime llm.bind_tools(...).invoke(messages)."""

    def bind_tools(self, outils):
        return self

    def invoke(self, messages, **kw):
        deja = [m.name for m in messages if isinstance(m, ToolMessage)]
        humain = " ".join(
            m.content for m in messages
            if isinstance(m, HumanMessage)).lower()
        erreur = any("introuvable" in str(m.content).lower()
                     for m in messages if isinstance(m, ToolMessage))

        if erreur:
            return AIMessage(content="Le numero de police est introuvable. "
                                     "Pouvez-vous le verifier ?")
        if "chercher_police" not in deja:
            num = re.search(r"pol-\w{4}", humain)
            num = num.group(0).upper() if num else "POL-0000"
            return AIMessage(content="", tool_calls=[{
                "name": "chercher_police", "args": {"numero": num},
                "id": "c1"}])
        if "rechercher_clause" not in deja:
            return AIMessage(content="", tool_calls=[{
                "name": "rechercher_clause",
                "args": {"sujet": "refoulement"}, "id": "c2"}])
        if "calculer_indemnite" not in deja:
            return AIMessage(content="", tool_calls=[{
                "name": "calculer_indemnite",
                "args": {"montant_dommages": 18000, "franchise": 1000,
                         "maximum": 25000}, "id": "c3"}])
        return AIMessage(content="Indemnite de 17000 $ apres franchise de "
                                 "1000 $ (clause 7.3.2, p.12).")


class ModeleBoucle:
    """Redemande indefiniment le meme outil."""

    def bind_tools(self, o):
        return self

    def invoke(self, messages, **kw):
        return AIMessage(content="", tool_calls=[{
            "name": "rechercher_clause", "args": {"sujet": "collision"},
            "id": "x"}])
