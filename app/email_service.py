import os
import httpx

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_URL = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "benta.fouzi@gmail.com")

async def envoyer_email_reinitialisation(email_destinataire: str, token: str):
    if not BREVO_API_KEY:
        print("⚠️ BREVO_API_KEY non configurée. Email non envoyé.")
        return False
    
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    lien = f"{base_url}/reset-password?token={token}"
    
    payload = {
        "sender": {"name": "MedicLab", "email": SENDER_EMAIL},
        "to": [{"email": email_destinataire}],
        "subject": "Réinitialisation de votre mot de passe",
        "htmlContent": f"""
            <h2>Réinitialisation de mot de passe</h2>
            <p>Vous avez demandé à réinitialiser votre mot de passe sur MedicLab.</p>
            <p>Cliquez sur le lien ci-dessous pour choisir un nouveau mot de passe :</p>
            <a href="{lien}" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Réinitialiser mon mot de passe</a>
            <p>Ce lien expirera dans 15 minutes.</p>
            <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
        """
    }
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(BREVO_URL, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            print(f"✅ Email envoyé à {email_destinataire}")
            return True
        else:
            print(f"❌ Erreur d'envoi : {response.status_code} - {response.text}")
            return False