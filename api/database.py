"""Connexion à la base SQLite IRVE."""
import os
import sqlite3
from pathlib import Path

RACINE_PROJET = Path(__file__).resolve().parent.parent
CHEMIN_BASE_DEFAUT = RACINE_PROJET / "data" / "database" / "irve_database.db"


def chemin_base() -> Path:
  """Chemin de la base : variable d'environnement IRVE_DB_PATH, sinon data/database/."""
  return Path(os.environ.get("IRVE_DB_PATH", CHEMIN_BASE_DEFAUT))


def get_connexion():
  """Ouvre une connexion par requête, clés étrangères activées, fermée dans tous les cas."""
  chemin = chemin_base()
  if not chemin.exists():
    raise RuntimeError(f"Base introuvable : {chemin}. Exécuter 02_database_setup.ipynb.")
  connexion = sqlite3.connect(chemin, check_same_thread=False)
  connexion.row_factory = sqlite3.Row
  connexion.execute("PRAGMA foreign_keys = ON")
  try:
    yield connexion
  finally:
    connexion.close()
