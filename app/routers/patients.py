from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.post("/create")
def create_patient(
    nom: str = Form(...),
    prenom: str = Form(...),
    age: Optional[str] = Form(None),
    sexe: Optional[str] = Form(None),
    telephone: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    try:
        age_int = int(age) if age and age.strip().isdigit() else None

        nouveau_patient = models.Patient(
            nom=nom.strip(),
            prenom=prenom.strip(),
            age=age_int,
            sexe=sexe,
            telephone=telephone,
            labo_id=current_user.labo_id
        )

        db.add(nouveau_patient)
        db.commit()
        db.refresh(nouveau_patient)

        return RedirectResponse(url="/patients?success=1", status_code=303)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")


@router.get("/list")
def list_patients(
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    return db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).all()


@router.post("/{patient_id}/delete")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.labo_id == current_user.labo_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    analyses_count = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.patient_id == patient_id
    ).count()

    if analyses_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de supprimer ce patient : il a {analyses_count} analyse(s). Supprimez d'abord les analyses."
        )

    db.delete(patient)
    db.commit()

    return RedirectResponse(url="/patients", status_code=303)