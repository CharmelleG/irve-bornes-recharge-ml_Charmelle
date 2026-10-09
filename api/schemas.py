"""Modèles de validation des entrées et de description des sorties."""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PUISSANCE_MAX_KW = 600
DATE_MIN = date(2000, 1, 1)
MOTIF_ID_PDC = r"^[A-Z0-9_]{3,60}$"
MOTIF_ID_STATION = r"^[A-Z0-9_.\-]{3,60}$"


def controler_date(valeur: date | None) -> date | None:
  if valeur is not None and not DATE_MIN <= valeur <= date.today():
    raise ValueError(f"la date doit être comprise entre {DATE_MIN} et aujourd'hui")
  return valeur


# --- Points de charge : entrées -------------------------------------
class PointDeChargeContenu(BaseModel):
  model_config = ConfigDict(extra="forbid")

  id_station: str = Field(..., pattern=MOTIF_ID_STATION, examples=["FRV75PDUR03"])
  puissance_kw: float = Field(..., gt=0, le=PUISSANCE_MAX_KW, examples=[150.0])
  prise_type_2: bool = Field(..., examples=[False])
  prise_type_combo_ccs: bool = Field(..., examples=[True])
  prise_type_chademo: bool = Field(..., examples=[False])
  prise_type_ef: bool = Field(..., examples=[False])
  date_mise_en_service: date | None = Field(None, examples=["2025-06-30"])

  _date = field_validator("date_mise_en_service")(controler_date)


class PointDeChargeCreation(PointDeChargeContenu):
  id_pdc: str = Field(..., pattern=MOTIF_ID_PDC, examples=["FRXYZE00001"])


class PointDeChargeModification(BaseModel):
  model_config = ConfigDict(extra="forbid")

  id_station: str | None = Field(None, pattern=MOTIF_ID_STATION)
  puissance_kw: float | None = Field(None, gt=0, le=PUISSANCE_MAX_KW)
  prise_type_2: bool | None = None
  prise_type_combo_ccs: bool | None = None
  prise_type_chademo: bool | None = None
  prise_type_ef: bool | None = None
  date_mise_en_service: date | None = None

  _date = field_validator("date_mise_en_service")(controler_date)

  @model_validator(mode="after")
  def au_moins_un_champ(self):
    if not self.model_fields_set:
      raise ValueError("au moins un champ doit être fourni")
    return self


# --- Sorties --------------------------------------------------------
class PointDeCharge(BaseModel):
  id_pdc: str
  id_station: str
  puissance_kw: float
  prise_type_2: bool
  prise_type_combo_ccs: bool
  prise_type_chademo: bool
  prise_type_ef: bool
  date_mise_en_service: date | None


class Station(BaseModel):
  id_station: str
  nom_station: str
  adresse_station: str
  implantation_station: str
  condition_acces: str
  latitude: float
  longitude: float
  code_insee: str
  amenageur: str
  operateur: str


class StationDetail(Station):
  points_de_charge: list[PointDeCharge]


class Commune(BaseModel):
  code_insee: str
  nom_commune: str
  code_departement: str
  nom_departement: str
  region: str
  population: int
  nb_stations: int
  nb_pdc: int
  nb_pdc_150kw: int
  pdc_pour_10000_hab: float | None
  distance_pdc_km: float
  distance_150kw_km: float
  desert_recharge: bool
  desert_150kw: bool


class Statistiques(BaseModel):
  communes: int
  stations: int
  points_de_charge: int
  points_150kw: int
  communes_desert_recharge: int
  habitants_desert_recharge: int
  communes_desert_150kw: int
  habitants_desert_150kw: int
