from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
import os
import time

router = APIRouter(
    prefix="/api/analyses",
    tags=["Analyses"]
)

@router.post("/", response_model=schemas.AnalyseResponse)
def creer_analyse(demande: schemas.AnalyseRequest, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    existing = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.patient_id == demande.patient_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Analyse déjà existante pour ce patient dans votre labo")

    if os.getenv("TESTING") != "True":
        print(f"🏥 Démarrage de l'analyse pour le patient {demande.patient_id}...")
        time.sleep(1) 
    
    resultat = "Analyse terminée avec succès. Aucune anomalie détectée."
    
    nouvelle_analyse = models.AnalyseDB(
        patient_id=demande.patient_id,
        type_analyse=demande.type_analyse,
        statut="terminé",
        message=resultat,
        labo_id=current_user.labo_id
    )
    db.add(nouvelle_analyse)
    db.commit()
    db.refresh(nouvelle_analyse)
    
    return {"patient_id": nouvelle_analyse.patient_id, "resultat": nouvelle_analyse.message, "statut": nouvelle_analyse.statut}

@router.get("/toutes")
def lister_analyses(db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    analyses = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.labo_id == current_user.labo_id
    ).order_by(models.AnalyseDB.id.desc()).all()
    return analyses

@router.get("/{patient_id}")
def get_analyse(patient_id: str, db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.patient_id == patient_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()
    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {
        "patient_id": analyse.patient_id,
        "type": analyse.type_analyse,
        "statut": analyse.statut,
        "message": analyse.message
    }