from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_creer_analyse():
    response = client.post("/api/analyses", json={
        "patient_id": "TEST-001",
        "type_analyse": "sanguin"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "TEST-001"
    assert "Aucune anomalie détectée" in data["resultat"]
    print("🧪 Test automatisé réussi !")
