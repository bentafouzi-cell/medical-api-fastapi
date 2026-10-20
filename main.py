from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import time
import os

# 1. Configuration de la base de données SQLite
DATABASE_URL = "sqlite:///./medical.db"

# Astuce DevOps : Utiliser une base différente pour les tests automatisés
if os.getenv("TESTING") == "True":
    DATABASE_URL = "sqlite:///./test_medical.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modèle de la table en base de données
class AnalyseDB(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    type_analyse = Column(String)
    statut = Column(String, default="en_attente")
    message = Column(String, default="")

# Créer les tables au démarrage de l'application
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Analyse Médicale avec SQLite")

# 3. Dépendance pour obtenir une session DB propre à chaque requête
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modèles Pydantic pour la validation des requêtes
class AnalyseRequest(BaseModel):
    patient_id: str
    type_analyse: str

@app.post("/api/analyses")
def creer_analyse(demande: AnalyseRequest, db: Session = Depends(get_db)):
    # Vérifier si le patient existe déjà (Règle métier)
    existing = db.query(AnalyseDB).filter(AnalyseDB.patient_id == demande.patient_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Analyse déjà existante pour ce patient")

    print(f"🏥 Démarrage de l'analyse pour le patient {demande.patient_id}...")
    time.sleep(1) # Simulation du traitement
    resultat = "Analyse terminée avec succès. Aucune anomalie détectée."
    print(f"✅ {resultat}")
    
    # Sauvegarde en base de données
    nouvelle_analyse = AnalyseDB(
        patient_id=demande.patient_id,
        type_analyse=demande.type_analyse,
        statut="terminé",
        message=resultat
    )
    db.add(nouvelle_analyse)
    db.commit()
    db.refresh(nouvelle_analyse)
    
    return {"patient_id": nouvelle_analyse.patient_id, "resultat": nouvelle_analyse.message}

@app.get("/api/analyses/{patient_id}")
def get_analyse(patient_id: str, db: Session = Depends(get_db)):
    analyse = db.query(AnalyseDB).filter(AnalyseDB.patient_id == patient_id).first()
    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {
        "patient_id": analyse.patient_id,
        "type": analyse.type_analyse,
        "statut": analyse.statut,
        "message": analyse.message
    }
