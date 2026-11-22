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
    age: str = Form(None), # Reçu en string depuis le HTML, on convertira après
    sexe: str = Form(None),
    telephone: str = Form(None),
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    try:
        # Conversion sécurisée de l'âge
        age_int = int(age) if age and age.isdigit() else None
        
        nouveau_patient = models.Patient(
            nom=nom,
            prenom=prenom,
            age=age_int,
            sexe=sexe,
            telephone=telephone,
            labo_id=current_user.labo_id
        )
        
        db.add(nouveau_patient)
        db.commit()
        db.refresh(nouveau_patient)
        
        # Retourne une redirection vers la page patients pour éviter le re-post
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/patients?success=1", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"ERREUR CRÉATION PATIENT: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")

@router.get("/list")
def list_patients(db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    return db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).all()