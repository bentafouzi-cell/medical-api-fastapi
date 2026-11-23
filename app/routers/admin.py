from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/labos")
def lister_labos(db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    
    labos = db.query(models.LaboDB).all()
    result = []
    for labo in labos:
        nb_users = db.query(models.UserDB).filter(models.UserDB.labo_id == labo.id).count()
        nb_patients = db.query(models.Patient).filter(models.Patient.labo_id == labo.id).count()
        nb_analyses = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == labo.id).count()
        result.append({
            "id": labo.id,
            "nom": labo.nom,
            "created_at": labo.created_at.strftime("%d/%m/%Y") if labo.created_at else "",
            "nb_users": nb_users,
            "nb_patients": nb_patients,
            "nb_analyses": nb_analyses
        })
    return result