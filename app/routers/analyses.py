from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/analyses", tags=["Analyses"])

@router.post("/create")
def create_analyse(
    patient_id: int = Form(...), 
    type_analyse: str = Form(...), 
    db: Session = Depends(get_db), 
    current_user: models.UserDB = Depends(get_current_user)
):
    # Vérifier que le patient existe et appartient bien à ce labo (sécurité multi-tenant)
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id, 
        models.Patient.labo_id == current_user.labo_id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé ou non autorisé")

    nouvelle_analyse = models.AnalyseDB(
        patient_id=patient.id,
        type_analyse=type_analyse,
        statut="En cours",
        labo_id=current_user.labo_id
    )
    
    db.add(nouvelle_analyse)
    db.commit()
    db.refresh(nouvelle_analyse)
    
    # Redirection vers l'accueil pour voir le résultat
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)