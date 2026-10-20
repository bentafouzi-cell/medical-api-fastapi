import os
from fastapi.testclient import TestClient
from main import app, Base, engine

# Forcer l'application à utiliser la base de données de test
os.environ["TESTING"] = "True"

# Recréer les tables pour la base de test avant de lancer les tests
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_cycle_complet_analyse():
    # 1. Tester la création d'une analyse
    response_post = client.post("/api/analyses", json={
        "patient_id": "TEST-DB-001",
        "type_analyse": "sanguin"
    })
    assert response_post.status_code == 200
    data = response_post.json()
    assert data["patient_id"] == "TEST-DB-001"
    assert "Aucune anomalie détectée" in data["resultat"]
    
    # 2. Tester la lecture de cette analyse en base de données
    response_get = client.get("/api/analyses/TEST-DB-001")
    assert response_get.status_code == 200
    assert response_get.json()["statut"] == "terminé"
    
    # 3. Tester la gestion d'erreur (Patient introuvable)
    response_404 = client.get("/api/analyses/PATIENT-INCONNU")
    assert response_404.status_code == 404
    
    # 4. Tester la gestion d'erreur (Doublon)
    response_doublon = client.post("/api/analyses", json={
        "patient_id": "TEST-DB-001",
        "type_analyse": "urine"
    })
    assert response_doublon.status_code == 400
    
    print("🧪 Tous les tests base de données sont réussis !")
