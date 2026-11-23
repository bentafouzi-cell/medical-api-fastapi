from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/analyses", tags=["Analyses"])


@router.post("/create")
def create_analyse(
    request: Request,
    patient_id: str = Form(...),
    type_analyse: str = Form(...),
    result_names: Optional[str] = Form(None),
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
        raise HTTPException(status_code=404, detail="Patient non trouvé ou non autorisé")

    nouvelle_analyse = models.AnalyseDB(
        patient_id=p_id,
        type_analyse=type_analyse,
        statut="En cours",
        labo_id=current_user.labo_id
    )

    db.add(nouvelle_analyse)
    db.commit()
    db.refresh(nouvelle_analyse)

    if result_names and result_values:
        names = result_names.split('||')
        values = result_values.split('||')
        units = result_units.split('||') if result_units else []
        mins = result_mins.split('||') if result_mins else []
        maxs = result_maxs.split('||') if result_maxs else []

        for i, name in enumerate(names):
            if name and i < len(values) and values[i]:
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


@router.get("/detail/{analyse_id}")
def get_analyse_detail(
    analyse_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()

    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")

    resultats = db.query(models.Resultat).filter(
        models.Resultat.analyse_id == analyse_id
    ).all()

    return {
        "analyse_id": analyse.id,
        "patient": f"{analyse.patient.nom} {analyse.patient.prenom}",
        "type_analyse": analyse.type_analyse,
        "statut": analyse.statut,
        "date": analyse.created_at.strftime("%d/%m/%Y %H:%M"),
        "resultats": [
            {
                "nom_test": r.nom_test,
                "valeur": r.valeur,
                "unite": r.unite,
                "norme_min": r.norme_min,
                "norme_max": r.norme_max
            } for r in resultats
        ]
    }


@router.post("/valider/{analyse_id}")
def valider_analyse(
    analyse_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()

    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")

    analyse.statut = "Terminé"
    db.commit()

    return RedirectResponse(url=f"/analyse/{analyse_id}", status_code=303)


@router.post("/resultats/{resultat_id}/update")
def update_resultat(
    resultat_id: int,
    nom_test: str = Form(...),
    valeur: str = Form(...),
    unite: Optional[str] = Form(None),
    norme_min: Optional[str] = Form(None),
    norme_max: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    resultat = db.query(models.Resultat).filter(models.Resultat.id == resultat_id).first()
    if not resultat:
        raise HTTPException(status_code=404, detail="Résultat non trouvé")

    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == resultat.analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()

    if not analyse:
        raise HTTPException(status_code=403, detail="Accès refusé")

    resultat.nom_test = nom_test.strip()
    resultat.valeur = valeur.strip()
    resultat.unite = (unite or "").strip()
    resultat.norme_min = (norme_min or "").strip()
    resultat.norme_max = (norme_max or "").strip()

    db.add(resultat)
    db.commit()

    return {"message": "Résultat mis à jour", "id": resultat.id, "new_value": resultat.valeur}


@router.post("/resultats/{resultat_id}/delete")
def delete_resultat(
    resultat_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    resultat = db.query(models.Resultat).filter(models.Resultat.id == resultat_id).first()
    if not resultat:
        raise HTTPException(status_code=404, detail="Résultat non trouvé")

    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == resultat.analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()

    if not analyse:
        raise HTTPException(status_code=403, detail="Accès refusé")

    db.delete(resultat)
    db.commit()

    return {"message": "Résultat supprimé"}


@router.post("/{analyse_id}/delete")
def delete_analyse(
    analyse_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()

    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")

    db.query(models.Resultat).filter(models.Resultat.analyse_id == analyse_id).delete()
    db.delete(analyse)
    db.commit()

    return RedirectResponse(url="/", status_code=303)

@router.post("/analyse/{analyse_id}/add-result")
def add_result_to_analyse(
    analyse_id: int,
    nom_test: str = Form(...),
    valeur: str = Form(...),
    unite: Optional[str] = Form(None),
    norme_min: Optional[str] = Form(None),
    norme_max: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(get_current_user)
):
    # Vérifier que l'analyse existe et appartient au labo
    analyse = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.id == analyse_id,
        models.AnalyseDB.labo_id == current_user.labo_id
    ).first()

    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")

    # Créer le nouveau résultat
    nouveau_resultat = models.Resultat(
        analyse_id=analyse_id,
        nom_test=nom_test.strip(),
        valeur=valeur.strip(),
        unite=(unite or "").strip(),
        norme_min=(norme_min or "").strip(),
        norme_max=(norme_max or "").strip()
    )

    db.add(nouveau_resultat)
    db.commit()

    # Redirection vers la page de détail pour voir le résultat ajouté
    return RedirectResponse(url=f"/analyse/{analyse_id}", status_code=303)

@router.get("/toutes")
def lister_analyses(db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    analyses = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.labo_id == current_user.labo_id
    ).order_by(models.AnalyseDB.created_at.desc()).all()
    
    result = []
    for a in analyses:
        result.append({
            "id": a.id,
            "patient_nom": f"{a.patient.nom} {a.patient.prenom}",
            "type_analyse": a.type_analyse,
            "statut": a.statut,
            "date": a.created_at.strftime("%d/%m/%Y %H:%M")
        })
    return result

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: models.UserDB = Depends(get_current_user)):
    total_patients = db.query(models.Patient).filter(models.Patient.labo_id == current_user.labo_id).count()
    total_analyses = db.query(models.AnalyseDB).filter(models.AnalyseDB.labo_id == current_user.labo_id).count()
    en_cours = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.labo_id == current_user.labo_id,
        models.AnalyseDB.statut == "En cours"
    ).count()
    terminees = db.query(models.AnalyseDB).filter(
        models.AnalyseDB.labo_id == current_user.labo_id,
        models.AnalyseDB.statut == "Terminé"
    ).count()
    
    return {
        "total_patients": total_patients,
        "total_analyses": total_analyses,
        "en_cours": en_cours,
        "terminees": terminees
    }