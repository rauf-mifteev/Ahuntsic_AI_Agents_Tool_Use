"""Partie 1 - les outils. Tests FOURNIS, ne pas modifier.

Version allegee (seance 1h30) : les cas limites redondants ont ete
retires, seuls les comportements essentiels restent verifies.
"""
import pytest

from agent.outils import (
    BASE_DOSSIERS, CLAUSES, DISPATCH, OUTILS_SCHEMA, SYSTEM,
    chercher_police, rechercher_clause, calculer_indemnite,
)


# ── chercher_police ──
def test_police_existante():
    assert chercher_police("POL-4471")["avenants"] == ["RE-04"]


def test_police_inconnue_message_actionnable():
    with pytest.raises(KeyError) as e:
        chercher_police("POL-9999")
    assert "verifiez" in str(e.value).lower()


# ── rechercher_clause ──
def test_clause_refoulement_mentionne_l_avenant():
    assert "RE-04" in rechercher_clause("refoulement")


def test_clause_cite_la_source():
    assert "p.12" in rechercher_clause("collision")


def test_sujet_inconnu_liste_les_options():
    r = rechercher_clause("incendie")
    assert "Aucune clause" in r and "refoulement" in r


# ── calculer_indemnite ──
def test_indemnite_simple():
    r = calculer_indemnite(18000, 1000, 25000)
    assert r["indemnite"] == 17000.0 and r["plafonne"] is False


def test_indemnite_plafonnee():
    r = calculer_indemnite(40000, 1000, 25000)
    assert r["indemnite"] == 25000.0 and r["plafonne"] is True


def test_indemnite_jamais_negative():
    assert calculer_indemnite(300, 500)["indemnite"] == 0.0


# ── schemas JSON ──
def test_trois_outils_declares():
    assert len(OUTILS_SCHEMA) == 3


def test_les_noms_correspondent_au_dispatch():
    noms = {o["name"] for o in OUTILS_SCHEMA}
    assert noms == set(DISPATCH)


def test_chaque_outil_a_les_cles_requises():
    for o in OUTILS_SCHEMA:
        assert set(o) == {"name", "description", "input_schema"}
        assert o["input_schema"]["type"] == "object"
        assert "properties" in o["input_schema"]
        assert "required" in o["input_schema"]


def test_les_descriptions_sont_substantielles():
    for o in OUTILS_SCHEMA:
        assert len(o["description"]) > 80, o["name"]


def test_le_system_prompt_impose_le_calcul_par_outil():
    assert "calculer_indemnite" in SYSTEM
