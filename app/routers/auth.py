from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import secrets
from .. import models, schemas, auth
from ..database import get_db
from ..email_service import envoyer_email_reinitialisation

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentification"]
)

@router.post("/register")
def register_user(email: str, password: str, nom_labo: str, db: Session = Depends(get_db)):
    existing_user = db.query(models.UserDB).filter(models.UserDB.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    nouveau_labo = models.LaboDB(nom=nom_labo)
    db.add(nouveau_labo)
    db.commit()
    db.refresh(nouveau_labo)

    hashed_password = auth.get_password_hash(password)
    new_user = models.UserDB(email=email, hashed_password=hashed_password, labo_id=nouveau_labo.id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Utilisateur et labo créés avec succès", "email": new_user.email}

@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.UserDB).filter(models.UserDB.email == form_data.username).first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(models.UserDB).filter(models.UserDB.email == email).first()
    if not user:
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    reset_token = models.PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    envoyer_email_reinitialisation(email, token)
    return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}

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
    
    user.hashed_password = auth.get_password_hash(new_password)
    reset_entry.used = True
    db.commit()
    
    return {"message": "Mot de passe réinitialisé avec succès"}