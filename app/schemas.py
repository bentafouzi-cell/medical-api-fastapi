from pydantic import BaseModel
from typing import List, Optional

# --- Schémas pour les Patients ---
class PatientCreate(BaseModel):
    nom: str
    prenom: str
    age: Optional[int] = None
    sexe: Optional[str] = None
    telephone: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    age: Optional[int] = None
    sexe: Optional[str] = None
    telephone: Optional[str] = None

    class Config:
        orm_mode = True

# --- Schémas pour les Analyses ---
class AnalyseRequest(BaseModel):
    patient_id: int  # On passe de str à int
    type_analyse: str

class AnalyseResponse(BaseModel):
    id: int
    patient_id: int
    type_analyse: str
    statut: str
    created_at: str

    class Config:
        orm_mode = True

# --- Schémas pour l'Authentification ---
class UserCreate(BaseModel):
    email: str
    password: str