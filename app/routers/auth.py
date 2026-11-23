from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import secrets
from urllib.parse import quote
from ..auth import (
    get_password_hash, verify_password, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, COOKIE_SECURE,
)
from .. import models
from ..database import get_db
from ..email_service import envoyer_email_reinitialisation

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


def _cible_apres_connexion(next_url: str) -> str:
    if not next_url:
        return "/"
    if not next_url.startswith("/") or next_url.startswith("//") or "\\" in next_url:
        return "/"
    return next_url

@router.post("/register")
def register_user(email: str, password: str, nom_labo: str, db: Session = Depends(get_db)):
    existing_user = db.query(models.UserDB).filter(models.UserDB.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    nouveau_labo = models.LaboDB(nom=nom_labo)
    db.add(nouveau_labo)
    db.commit()
    db.refresh(nouveau_labo)

    hashed_password = get_password_hash(password)
    new_user = models.UserDB(email=email, hashed_password=hashed_password, labo_id=nouveau_labo.id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Utilisateur et labo créés avec succès", "email": new_user.email}

@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    next_url: str = Form(""),
    db: Session = Depends(get_db),
):
    user = db.query(models.UserDB).filter(models.UserDB.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Un laboratoire suspendu ne doit plus pouvoir entrer. L'administrateur est
    # exempte : sinon une suspension de son propre labo le verrouillerait dehors.
    # is_active NULL (colonne ajoutee apres coup) est traite comme actif.
    if not user.is_admin:
        labo = db.query(models.LaboDB).filter(models.LaboDB.id == user.labo_id).first()
        if labo is not None and labo.is_active is False:
            message = "Ce laboratoire est suspendu. Contactez l'administrateur."
            return RedirectResponse(
                url=f"/login?error={quote(message)}&next={quote(_cible_apres_connexion(next_url))}",
                status_code=302,
            )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "is_admin": user.is_admin}, 
        expires_delta=access_token_expires
    )
    
    redirect_url = "/admin/dashboard" if user.is_admin else _cible_apres_connexion(next_url)
    
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return response

@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    print(f"🚨 [ROUTE] DÉBUT forgot_password pour : {email}")

    user = db.query(models.UserDB).filter(models.UserDB.email == email).first()
    
    if not user:
        print("⚠️ [ROUTE] Utilisateur non trouvé (Sécurité - Fake Success)")
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    try:
        reset_token = models.PasswordResetToken(token=token, user_id=user.id, expires_at=expires_at)
        db.add(reset_token)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ [ROUTE] Échec de l'enregistrement du jeton : {e}")
        raise HTTPException(status_code=500, detail="Impossible de créer le lien de réinitialisation.")
    
    print("🚀 [ROUTE] Appel de envoyer_email_reinitialisation MAINTENANT...")
    
    try:
        succes_envoi = envoyer_email_reinitialisation(email, token)
        print(f"🔍 [ROUTE] RÉSULTAT REÇU DE LA FONCTION : {succes_envoi} (Type: {type(succes_envoi)})")
        
        if not succes_envoi:
            print("❌ [ROUTE] ÉCHEC DÉTECTÉ -> Levée erreur 500")
            raise HTTPException(status_code=500, detail="Échec de l'envoi de l'email. Vérifiez les logs serveur (Brevo).")
            
        print("✅ [ROUTE] SUCCÈS CONFIRMÉ -> Retour 200 OK")
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}
        
    except Exception as e:
        print(f"💥 [ROUTE] EXCEPTION IMPRÉVUE : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne serveur : {str(e)}")

@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    reset_entry = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token,
        models.PasswordResetToken.used == False
    ).first()
    
    if not reset_entry or reset_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")
    
    user = db.query(models.UserDB).filter(models.UserDB.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user.hashed_password = get_password_hash(new_password)
    reset_entry.used = True
    db.commit()
    
    return {"message": "Mot de passe réinitialisé avec succès"}