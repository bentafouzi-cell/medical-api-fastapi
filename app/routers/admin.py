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
            "is_active": labo.is_active,
            "created_at": labo.created_at.strftime("%d/%m/%Y") if labo.created_at else "",
            "nb_users": nb_users,
            "nb_patients": nb_patients,
            "nb_analyses": nb_analyses
        })
    return result

@router.post("/labos/{labo_id}/toggle")
def toggle_labo(labo_id: int, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    
    labo = db.query(models.LaboDB).filter(models.LaboDB.id == labo_id).first()
    if labo is not None and labo.id == current_user.labo_id:
        # Se suspendre ou se supprimer soi-meme = se verrouiller dehors, sans
        # aucun moyen de revenir en arriere depuis l'interface.
        raise HTTPException(
            status_code=400,
            detail="Impossible de modifier le laboratoire de votre propre compte administrateur",
        )
    if not labo:
        raise HTTPException(status_code=404, detail="Laboratoire non trouvé")
    
    labo.is_active = not labo.is_active
    db.commit()
    return {"message": f"Laboratoire {'activé' if labo.is_active else 'suspendu'}", "is_active": labo.is_active}

@router.delete("/labos/{labo_id}")
def supprimer_labo(labo_id: int, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    
    labo = db.query(models.LaboDB).filter(models.LaboDB.id == labo_id).first()
    if labo is not None and labo.id == current_user.labo_id:
        # Se suspendre ou se supprimer soi-meme = se verrouiller dehors, sans
        # aucun moyen de revenir en arriere depuis l'interface.
        raise HTTPException(
            status_code=400,
            detail="Impossible de modifier le laboratoire de votre propre compte administrateur",
        )
    if not labo:
        raise HTTPException(status_code=404, detail="Laboratoire non trouvé")
    
    db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == labo_id).delete()
    db.query(models.Patient).filter(models.Patient.labo_id == labo_id).delete()
    db.query(models.UserDB).filter(models.UserDB.labo_id == labo_id).delete()
    db.delete(labo)
    db.commit()
    return {"message": "Laboratoire et toutes ses données supprimés"}