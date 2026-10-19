from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI(title="API Analyse Médicale")

class AnalyseRequest(BaseModel):
    patient_id: str
    type_analyse: str

# Base de données simulée en mémoire pour ce TP
db_analyses = {}

@app.post("/api/analyses")
def creer_analyse(demande: AnalyseRequest):
    print(f"🏥 Démarrage de l'analyse pour le patient {demande.patient_id}...")
    time.sleep(2) # Simulation du traitement
    resultat = "Analyse terminée avec succès. Aucune anomalie détectée."
    print(f"✅ {resultat}")
    
    db_analyses[demande.patient_id] = {
        "type": demande.type_analyse,
        "statut": "terminé",
        "message": resultat
    }
    return {"patient_id": demande.patient_id, "resultat": resultat}

@app.get("/api/analyses/{patient_id}")
def get_analyse(patient_id: str):
    if patient_id in db_analyses:
        return db_analyses[patient_id]
    return {"error": "Analyse non trouvée"}
