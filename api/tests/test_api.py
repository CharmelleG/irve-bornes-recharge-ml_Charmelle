"""Tests de l'API IRVE, exécutés sur une copie temporaire de la base.

Lancement depuis la racine du projet :  python -m pytest -v
ou exécution directe du fichier (bouton « Run Python File » de VS Code).
"""
import shutil
import sqlite3
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from fastapi.testclient import TestClient

from api.database import CHEMIN_BASE_DEFAUT
from api.main import app

CLE = "cle-de-test"
ENTETE = {"X-API-Key": CLE}
NOUVEAU_POINT = {
    "id_pdc": "FRTESTE0000001", "id_station": None, "puissance_kw": 150.0,
    "prise_type_2": False, "prise_type_combo_ccs": True, "prise_type_chademo": False,
    "prise_type_ef": False, "date_mise_en_service": "2025-06-30",
}


@pytest.fixture
def base(tmp_path, monkeypatch):
  if not CHEMIN_BASE_DEFAUT.exists():
    pytest.skip("Base absente : exécuter d'abord 02_database_setup.ipynb")
  copie = tmp_path / "irve_test.db"
  shutil.copy(CHEMIN_BASE_DEFAUT, copie)
  monkeypatch.setenv("IRVE_DB_PATH", str(copie))
  monkeypatch.setenv("IRVE_API_KEY", CLE)
  return copie


@pytest.fixture
def client(base):
  with TestClient(app) as client:
    yield client


@pytest.fixture
def station(base):
  with sqlite3.connect(base) as connexion:
    return connexion.execute("SELECT id_station FROM STATION ORDER BY id_station LIMIT 1").fetchone()[0]


@pytest.fixture
def point(station):
  return {**NOUVEAU_POINT, "id_station": station}


def compter(base, table):
  with sqlite3.connect(base) as connexion:
    return connexion.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# --- Lecture ----------------------------------------------------------
def test_racine_redirige_vers_la_documentation(client):
  reponse = client.get("/", follow_redirects=False)
  assert reponse.status_code == 307
  assert reponse.headers["location"] == "/docs"


def test_statistiques_coherentes_avec_la_base(client, base):
  stats = client.get("/stats").json()
  assert stats["communes"] == compter(base, "COMMUNE")
  assert stats["stations"] == compter(base, "STATION")
  assert stats["points_de_charge"] == compter(base, "POINT_DE_CHARGE")
  assert 0 < stats["communes_desert_recharge"] < stats["communes"]


def test_pagination_des_communes(client):
  premiere = client.get("/communes", params={"limit": 5}).json()
  suivante = client.get("/communes", params={"limit": 5, "offset": 5}).json()
  assert len(premiere) == 5 and len(suivante) == 5
  assert {c["code_insee"] for c in premiere}.isdisjoint(c["code_insee"] for c in suivante)


def test_limite_de_pagination_plafonnee(client):
  assert client.get("/communes", params={"limit": 501}).status_code == 422


def test_filtre_desert_et_departement(client):
  communes = client.get("/communes", params={"desert_recharge": True, "code_departement": "58"}).json()
  assert communes
  assert all(c["desert_recharge"] and c["code_departement"] == "58" for c in communes)
  assert all(c["distance_pdc_km"] > 10 for c in communes)


def test_fiche_commune(client):
  paris = client.get("/communes/75056").json()
  assert paris["nom_commune"] == "Paris"
  assert paris["nb_pdc"] > 0 and paris["pdc_pour_10000_hab"] > 0
  assert paris["desert_recharge"] is False


def test_commune_code_invalide_ou_inconnu(client):
  assert client.get("/communes/ABC").status_code == 422
  assert client.get("/communes/99999").status_code == 404


def test_deserts_tries_par_population(client):
  deserts = client.get("/deserts", params={"limit": 20}).json()
  populations = [c["population"] for c in deserts]
  assert populations == sorted(populations, reverse=True)
  assert all(c["desert_recharge"] for c in deserts)
  assert client.get("/deserts", params={"type_desert": "autre"}).status_code == 422


def test_fiche_station_avec_ses_points(client, station):
  fiche = client.get(f"/stations/{station}").json()
  assert fiche["id_station"] == station
  assert fiche["points_de_charge"]
  assert all(p["id_station"] == station for p in fiche["points_de_charge"])


def test_filtre_puissance_minimale(client):
  points = client.get("/points-de-charge", params={"puissance_min": 150, "limit": 100}).json()
  assert points and all(p["puissance_kw"] >= 150 for p in points)


