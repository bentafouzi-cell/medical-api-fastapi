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

    # VÉRIFICATION CRUCIALE : Empêcher la suppression si le patient a des analyses
    analyses_count = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.patient_id == patient_id
    ).count()

    if analyses_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Impossible de supprimer ce patient : il a {analyses_count} analyse(s) enregistrée(s). Supprimez d'abord les analyses."
        )

    db.delete(patient)
    db.commit()

    return RedirectResponse(url="/patients", status_code=303)