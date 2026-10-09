"""API REST IRVE : lecture des communes, stations et points de charge, gestion des points.

Lancement depuis la racine du projet :
    uvicorn api.main:app --host 127.0.0.1 --port 8003
ou exécution directe du fichier (bouton « Run Python File » de VS Code) :
    python api/main.py
"""
import sqlite3
import sys
from pathlib import Path as Chemin
from typing import Literal

if __package__ in (None, ""):
  sys.path.insert(0, str(Chemin(__file__).resolve().parent.parent))

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from api.database import get_connexion
from api.schemas import (MOTIF_ID_PDC, MOTIF_ID_STATION, Commune, PointDeCharge,
                         PointDeChargeContenu, PointDeChargeCreation,
                         PointDeChargeModification, Station, StationDetail, Statistiques)
from api.security import verifier_cle

LIMITE_MAX = 500
PUISSANCE_150KW = 150
MOTIF_INSEE = r"^(\d{5}|2[AB]\d{3})$"

app = FastAPI(
    title="API IRVE : maillage des points de recharge",
    description=(
        "Données issues du fichier consolidé IRVE (data.gouv.fr), nettoyées et rattachées aux "
        "communes 2025. Lecture publique ; création, modification et suppression des points de "
        "charge réservées aux détenteurs de la clé d'API (en-tête `X-API-Key`)."),
    version="2.0.0",
)


@app.exception_handler(sqlite3.IntegrityError)
def conflit_integrite(_: Request, erreur: sqlite3.IntegrityError) -> JSONResponse:
  return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                      content={"detail": f"Contrainte d'intégrité non respectée : {erreur}"})


# --- Requêtes communes ----------------------------------------------
SELECT_COMMUNE = f"""
SELECT c.code_insee, c.nom_commune, c.code_departement, d.nom_departement,
       r.nom_region AS region, c.population, c.distance_pdc_km, c.distance_150kw_km,
       c.desert_recharge, c.desert_150kw,
       (SELECT COUNT(*) FROM STATION s WHERE s.code_insee = c.code_insee) AS nb_stations,
       (SELECT COUNT(*) FROM POINT_DE_CHARGE p JOIN STATION s ON s.id_station = p.id_station
         WHERE s.code_insee = c.code_insee) AS nb_pdc,
       (SELECT COUNT(*) FROM POINT_DE_CHARGE p JOIN STATION s ON s.id_station = p.id_station
         WHERE s.code_insee = c.code_insee AND p.puissance_kw >= {PUISSANCE_150KW}) AS nb_pdc_150kw
FROM COMMUNE c
JOIN DEPARTEMENT d ON d.code_departement = c.code_departement
JOIN REGION r ON r.code_region = d.code_region
"""

SELECT_STATION = """
SELECT s.id_station, s.nom_station, s.adresse_station, s.implantation_station,
       s.condition_acces, s.latitude, s.longitude, s.code_insee,
       a.nom_acteur AS amenageur, o.nom_acteur AS operateur
FROM STATION s
JOIN ACTEUR a ON a.id_acteur = s.id_amenageur
JOIN ACTEUR o ON o.id_acteur = s.id_operateur
"""

COLONNES_POINT = ["id_pdc", "puissance_kw", "prise_type_2", "prise_type_combo_ccs",
                  "prise_type_chademo", "prise_type_ef", "date_mise_en_service", "id_station"]


def commune_en_dict(ligne: sqlite3.Row) -> dict:
  commune = dict(ligne)
  commune["pdc_pour_10000_hab"] = (round(commune["nb_pdc"] * 10000 / commune["population"], 1)
                                   if commune["population"] else None)
  return commune


def lire_point(connexion: sqlite3.Connection, id_pdc: str) -> dict:
  ligne = connexion.execute(f"SELECT {', '.join(COLONNES_POINT)} FROM POINT_DE_CHARGE "
                            "WHERE id_pdc = ?", (id_pdc,)).fetchone()
  if ligne is None:
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"Point de charge {id_pdc} introuvable")
  return dict(ligne)


def verifier_station(connexion: sqlite3.Connection, id_station: str) -> None:
  if connexion.execute("SELECT 1 FROM STATION WHERE id_station = ?", (id_station,)).fetchone() is None:
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                        f"Station {id_station} inexistante : créer le point dans une station existante")


def valeurs_sql(donnees: dict) -> dict:
  """Booléens en 0/1 et dates au format ISO, comme dans la base."""
  return {cle: (int(v) if isinstance(v, bool) else v.isoformat() if hasattr(v, "isoformat") else v)
          for cle, v in donnees.items()}


# --- Général ----------------------------------------------------------
@app.get("/", include_in_schema=False)
def racine():
  return RedirectResponse(url="/docs")


@app.get("/stats", response_model=Statistiques, tags=["Statistiques"],
         summary="Chiffres clés du réseau et des déserts de recharge")