def test_point_inexistant(client):
  assert client.get("/points-de-charge/FRINEXISTANT").status_code == 404


def test_injection_sql_sans_effet(client, base):
  avant = compter(base, "STATION")
  assert client.get("/stations", params={"code_insee": "75056' OR '1'='1"}).status_code == 422
  assert client.get("/stations/X'; DROP TABLE STATION; --").status_code in (404, 422)
  assert compter(base, "STATION") == avant


# --- Sécurité des écritures -------------------------------------------
@pytest.mark.parametrize("methode, chemin", [
    ("post", "/points-de-charge"),
    ("put", "/points-de-charge/FRTESTE0000001"),
    ("patch", "/points-de-charge/FRTESTE0000001"),
    ("delete", "/points-de-charge/FRTESTE0000001"),
])
def test_ecriture_refusee_sans_cle(client, point, methode, chemin):
  corps = {} if methode == "delete" else {"json": point}
  assert client.request(methode.upper(), chemin, **corps).status_code == 401
  assert client.request(methode.upper(), chemin, headers={"X-API-Key": "mauvaise"},
                        **corps).status_code == 401


def test_ecriture_desactivee_sans_cle_configuree(client, point, monkeypatch, tmp_path):
  monkeypatch.delenv("IRVE_API_KEY")
  monkeypatch.setattr("api.security.RACINE_PROJET", tmp_path)
  assert client.post("/points-de-charge", json=point, headers=ENTETE).status_code == 503


# --- Cycle CRUD complet -----------------------------------------------
def test_cycle_creation_lecture_modification_suppression(client, base, point):
  avant = compter(base, "POINT_DE_CHARGE")

  cree = client.post("/points-de-charge", json=point, headers=ENTETE)
  assert cree.status_code == 201
  assert cree.json()["puissance_kw"] == 150.0
  assert compter(base, "POINT_DE_CHARGE") == avant + 1

  lu = client.get(f"/points-de-charge/{point['id_pdc']}")
  assert lu.status_code == 200 and lu.json()["prise_type_combo_ccs"] is True

  remplacement = {k: v for k, v in point.items() if k != "id_pdc"} | {"puissance_kw": 300.0}
  remplace = client.put(f"/points-de-charge/{point['id_pdc']}", json=remplacement, headers=ENTETE)
  assert remplace.status_code == 200 and remplace.json()["puissance_kw"] == 300.0

  modifie = client.patch(f"/points-de-charge/{point['id_pdc']}",
                         json={"prise_type_2": True}, headers=ENTETE)
  assert modifie.status_code == 200
  assert modifie.json()["prise_type_2"] is True and modifie.json()["puissance_kw"] == 300.0

  supprime = client.delete(f"/points-de-charge/{point['id_pdc']}", headers=ENTETE)
  assert supprime.status_code == 204
  assert client.get(f"/points-de-charge/{point['id_pdc']}").status_code == 404
  assert compter(base, "POINT_DE_CHARGE") == avant


# --- Validation des entrées -------------------------------------------
def test_creation_en_double(client, point):
  assert client.post("/points-de-charge", json=point, headers=ENTETE).status_code == 201
  assert client.post("/points-de-charge", json=point, headers=ENTETE).status_code == 409


def test_creation_dans_une_station_inexistante(client, point):
  reponse = client.post("/points-de-charge", json=point | {"id_station": "FRINEXISTANTE"},
                        headers=ENTETE)
  assert reponse.status_code == 422


@pytest.mark.parametrize("champ, valeur", [
    ("puissance_kw", 0), ("puissance_kw", 601), ("puissance_kw", "rapide"),
    ("date_mise_en_service", "2099-01-01"), ("date_mise_en_service", "1990-01-01"),
    ("prise_type_2", "peut-être"), ("id_pdc", "id avec espaces"), ("champ_inconnu", 1),
])
def test_entree_invalide_refusee(client, point, champ, valeur):
  assert client.post("/points-de-charge", json=point | {champ: valeur},
                     headers=ENTETE).status_code == 422


def test_modification_partielle_vide_refusee(client, point):
  client.post("/points-de-charge", json=point, headers=ENTETE)
  assert client.patch(f"/points-de-charge/{point['id_pdc']}", json={},
                      headers=ENTETE).status_code == 422



if __name__ == "__main__":
  sys.exit(pytest.main([__file__, "-v"]))
