from pydantic import BaseModel

class AnalyseRequest(BaseModel):
    patient_id: str
    type_analyse: str

class AnalyseResponse(BaseModel):
    patient_id: str
    resultat: str
    statut: str

class UserCreate(BaseModel):
    email: str
    password: str