from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["Patients"])

@router.post("/create")
def create_patient(nom: str, prenom: str, age: int = None, sexe: str = None, telephone: str = None, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    nouveau_patient = models.Patient(
        nom=nom,
        prenom=prenom,
        age=age,
        sexe=sexe,
        telephone=telephone,
        labo_id=current_user.labo_id
    )
    db.add(nouveau_patient)
    db.commit()
    db.refresh(nouveau_patient)
    return {"message": "Patient créé avec succès", "patient": nouveau_patient}

@router.get("/list")
def list_patients(db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    patients = db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).all()
    return patients