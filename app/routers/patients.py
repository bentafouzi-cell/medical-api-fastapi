from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["Patients"])

@router.post("/create")
def create_patient(
    nom: str = Form(...),
    prenom: str = Form(...),
    age: int = Form(None),
    sexe: str = Form(None),
    telephone: str = Form(None),
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    try:
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
        return {"message": "Patient créé", "id": nouveau_patient.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def list_patients(db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    return db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).all()