def statistiques(connexion: sqlite3.Connection = Depends(get_connexion)):
  return dict(connexion.execute(f"""
      SELECT (SELECT COUNT(*) FROM COMMUNE) AS communes,
             (SELECT COUNT(*) FROM STATION) AS stations,
             (SELECT COUNT(*) FROM POINT_DE_CHARGE) AS points_de_charge,
             (SELECT COUNT(*) FROM POINT_DE_CHARGE WHERE puissance_kw >= {PUISSANCE_150KW}) AS points_150kw,
             (SELECT COUNT(*) FROM COMMUNE WHERE desert_recharge = 1) AS communes_desert_recharge,
             (SELECT COALESCE(SUM(population), 0) FROM COMMUNE WHERE desert_recharge = 1) AS habitants_desert_recharge,
             (SELECT COUNT(*) FROM COMMUNE WHERE desert_150kw = 1) AS communes_desert_150kw,
             (SELECT COALESCE(SUM(population), 0) FROM COMMUNE WHERE desert_150kw = 1) AS habitants_desert_150kw
  """).fetchone())


# --- Communes ---------------------------------------------------------
@app.get("/communes", response_model=list[Commune], tags=["Communes"],
         summary="Lister les communes, avec filtres et pagination")
def lister_communes(
    code_departement: str | None = Query(None, pattern=r"^(\d{2}|2[AB]|97\d)$", examples=["58"]),
    region: str | None = Query(None, max_length=60, examples=["Bourgogne-Franche-Comté"]),
    desert_recharge: bool | None = None,
    desert_150kw: bool | None = None,
    limit: int = Query(50, ge=1, le=LIMITE_MAX),
    offset: int = Query(0, ge=0),
    connexion: sqlite3.Connection = Depends(get_connexion),
):
  conditions, parametres = [], []
  for colonne, valeur in [("c.code_departement", code_departement), ("r.nom_region", region),
                          ("c.desert_recharge", desert_recharge), ("c.desert_150kw", desert_150kw)]:
    if valeur is not None:
      conditions.append(f"{colonne} = ?")
      parametres.append(int(valeur) if isinstance(valeur, bool) else valeur)
  where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
  lignes = connexion.execute(f"{SELECT_COMMUNE} {where} ORDER BY c.code_insee LIMIT ? OFFSET ?",
                             (*parametres, limit, offset)).fetchall()
  return [commune_en_dict(ligne) for ligne in lignes]


@app.get("/communes/{code_insee}", response_model=Commune, tags=["Communes"],
         summary="Fiche d'une commune : équipement et distances")
def lire_commune(code_insee: str = Path(..., pattern=MOTIF_INSEE, examples=["58194"]),
                 connexion: sqlite3.Connection = Depends(get_connexion)):
  ligne = connexion.execute(f"{SELECT_COMMUNE} WHERE c.code_insee = ?", (code_insee,)).fetchone()
  if ligne is None:
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"Commune {code_insee} introuvable")
  return commune_en_dict(ligne)


@app.get("/deserts", response_model=list[Commune], tags=["Communes"],
         summary="Communes en désert de recharge, les plus peuplées d'abord")
def lister_deserts(type_desert: Literal["recharge", "150kw"] = "recharge",
                   limit: int = Query(50, ge=1, le=LIMITE_MAX),
                   offset: int = Query(0, ge=0),
                   connexion: sqlite3.Connection = Depends(get_connexion)):
  colonne = "c.desert_recharge" if type_desert == "recharge" else "c.desert_150kw"
  lignes = connexion.execute(
      f"{SELECT_COMMUNE} WHERE {colonne} = 1 ORDER BY c.population DESC LIMIT ? OFFSET ?",
      (limit, offset)).fetchall()
  return [commune_en_dict(ligne) for ligne in lignes]


# --- Stations ---------------------------------------------------------
@app.get("/stations", response_model=list[Station], tags=["Stations"],
         summary="Lister les stations, éventuellement d'une commune")
def lister_stations(code_insee: str | None = Query(None, pattern=MOTIF_INSEE),
                    limit: int = Query(50, ge=1, le=LIMITE_MAX),
                    offset: int = Query(0, ge=0),
                    connexion: sqlite3.Connection = Depends(get_connexion)):
  where, parametres = ("WHERE s.code_insee = ?", [code_insee]) if code_insee else ("", [])
  lignes = connexion.execute(f"{SELECT_STATION} {where} ORDER BY s.id_station LIMIT ? OFFSET ?",
                             (*parametres, limit, offset)).fetchall()
  return [dict(ligne) for ligne in lignes]


@app.get("/stations/{id_station}", response_model=StationDetail, tags=["Stations"],
         summary="Fiche d'une station et de ses points de charge")
def lire_station(id_station: str = Path(..., pattern=MOTIF_ID_STATION),
                 connexion: sqlite3.Connection = Depends(get_connexion)):
  ligne = connexion.execute(f"{SELECT_STATION} WHERE s.id_station = ?", (id_station,)).fetchone()
  if ligne is None:
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"Station {id_station} introuvable")
  points = connexion.execute(f"SELECT {', '.join(COLONNES_POINT)} FROM POINT_DE_CHARGE "
                             "WHERE id_station = ? ORDER BY id_pdc", (id_station,)).fetchall()
  return {**dict(ligne), "points_de_charge": [dict(p) for p in points]}


