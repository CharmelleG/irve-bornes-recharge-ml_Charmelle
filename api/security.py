"""Contrôle de la clé d'API exigée pour les opérations d'écriture."""
import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from api.database import RACINE_PROJET

entete_cle = APIKeyHeader(name="X-API-Key", auto_error=False,
                          description="Clé d'API exigée pour POST, PUT, PATCH et DELETE")


def cle_attendue() -> str | None:
  """Clé lue dans la variable d'environnement IRVE_API_KEY, sinon dans le fichier .env."""
  if os.environ.get("IRVE_API_KEY"):
    return os.environ["IRVE_API_KEY"]
  fichier_env = RACINE_PROJET / ".env"
  if fichier_env.exists():
    for ligne in fichier_env.read_text(encoding="utf-8").splitlines():
      nom, _, valeur = ligne.partition("=")
      if nom.strip() == "IRVE_API_KEY" and valeur.strip():
        return valeur.strip()
  return None


def verifier_cle(cle_recue: str | None = Security(entete_cle)) -> None:
  cle = cle_attendue()
  if cle is None:
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                        "Écriture désactivée : aucune clé d'API n'est configurée sur le serveur")
  if cle_recue is None or not secrets.compare_digest(cle_recue, cle):
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clé d'API absente ou invalide",
                        headers={"WWW-Authenticate": "API-Key"})
