from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/analyses", tags=["Analyses"])

@router.post("/create")
def create_analyse(
    request: Request,
    patient_id: str = Form(...), 
    type_analyse: str = Form(...),
    # Champs dynamiques pour les résultats (reçus comme listes depuis le form JS)
    result_names: Optional[str] = Form(None), # JSON string ou liste séparée par |
    result_values: Optional[str] = Form(None),
    result_units: Optional[str] = Form(None),
    result_mins: Optional[str] = Form(None),
    result_maxs: Optional[str] = Form(None),
    db: Session = Depends(get_db), 
    current_user: models.UserDB = Depends(get_current_user)
):
    try:
        p_id = int(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID Patient invalide")

    patient = db.query(models.Patient).filter(
        models.Patient.id == p_id, 
        models.Patient.labo_id == current_user.labo_id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    # Création de l'analyse
    nouvelle_analyse = models.AnalyseDB(
        patient_id=p_id,
        type_analyse=type_analyse,
        statut="En cours",
        labo_id=current_user.labo_id
    )
    db.add(nouvelle_analyse)
    db.commit()
    db.refresh(nouvelle_analyse)

    # Traitement des résultats si présents
    if result_names and result_values:
        names = result_names.split('||')
        values = result_values.split('||')
        units = result_units.split('||') if result_units else []
        mins = result_mins.split('||') if result_mins else []
        maxs = result_maxs.split('||') if result_maxs else []

        for i, name in enumerate(names):
            if name and values[i]:
                res = models.Resultat(
                    analyse_id=nouvelle_analyse.id,
                    nom_test=name.strip(),
                    valeur=values[i].strip(),
                    unite=units[i].strip() if i < len(units) else "",
                    norme_min=mins[i].strip() if i < len(mins) else "",
                    norme_max=maxs[i].strip() if i < len(maxs) else ""
                )
                db.add(res)
        
        db.commit()

    return RedirectResponse(url="/", status_code=303)