# --- Points de charge : lecture -----------------------------------------
@app.get("/points-de-charge", response_model=list[PointDeCharge], tags=["Points de charge"],
         summary="Lister les points de charge")
def lister_points(id_station: str | None = Query(None, pattern=MOTIF_ID_STATION),
                  puissance_min: float | None = Query(None, ge=0, le=600),
                  limit: int = Query(50, ge=1, le=LIMITE_MAX),
                  offset: int = Query(0, ge=0),
                  connexion: sqlite3.Connection = Depends(get_connexion)):
  conditions, parametres = [], []
  if id_station is not None:
    conditions.append("id_station = ?")
    parametres.append(id_station)
  if puissance_min is not None:
    conditions.append("puissance_kw >= ?")
    parametres.append(puissance_min)
  where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
  lignes = connexion.execute(f"SELECT {', '.join(COLONNES_POINT)} FROM POINT_DE_CHARGE {where} "
                             "ORDER BY id_pdc LIMIT ? OFFSET ?",
                             (*parametres, limit, offset)).fetchall()
  return [dict(ligne) for ligne in lignes]


@app.get("/points-de-charge/{id_pdc}", response_model=PointDeCharge, tags=["Points de charge"],
         summary="Fiche d'un point de charge")
def lire_point_de_charge(id_pdc: str = Path(..., pattern=MOTIF_ID_PDC),
                         connexion: sqlite3.Connection = Depends(get_connexion)):
  return lire_point(connexion, id_pdc)


# --- Points de charge : écriture (clé d'API) ----------------------------
@app.post("/points-de-charge", response_model=PointDeCharge, status_code=status.HTTP_201_CREATED,
          tags=["Points de charge"], summary="Créer un point de charge",
          dependencies=[Depends(verifier_cle)])
def creer_point(point: PointDeChargeCreation,
                connexion: sqlite3.Connection = Depends(get_connexion)):
  if connexion.execute("SELECT 1 FROM POINT_DE_CHARGE WHERE id_pdc = ?",
                       (point.id_pdc,)).fetchone():
    raise HTTPException(status.HTTP_409_CONFLICT, f"Le point de charge {point.id_pdc} existe déjà")
  verifier_station(connexion, point.id_station)
  donnees = valeurs_sql(point.model_dump())
  connexion.execute(f"INSERT INTO POINT_DE_CHARGE ({', '.join(donnees)}) "
                    f"VALUES ({', '.join('?' * len(donnees))})", tuple(donnees.values()))
  connexion.commit()
  return lire_point(connexion, point.id_pdc)


@app.put("/points-de-charge/{id_pdc}", response_model=PointDeCharge, tags=["Points de charge"],
         summary="Remplacer toutes les caractéristiques d'un point de charge",
         dependencies=[Depends(verifier_cle)])
def remplacer_point(contenu: PointDeChargeContenu,
                    id_pdc: str = Path(..., pattern=MOTIF_ID_PDC),
                    connexion: sqlite3.Connection = Depends(get_connexion)):
  lire_point(connexion, id_pdc)
  verifier_station(connexion, contenu.id_station)
  donnees = valeurs_sql(contenu.model_dump())
  connexion.execute(f"UPDATE POINT_DE_CHARGE SET {', '.join(f'{c} = ?' for c in donnees)} "
                    "WHERE id_pdc = ?", (*donnees.values(), id_pdc))
  connexion.commit()
  return lire_point(connexion, id_pdc)


@app.patch("/points-de-charge/{id_pdc}", response_model=PointDeCharge, tags=["Points de charge"],
           summary="Modifier une partie des caractéristiques d'un point de charge",
           dependencies=[Depends(verifier_cle)])
def modifier_point(modification: PointDeChargeModification,
                   id_pdc: str = Path(..., pattern=MOTIF_ID_PDC),
                   connexion: sqlite3.Connection = Depends(get_connexion)):
  lire_point(connexion, id_pdc)
  donnees = valeurs_sql(modification.model_dump(exclude_unset=True))
  if "id_station" in donnees:
    verifier_station(connexion, donnees["id_station"])
  connexion.execute(f"UPDATE POINT_DE_CHARGE SET {', '.join(f'{c} = ?' for c in donnees)} "
                    "WHERE id_pdc = ?", (*donnees.values(), id_pdc))
  connexion.commit()
  return lire_point(connexion, id_pdc)


@app.delete("/points-de-charge/{id_pdc}", status_code=status.HTTP_204_NO_CONTENT,
            tags=["Points de charge"], summary="Supprimer un point de charge",
            dependencies=[Depends(verifier_cle)])
def supprimer_point(id_pdc: str = Path(..., pattern=MOTIF_ID_PDC),
                    connexion: sqlite3.Connection = Depends(get_connexion)):
  lire_point(connexion, id_pdc)
  connexion.execute("DELETE FROM POINT_DE_CHARGE WHERE id_pdc = ?", (id_pdc,))
  connexion.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
  print("Documentation interactive : http://127.0.0.1:8003/docs (Ctrl+C pour arrêter)")
  uvicorn.run("api.main:app", host="127.0.0.1", port=8003)
