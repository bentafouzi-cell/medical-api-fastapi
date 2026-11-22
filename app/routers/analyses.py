from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/analyses", tags=["Analyses"])

@router.post("/create")
def create_analyse(
    request: Request,
    patient_id: str = Form(...), 
    type_analyse: str = Form(...), 
    db: Session = Depends(get_db), 
    current_user: models.UserDB = Depends(get_current_user)
):
    # 1. Conversion explicite de l'ID (parfois le formulaire envoie une chaîne)
    try:
        p_id = int(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID Patient invalide")

    print(f" Tentative de création : Patient ID={p_id}, Type={type_analyse}, Labo ID={current_user.labo_id}")

    # 2. Vérification du patient
    patient = db.query(models.Patient).filter(
        models.Patient.id == p_id, 
        models.Patient.labo_id == current_user.labo_id
    ).first()
    
    if not patient:
        print(f"❌ Échec : Patient {p_id} non trouvé pour le labo {current_user.labo_id}")
        raise HTTPException(status_code=404, detail="Patient non trouvé ou non autorisé")

    try:
        # 3. Création
        nouvelle_analyse = models.AnalyseDB(
            patient_id=p_id,
            type_analyse=type_analyse,
            statut="En cours",
            labo_id=current_user.labo_id
        )
        
        db.add(nouvelle_analyse)
        db.commit()
        db.refresh(nouvelle_analyse)
        
        print(f"✅ Succès : Analyse créée ID={nouvelle_analyse.id}")
        
        # 4. Redirection
        return RedirectResponse(url="/", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"💥 Erreur Base de Données : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")