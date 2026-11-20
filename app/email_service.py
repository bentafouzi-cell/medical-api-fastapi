import os
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "benta.fouzi@gmail.com")
BASE_URL = os.getenv("BASE_URL", "https://medical-api-fastapi.onrender.com")

def envoyer_email_reinitialisation(email_destinataire: str, token: str) -> bool:
    if not BREVO_API_KEY:
        print("⚠️ BREVO_API_KEY non configurée. Email non envoyé.")
        return False

    lien = f"{BASE_URL}/reset-password?token={token}"

    html_content = f"""
    <h2>Réinitialisation de mot de passe</h2>
    <p>Vous avez demandé à réinitialiser votre mot de passe sur MedicLab.</p>
    <p>Cliquez sur le lien ci-dessous :</p>
    <a href="{lien}" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Réinitialiser mon mot de passe</a>
    <p>Ce lien expirera dans 15 minutes.</p>
    <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
    """

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "sender": {"name": "MedicLab", "email": SENDER_EMAIL},
                "to": [{"email": email_destinataire}],
                "subject": "Réinitialisation de votre mot de passe — MedicLab",
                "htmlContent": html_content
            },
            timeout=15
        )
        print(f"🔍 STATUT BREVO : {response.status_code}")
        print(f"🔍 RÉPONSE BREVO : {response.text}")
        if response.status_code in [200, 201]:
            print(f"✅ Email envoyé à {email_destinataire}")
            return True
        else:
            print(f"❌ Erreur d'envoi : {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")
        return False